import os
"""
Generation API Endpoints
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.project_character import ProjectCharacter
from app.models.episode import Episode, EpisodeStatus
from app.schemas.generation import (
    GenerateScriptRequest, GenerateScriptResponse,
    GenerateVoiceoverRequest, GenerateVoiceoverResponse,
    GenerateSoundsRequest, GenerateSoundsResponse,
    GenerateMusicRequest, GenerateMusicResponse,
    MergeAudioRequest, MergeAudioResponse,
    GenerateCoverRequest, GenerateCoverResponse,
    SelectCoverRequest,
    GenerateFullRequest, GenerateFullResponse,
    GenerationStatusResponse
)
from app.core.dependencies import get_current_user, verify_episode_ownership
from app.core.exceptions import BusinessLogicError, InvalidStatusTransitionError
from app.services.llm_service import LLMService
from app.services.elevenlabs_service import ElevenLabsService
from app.services.cover_service import CoverService
from app.services.audio_service import AudioService
from app.services.storage_service import StorageService
from app.services.summary_service import SummaryService

router = APIRouter()


@router.post("/script/{episode_id}", response_model=GenerateScriptResponse)
async def generate_script(
    request: GenerateScriptRequest,
    episode: Episode = Depends(verify_episode_ownership),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate script for an episode"""
    # Get project and characters
    project_result = await db.execute(
        select(Project).where(Project.id == episode.project_id)
    )
    project = project_result.scalar_one()
    
    char_result = await db.execute(
        select(ProjectCharacter)
        .options(selectinload(ProjectCharacter.voice))
        .where(ProjectCharacter.project_id == project.id)
        .order_by(ProjectCharacter.sort_order)
    )
    characters = list(char_result.scalars().all())
    
    # Get previous episodes for context if this is a continuation
    previous_episodes = None
    if episode.episode_number > 1:
        prev_result = await db.execute(
            select(Episode)
            .where(
                Episode.project_id == project.id,
                Episode.episode_number < episode.episode_number
            )
            .order_by(Episode.episode_number)
        )
        previous_episodes = list(prev_result.scalars().all())
    
    # Update status
    episode.status = EpisodeStatus.SCRIPT_GENERATING.value
    episode.error_message = None
    await db.commit()
    
    try:
        # Generate script
        llm_service = LLMService(current_user)
        script = await llm_service.generate_script(
            project=project,
            episode=episode,
            characters=characters,
            previous_episodes=previous_episodes,
            custom_prompt=request.custom_prompt,
            temperature=request.temperature
        )
        
        # Save script
        episode.script_json = script
        
        # Build text version
        summary_service = SummaryService(current_user)
        episode.script_text = summary_service.build_script_text_from_json(script)
        
        # Update title if auto-generated
        if episode.title_auto_generated and script.get("story_title"):
            episode.title = script["story_title"]
        
        episode.status = EpisodeStatus.SCRIPT_DONE.value
        episode.updated_at = datetime.utcnow()
        
        return GenerateScriptResponse(
            episode_id=episode.id,
            status=episode.status,
            story_title=script.get("story_title"),
            lines_count=len(script.get("lines", [])),
            estimated_duration_minutes=script.get("approx_duration_minutes", 0)
        )
        
    except Exception as e:
        episode.status = EpisodeStatus.ERROR.value
        episode.error_message = str(e)
        raise


@router.post("/voiceover/{episode_id}", response_model=GenerateVoiceoverResponse)
async def generate_voiceover(
    request: GenerateVoiceoverRequest,
    episode: Episode = Depends(verify_episode_ownership),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate voiceover for an episode"""
    if not episode.script_json:
        raise BusinessLogicError("Episode must have a script before generating voiceover")
    
    # Delete old audio file before regeneration
    if episode.voice_audio_url:
        old_path = f"/var/www/heinercast/storage{episode.voice_audio_url.replace('/storage', '')}"
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except: pass

    # Update status
    episode.status = EpisodeStatus.VOICEOVER_GENERATING.value
    episode.error_message = None
    await db.commit()
    
    try:
        # Get script lines
        lines = episode.script_json.get("lines", [])
        if not lines:
            raise BusinessLogicError("Script has no lines")
        
        
        # Convert local voice_id to ElevenLabs voice_id
        from app.models import Voice
        voice_cache = {}
        for line in lines:
            local_voice_id = line.get("voice_id")
            if local_voice_id and local_voice_id not in voice_cache:
                voice = await db.execute(
                    select(Voice).where(Voice.id == local_voice_id)
                )
                voice_obj = voice.scalar_one_or_none()
                if voice_obj and voice_obj.elevenlabs_voice_id:
                    voice_cache[local_voice_id] = voice_obj.elevenlabs_voice_id
            if local_voice_id in voice_cache:
                line["voice_id"] = voice_cache[local_voice_id]
        # Initialize services
        elevenlabs_service = ElevenLabsService(current_user)
        audio_service = AudioService()
        storage_service = StorageService(
            current_user.storage_type,
            current_user.google_drive_credentials
        )
        
        # Generate voiceover (may be in parts)
        audio_parts, timestamps_parts = await elevenlabs_service.generate_dialogue_in_parts(lines)
        
        # Merge parts if needed
        if len(audio_parts) > 1:
            audio_url = await audio_service.merge_audio_parts(audio_parts)
        else:
            audio_url = await storage_service.save_file(
                audio_parts[0],
                subfolder="audio",
                extension="mp3"
            )
        
        # Get duration
        duration = await audio_service.get_audio_duration(audio_url)
        
        # Combine timestamps
        combined_timestamps = {
            "parts": timestamps_parts,
            "total_parts": len(timestamps_parts)
        }
        
        # Save results
        episode.voice_audio_url = audio_url
        episode.voice_audio_duration_seconds = duration
        episode.voice_timestamps_json = combined_timestamps
        episode.status = EpisodeStatus.VOICEOVER_DONE.value
        episode.updated_at = datetime.utcnow()
        
        await db.commit()
        return GenerateVoiceoverResponse(
            episode_id=episode.id,
            status=episode.status,
            audio_url=audio_url,
            duration_seconds=duration,
            parts_count=len(audio_parts)
        )
        
    except Exception as e:
        episode.status = EpisodeStatus.ERROR.value
        episode.error_message = str(e)
        raise


@router.post("/sounds/{episode_id}", response_model=GenerateSoundsResponse)
async def generate_sounds(
    request: GenerateSoundsRequest,
    episode: Episode = Depends(verify_episode_ownership),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate sound effects for an episode"""
    if not episode.voice_audio_url:
        raise BusinessLogicError("Episode must have voiceover before generating sounds")
    
    if not episode.include_sound_effects:
        raise BusinessLogicError("Sound effects are disabled for this episode")
    
    # Update status
    episode.status = EpisodeStatus.SOUNDS_GENERATING.value
    episode.error_message = None
    await db.commit()
    
    try:
        # Extract sound effects from script
        lines = episode.script_json.get("lines", [])
        sound_effects = []
        
        # Calculate approximate timing based on voice timestamps
        timestamps = episode.voice_timestamps_json or {}
        parts = timestamps.get("parts", [{}])
        
        current_time = 0.0
        for i, line in enumerate(lines):
            sound_prompt = line.get("sound_effect")
            
            # Estimate line duration (rough approximation)
            line_chars = len(line.get("text", ""))
            line_duration = line_chars / 14.0  # ~14 chars per second
            
            if sound_prompt:
                sound_effects.append({
                    "prompt": sound_prompt,
                    "start_time": current_time + line_duration,  # Sound at end of line
                    "line_index": i
                })
            
            current_time += line_duration
        
        if not sound_effects:
            episode.sounds_json = []
            episode.status = EpisodeStatus.SOUNDS_DONE.value
            return GenerateSoundsResponse(
                episode_id=episode.id,
                status=episode.status,
                sounds_count=0,
                sounds=[]
            )
        
        # Generate each sound effect
        elevenlabs_service = ElevenLabsService(current_user)
        storage_service = StorageService(
            current_user.storage_type,
            current_user.google_drive_credentials
        )
        
        generated_sounds = []
        for sound in sound_effects:
            audio_bytes = await elevenlabs_service.generate_sound_effect(
                prompt=sound["prompt"],
                duration_seconds=request.default_duration_seconds,
                prompt_influence=request.prompt_influence
            )
            
            sound_url = await storage_service.save_file(
                audio_bytes,
                subfolder="audio",
                extension="mp3"
            )
            
            generated_sounds.append({
                "prompt": sound["prompt"],
                "url": sound_url,
                "local_path": sound_url,
                "start_time": sound["start_time"],
                "duration": request.default_duration_seconds
            })
        
        episode.sounds_json = generated_sounds
        episode.status = EpisodeStatus.SOUNDS_DONE.value
        episode.updated_at = datetime.utcnow()
        
        return GenerateSoundsResponse(
            episode_id=episode.id,
            status=episode.status,
            sounds_count=len(generated_sounds),
            sounds=generated_sounds
        )
        
    except Exception as e:
        episode.status = EpisodeStatus.ERROR.value
        episode.error_message = str(e)
        raise


@router.post("/music/{episode_id}", response_model=GenerateMusicResponse)
async def generate_music(
    request: GenerateMusicRequest,
    episode: Episode = Depends(verify_episode_ownership),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate background music for an episode"""
    if not episode.voice_audio_url:
        raise BusinessLogicError("Episode must have voiceover before generating music")
    
    if not episode.include_background_music:
        raise BusinessLogicError("Background music is disabled for this episode")
    
    # Update status
    episode.status = EpisodeStatus.MUSIC_GENERATING.value
    episode.error_message = None
    await db.commit()
    
    try:
        # Get project for musical atmosphere
        project_result = await db.execute(
            select(Project).where(Project.id == episode.project_id)
        )
        project = project_result.scalar_one()
        
        # Build music prompt
        duration_ms = int((episode.voice_audio_duration_seconds or 300) * 1000)
        
        atmosphere = project.musical_atmosphere or project.genre_tone
        music_prompt = f"{atmosphere}, instrumental background music for audiobook, ambient, atmospheric"
        
        # Generate music
        elevenlabs_service = ElevenLabsService(current_user)
        storage_service = StorageService(
            current_user.storage_type,
            current_user.google_drive_credentials
        )
        
        # Create plan
        composition_plan = await elevenlabs_service.create_music_plan(
            prompt=music_prompt,
            duration_ms=duration_ms
        )
        
        # Generate music
        music_bytes = await elevenlabs_service.generate_music(
            composition_plan=composition_plan,
            force_instrumental=request.force_instrumental
        )
        
        music_url = await storage_service.save_file(
            music_bytes,
            subfolder="audio",
            extension="mp3"
        )
        
        episode.music_url = music_url
        episode.music_composition_plan = composition_plan
        episode.status = EpisodeStatus.MUSIC_DONE.value
        episode.updated_at = datetime.utcnow()
        
        return GenerateMusicResponse(
            episode_id=episode.id,
            status=episode.status,
            music_url=music_url,
            duration_seconds=duration_ms / 1000
        )
        
    except Exception as e:
        episode.status = EpisodeStatus.ERROR.value
        episode.error_message = str(e)
        raise


@router.post("/merge/{episode_id}", response_model=MergeAudioResponse)
async def merge_audio(
    request: MergeAudioRequest,
    episode: Episode = Depends(verify_episode_ownership),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Merge voice, sounds, and music into final audio"""
    if not episode.voice_audio_url:
        raise BusinessLogicError("Episode must have voiceover before merging")
    
    # Update status
    episode.status = EpisodeStatus.MERGING.value
    episode.error_message = None
    await db.commit()
    
    try:
        audio_service = AudioService()
        
        # Determine what to merge
        sounds = episode.sounds_json if episode.include_sound_effects else None
        music_path = episode.music_url if episode.include_background_music else None
        
        # Full merge
        final_url = await audio_service.full_merge(
            voice_audio_path=episode.voice_audio_url,
            sounds=sounds,
            music_path=music_path,
            voice_volume=request.voice_volume,
            sounds_volume=request.sounds_volume,
            music_volume=request.music_volume_db
        )
        
        # Get duration
        duration = await audio_service.get_audio_duration(final_url)
        
        episode.final_audio_url = final_url
        episode.final_audio_duration_seconds = duration
        episode.status = EpisodeStatus.AUDIO_DONE.value
        episode.updated_at = datetime.utcnow()
        
        return MergeAudioResponse(
            episode_id=episode.id,
            status=episode.status,
            final_audio_url=final_url,
            duration_seconds=duration
        )
        
    except Exception as e:
        episode.status = EpisodeStatus.ERROR.value
        episode.error_message = str(e)
        raise


@router.post("/cover/{episode_id}", response_model=GenerateCoverResponse)
async def generate_cover(
    request: GenerateCoverRequest,
    episode: Episode = Depends(verify_episode_ownership),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate cover image for an episode"""
    # Delete old cover files before regeneration
    if episode.cover_url:
        old_path = f"/var/www/heinercast/storage{episode.cover_url.replace('/storage', '')}"
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except: pass
    
    if episode.cover_variants_json:
        for variant in episode.cover_variants_json:
            url = variant.get('url', '')
            if url:
                old_path = f"/var/www/heinercast/storage{url.replace('/storage', '')}"
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except: pass
        episode.cover_variants_json = None
        episode.cover_url = None

    # Update status
    episode.status = EpisodeStatus.COVER_GENERATING.value
    episode.error_message = None
    await db.commit()
    
    try:
        # Get project
        project_result = await db.execute(
            select(Project).where(Project.id == episode.project_id)
        )
        project = project_result.scalar_one()
        
        # Build prompt
        cover_service = CoverService(current_user)
        storage_service = StorageService(
            current_user.storage_type,
            current_user.google_drive_credentials
        )
        
        base_prompt = cover_service.build_cover_prompt(
            title=episode.title or project.title,
            genre_tone=project.genre_tone,
            description=episode.description,
            template=current_user.cover_prompt_template
        )
        # Add custom instructions if provided
        prompt = base_prompt
        if request.custom_prompt:
            prompt = f"{base_prompt}\n\nAdditional instructions: {request.custom_prompt}"
        
        # Store reference image if provided
        reference_url = request.reference_images[0] if request.reference_images else None
        if reference_url:
            episode.cover_reference_image_url = reference_url
        
        # Generate covers
        reference_urls = request.reference_images or ([reference_url] if reference_url else None)
        cover_urls = await cover_service.generate_multiple_covers(
            prompt=prompt,
            count=request.variants_count,
            reference_image_urls=request.reference_images,
            aspect_ratio=request.aspect_ratio
        )
        
        # Save cover URLs locally
        saved_urls = []
        for url in cover_urls:
            local_url = await storage_service.save_from_url(
                url,
                subfolder="covers"
            )
            saved_urls.append(local_url)
        
        # Build variants JSON
        variants = [
            {"url": url, "selected": i == 0}
            for i, url in enumerate(saved_urls)
        ]
        
        episode.cover_url = saved_urls[0] if saved_urls else None
        episode.cover_variants_json = variants
        episode.status = EpisodeStatus.DONE.value
        episode.updated_at = datetime.utcnow()
        
        return GenerateCoverResponse(
            episode_id=episode.id,
            status=episode.status,
            cover_url=episode.cover_url,
            variants=variants
        )
        
    except Exception as e:
        episode.status = EpisodeStatus.ERROR.value
        episode.error_message = str(e)
        raise


@router.post("/cover/{episode_id}/select")
async def select_cover(
    request: SelectCoverRequest,
    episode: Episode = Depends(verify_episode_ownership),
    db: AsyncSession = Depends(get_db)
):
    """Select a cover variant as the main cover"""
    if not episode.cover_variants_json:
        raise BusinessLogicError("No cover variants available")
    
    variants = episode.cover_variants_json
    if request.variant_index >= len(variants):
        raise BusinessLogicError(f"Invalid variant index: {request.variant_index}")
    
    # Update selection
    for i, variant in enumerate(variants):
        variant["selected"] = (i == request.variant_index)
    
    episode.cover_url = variants[request.variant_index]["url"]
    episode.cover_variants_json = variants.copy()  # Force SQLAlchemy to detect change
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(episode, "cover_variants_json")
    episode.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Cover selected", "cover_url": episode.cover_url}


@router.post("/full/{episode_id}", response_model=GenerateFullResponse)
async def generate_full(
    request: GenerateFullRequest,
    episode: Episode = Depends(verify_episode_ownership),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Run full generation pipeline"""
    # Get project and characters
    project_result = await db.execute(
        select(Project).where(Project.id == episode.project_id)
    )
    project = project_result.scalar_one()
    
    char_result = await db.execute(
        select(ProjectCharacter)
        .options(selectinload(ProjectCharacter.voice))
        .where(ProjectCharacter.project_id == project.id)
    )
    characters = list(char_result.scalars().all())
    
    response = GenerateFullResponse(
        episode_id=episode.id,
        status="processing",
        script_status="pending",
        voiceover_status="pending",
        sounds_status="pending" if episode.include_sound_effects else "skipped",
        music_status="pending" if episode.include_background_music else "skipped",
        merge_status="pending",
        cover_status="pending" if request.generate_cover else "skipped"
    )
    
    try:
        # 1. Generate script
        response.script_status = "in_progress"
        episode.status = EpisodeStatus.SCRIPT_GENERATING.value
        await db.commit()
        
        # Get previous episodes for context
        previous_episodes = None
        if episode.episode_number > 1:
            prev_result = await db.execute(
                select(Episode)
                .where(
                    Episode.project_id == project.id,
                    Episode.episode_number < episode.episode_number
                )
                .order_by(Episode.episode_number)
            )
            previous_episodes = list(prev_result.scalars().all())
        
        llm_service = LLMService(current_user)
        script = await llm_service.generate_script(
            project=project,
            episode=episode,
            characters=characters,
            previous_episodes=previous_episodes
        )
        
        episode.script_json = script
        summary_service = SummaryService(current_user)
        episode.script_text = summary_service.build_script_text_from_json(script)
        if episode.title_auto_generated and script.get("story_title"):
            episode.title = script["story_title"]
        
        response.script_status = "done"
        episode.status = EpisodeStatus.SCRIPT_DONE.value
        
        # 2. Generate voiceover
        response.voiceover_status = "in_progress"
        episode.status = EpisodeStatus.VOICEOVER_GENERATING.value
        await db.commit()
        
        elevenlabs_service = ElevenLabsService(current_user)
        audio_service = AudioService()
        storage_service = StorageService(
            current_user.storage_type,
            current_user.google_drive_credentials
        )
        
        lines = script.get("lines", [])
        audio_parts, timestamps_parts = await elevenlabs_service.generate_dialogue_in_parts(lines)
        
        if len(audio_parts) > 1:
            audio_url = await audio_service.merge_audio_parts(audio_parts)
        else:
            audio_url = await storage_service.save_file(audio_parts[0], subfolder="audio", extension="mp3")
        
        duration = await audio_service.get_audio_duration(audio_url)
        episode.voice_audio_url = audio_url
        episode.voice_audio_duration_seconds = duration
        episode.voice_timestamps_json = {"parts": timestamps_parts}
        
        response.voiceover_status = "done"
        episode.status = EpisodeStatus.VOICEOVER_DONE.value
        
        # 3. Generate sounds (if enabled)
        if episode.include_sound_effects:
            response.sounds_status = "in_progress"
            episode.status = EpisodeStatus.SOUNDS_GENERATING.value
            await db.commit()
            
            # Extract and generate sounds (simplified)
            sound_effects = []
            current_time = 0.0
            for line in lines:
                line_chars = len(line.get("text", ""))
                line_duration = line_chars / 14.0
                if line.get("sound_effect"):
                    sound_effects.append({
                        "prompt": line["sound_effect"],
                        "start_time": current_time + line_duration
                    })
                current_time += line_duration
            
            generated_sounds = []
            for sound in sound_effects:
                audio_bytes = await elevenlabs_service.generate_sound_effect(sound["prompt"])
                sound_url = await storage_service.save_file(audio_bytes, subfolder="audio", extension="mp3")
                generated_sounds.append({
                    "prompt": sound["prompt"],
                    "url": sound_url,
                    "local_path": sound_url,
                    "start_time": sound["start_time"],
                    "duration": 3.0
                })
            
            episode.sounds_json = generated_sounds
            response.sounds_status = "done"
            episode.status = EpisodeStatus.SOUNDS_DONE.value
        
        # 4. Generate music (if enabled)
        if episode.include_background_music:
            response.music_status = "in_progress"
            episode.status = EpisodeStatus.MUSIC_GENERATING.value
            await db.commit()
            
            duration_ms = int(episode.voice_audio_duration_seconds * 1000)
            atmosphere = project.musical_atmosphere or project.genre_tone
            music_prompt = f"{atmosphere}, instrumental background music"
            
            composition_plan = await elevenlabs_service.create_music_plan(music_prompt, duration_ms)
            music_bytes = await elevenlabs_service.generate_music(composition_plan)
            music_url = await storage_service.save_file(music_bytes, subfolder="audio", extension="mp3")
            
            episode.music_url = music_url
            episode.music_composition_plan = composition_plan
            response.music_status = "done"
            episode.status = EpisodeStatus.MUSIC_DONE.value
        
        # 5. Merge audio
        response.merge_status = "in_progress"
        episode.status = EpisodeStatus.MERGING.value
        await db.commit()
        
        final_url = await audio_service.full_merge(
            voice_audio_path=episode.voice_audio_url,
            sounds=episode.sounds_json if episode.include_sound_effects else None,
            music_path=episode.music_url if episode.include_background_music else None,
            voice_volume=request.voice_volume,
            sounds_volume=request.sounds_volume,
            music_volume=request.music_volume_db
        )
        
        final_duration = await audio_service.get_audio_duration(final_url)
        episode.final_audio_url = final_url
        episode.final_audio_duration_seconds = final_duration
        response.merge_status = "done"
        response.final_audio_url = final_url
        response.final_audio_duration_seconds = final_duration
        episode.status = EpisodeStatus.AUDIO_DONE.value
        
        # 6. Generate cover (if enabled)
        if request.generate_cover:
            response.cover_status = "in_progress"
            episode.status = EpisodeStatus.COVER_GENERATING.value
            await db.commit()
            
            cover_service = CoverService(current_user)
            prompt = cover_service.build_cover_prompt(
                title=episode.title or project.title,
                genre_tone=project.genre_tone,
                description=episode.description,
                template=current_user.cover_prompt_template
            )
            
            cover_urls = await cover_service.generate_multiple_covers(
                prompt=prompt,
                count=request.cover_variants_count,
                reference_image_url=request.cover_reference_image_url
            )
            
            saved_urls = []
            for url in cover_urls:
                local_url = await storage_service.save_from_url(url, subfolder="covers")
                saved_urls.append(local_url)
            
            variants = [{"url": url, "selected": i == 0} for i, url in enumerate(saved_urls)]
            episode.cover_url = saved_urls[0] if saved_urls else None
            episode.cover_variants_json = variants
            response.cover_status = "done"
            response.cover_url = episode.cover_url
        
        # 7. Generate summary for future continuations
        summary = await summary_service.generate_summary(episode)
        episode.summary = summary
        
        # Done!
        episode.status = EpisodeStatus.DONE.value
        episode.updated_at = datetime.utcnow()
        response.status = "done"
        
        return response
        
    except Exception as e:
        episode.status = EpisodeStatus.ERROR.value
        episode.error_message = str(e)
        response.status = "error"
        raise


@router.get("/status/{episode_id}", response_model=GenerationStatusResponse)
async def get_generation_status(
    episode: Episode = Depends(verify_episode_ownership)
):
    """Get current generation status"""
    status = episode.status
    
    # Determine steps
    all_steps = ["script", "voiceover"]
    if episode.include_sound_effects:
        all_steps.append("sounds")
    if episode.include_background_music:
        all_steps.append("music")
    all_steps.extend(["merge", "cover"])
    
    # Determine completed and remaining
    status_to_step = {
        EpisodeStatus.DRAFT.value: 0,
        EpisodeStatus.SCRIPT_GENERATING.value: 0,
        EpisodeStatus.SCRIPT_DONE.value: 1,
        EpisodeStatus.VOICEOVER_GENERATING.value: 1,
        EpisodeStatus.VOICEOVER_DONE.value: 2,
        EpisodeStatus.SOUNDS_GENERATING.value: 2,
        EpisodeStatus.SOUNDS_DONE.value: 3,
        EpisodeStatus.MUSIC_GENERATING.value: 3,
        EpisodeStatus.MUSIC_DONE.value: 4,
        EpisodeStatus.MERGING.value: 4,
        EpisodeStatus.AUDIO_DONE.value: 5,
        EpisodeStatus.COVER_GENERATING.value: 5,
        EpisodeStatus.DONE.value: 6,
        EpisodeStatus.ERROR.value: -1
    }
    
    current_step_idx = status_to_step.get(status, 0)
    
    if current_step_idx < 0:
        current_step = "error"
        completed = all_steps[:0]
        remaining = all_steps
    elif current_step_idx >= len(all_steps):
        current_step = "done"
        completed = all_steps
        remaining = []
    else:
        current_step = all_steps[current_step_idx] if current_step_idx < len(all_steps) else "done"
        completed = all_steps[:current_step_idx]
        remaining = all_steps[current_step_idx:]
    
    return GenerationStatusResponse(
        episode_id=episode.id,
        status=status,
        current_step=current_step,
        steps_completed=completed,
        steps_remaining=remaining,
        error_message=episode.error_message,
        script_ready=bool(episode.script_json),
        voiceover_ready=bool(episode.voice_audio_url),
        sounds_ready=bool(episode.sounds_json) if episode.include_sound_effects else True,
        music_ready=bool(episode.music_url) if episode.include_background_music else True,
        audio_ready=bool(episode.final_audio_url),
        cover_ready=bool(episode.cover_url)
    )


    from ..services.music_service import MusicService
    
    # Check if voice audio exists
    if not episode.voice_audio_url or not episode.voice_audio_duration_seconds:
        raise HTTPException(status_code=400, detail="Voice audio must be generated first")
    
    # Get project for genre/atmosphere info
    project_result = await db.execute(
        select(Project).where(Project.id == episode.project_id)
    )
    project = project_result.scalar_one()
    
    # Build music prompt
    if request.prompt:
        music_prompt = request.prompt
    else:
        music_prompt = MusicService.build_music_prompt(
            genre_tone=project.genre_tone,
            musical_atmosphere=project.musical_atmosphere
        )
    
    # Calculate duration in ms (from voice audio)
    duration_ms = int(episode.voice_audio_duration_seconds * 1000)
    
    # Update status
    episode.status = "music_generating"
    await db.commit()
    
    try:
        music_service = MusicService(current_user.elevenlabs_api_key)
        storage_service = StorageService(
            current_user.storage_type,
            current_user.google_drive_credentials
        )
        
        # Generate music
        music_bytes = await music_service.generate_music(
            prompt=music_prompt,
            duration_ms=duration_ms,
            force_instrumental=True
        )
        
        # Save music file
        music_filename = f"music_{episode.id}.mp3"
        music_url = await storage_service.save_bytes(
            music_bytes,
            filename=music_filename,
            subfolder="music"
        )
        
        episode.music_url = music_url
        episode.status = EpisodeStatus.DONE.value
        await db.commit()
        
        return {
            "episode_id": str(episode.id),
            "music_url": music_url,
            "duration_ms": duration_ms,
            "prompt": music_prompt
        }
        
    except Exception as e:
        episode.status = EpisodeStatus.ERROR.value
        episode.error_message = str(e)
        await db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/music/{episode_id}/merge")
async def merge_audio_with_music(
    episode_id: UUID,
    request: MergeAudioRequest,
    episode: Episode = Depends(verify_episode_ownership),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Merge voice audio with background music"""
    from ..services.music_service import MusicService
    import tempfile
    import os
    
    # Check prerequisites
    if not episode.voice_audio_url:
        raise HTTPException(status_code=400, detail="Voice audio not found")
    if not episode.music_url:
        raise HTTPException(status_code=400, detail="Music not generated yet")
    
    storage_service = StorageService(
        current_user.storage_type,
        current_user.google_drive_credentials
    )
    
    try:
        # Get local paths
        voice_path = f"/var/www/heinercast/storage{episode.voice_audio_url.replace('/storage', '')}"
        music_path = f"/var/www/heinercast/storage{episode.music_url.replace('/storage', '')}"
        
        # Create temp output file
        output_filename = f"merged_{episode.id}_{abs(int(request.music_volume_db))}db.mp3"
        output_path = f"/var/www/heinercast/storage/audio/{output_filename}"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Merge audio
        await MusicService.merge_audio_with_music(
            voice_path=voice_path,
            music_path=music_path,
            output_path=output_path,
            music_volume_db=request.music_volume_db
        )
        
        # Save URL
        merged_url = f"/storage/audio/{output_filename}"
        episode.final_audio_url = merged_url
        await db.commit()
        
        return {
            "episode_id": str(episode.id),
            "merged_url": merged_url,
            "music_volume_db": request.music_volume_db
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/music/{episode_id}")
async def delete_music(
    episode_id: UUID,
    episode: Episode = Depends(verify_episode_ownership),
    db: AsyncSession = Depends(get_db)
):
    """Delete generated music"""
    import os
    
    if episode.music_url:
        music_path = f"/var/www/heinercast/storage{episode.music_url.replace('/storage', '')}"
        if os.path.exists(music_path):
            os.remove(music_path)
        episode.music_url = None
        await db.commit()
    
    return {"message": "Music deleted"}


@router.delete("/music/{episode_id}/merged")
async def delete_merged_audio(
    episode_id: UUID,
    episode: Episode = Depends(verify_episode_ownership),
    db: AsyncSession = Depends(get_db)
):
    """Delete merged audio"""
    import os
    
    if episode.final_audio_url:
        merged_path = f"/var/www/heinercast/storage{episode.final_audio_url.replace('/storage', '')}"
        if os.path.exists(merged_path):
            os.remove(merged_path)
        episode.final_audio_url = None
        await db.commit()
    
    return {"message": "Merged audio deleted"}
