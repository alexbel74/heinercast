"""
Episodes API Endpoints
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.project_character import ProjectCharacter
from app.models.episode import Episode, EpisodeStatus
from app.schemas.episode import (
    EpisodeCreate, EpisodeUpdate, EpisodeResponse, EpisodeDetailResponse,
    EpisodeListResponse, EpisodeScriptUpdate, EpisodeContinuationCreate
)
from app.core.dependencies import get_current_user, verify_project_ownership, verify_episode_ownership
from app.core.exceptions import NotFoundError, EpisodeDeletionError, BusinessLogicError
# Build text directly

router = APIRouter()


@router.get("/{episode_id}", response_model=EpisodeDetailResponse)
async def get_episode(
    episode: Episode = Depends(verify_episode_ownership),
    db: AsyncSession = Depends(get_db)
):
    """Get episode details"""
    # Parse cover variants count
    cover_variants_count = 0
    if episode.cover_variants_json:
        cover_variants_count = len(episode.cover_variants_json) if isinstance(episode.cover_variants_json, list) else 0
    
    return EpisodeDetailResponse(
        id=episode.id,
        project_id=episode.project_id,
        episode_number=episode.episode_number,
        title=episode.title,
        title_auto_generated=episode.title_auto_generated,
        show_episode_number=episode.show_episode_number,
        description=episode.description,
        target_duration_minutes=episode.target_duration_minutes,
        include_sound_effects=episode.include_sound_effects,
        include_background_music=episode.include_background_music,
        status=episode.status,
        error_message=episode.error_message,
        has_script=bool(episode.script_json),
        script_text=episode.script_text,
        script_json=episode.script_json,
        voice_audio_url=episode.voice_audio_url,
        voice_audio_duration_seconds=episode.voice_audio_duration_seconds,
        voice_timestamps_json=episode.voice_timestamps_json,
        final_audio_url=episode.final_audio_url,
        final_audio_duration_seconds=episode.final_audio_duration_seconds,
        music_url=episode.music_url,
        music_composition_plan=episode.music_composition_plan,
        sounds_json=episode.sounds_json,
        cover_url=episode.cover_url,
        cover_reference_image_url=episode.cover_reference_image_url,
        cover_variants_json=episode.cover_variants_json,
        cover_variants_count=cover_variants_count,
        summary=episode.summary,
        created_at=episode.created_at,
        updated_at=episode.updated_at
    )


@router.put("/{episode_id}", response_model=EpisodeResponse)
async def update_episode(
    update_data: EpisodeUpdate,
    episode: Episode = Depends(verify_episode_ownership),
    db: AsyncSession = Depends(get_db)
):
    """Update an episode"""
    if update_data.title is not None:
        episode.title = update_data.title
        episode.title_auto_generated = False
    if update_data.title_auto_generated is not None:
        episode.title_auto_generated = update_data.title_auto_generated
    if update_data.show_episode_number is not None:
        episode.show_episode_number = update_data.show_episode_number
    if update_data.description is not None:
        episode.description = update_data.description
    if update_data.target_duration_minutes is not None:
        episode.target_duration_minutes = update_data.target_duration_minutes
    if update_data.include_sound_effects is not None:
        episode.include_sound_effects = update_data.include_sound_effects
    if update_data.include_background_music is not None:
        episode.include_background_music = update_data.include_background_music
    
    episode.updated_at = datetime.utcnow()
    
    cover_variants_count = 0
    if episode.cover_variants_json:
        cover_variants_count = len(episode.cover_variants_json) if isinstance(episode.cover_variants_json, list) else 0
    
    return EpisodeResponse(
        id=episode.id,
        project_id=episode.project_id,
        episode_number=episode.episode_number,
        title=episode.title,
        title_auto_generated=episode.title_auto_generated,
        show_episode_number=episode.show_episode_number,
        description=episode.description,
        target_duration_minutes=episode.target_duration_minutes,
        include_sound_effects=episode.include_sound_effects,
        include_background_music=episode.include_background_music,
        status=episode.status,
        error_message=episode.error_message,
        has_script=bool(episode.script_json),
        script_text=episode.script_text,
        voice_audio_url=episode.voice_audio_url,
        voice_audio_duration_seconds=episode.voice_audio_duration_seconds,
        final_audio_url=episode.final_audio_url,
        final_audio_duration_seconds=episode.final_audio_duration_seconds,
        music_url=episode.music_url,
        cover_url=episode.cover_url,
        cover_variants_count=cover_variants_count,
        summary=episode.summary,
        created_at=episode.created_at,
        updated_at=episode.updated_at
    )


@router.delete("/{episode_id}")
async def delete_episode(
    episode: Episode = Depends(verify_episode_ownership),
    db: AsyncSession = Depends(get_db)
):
    """Delete an episode (only the last episode can be deleted)"""
    # Get the maximum episode number in the project
    result = await db.execute(
        select(func.max(Episode.episode_number))
        .where(Episode.project_id == episode.project_id)
    )
    max_episode_number = result.scalar() or 0
    
    if episode.episode_number != max_episode_number:
        raise EpisodeDeletionError("Only the last episode can be deleted")
    

    # Delete associated files from storage
    import os
    storage_base = "/var/www/heinercast/storage"
    
    files_to_delete = []
    
    # Audio files
    if episode.voice_audio_url:
        files_to_delete.append(episode.voice_audio_url)
    if episode.final_audio_url:
        files_to_delete.append(episode.final_audio_url)
    if episode.music_url:
        files_to_delete.append(episode.music_url)
    
    # Cover files
    if episode.cover_url:
        files_to_delete.append(episode.cover_url)
    if episode.cover_variants_json:
        for variant in episode.cover_variants_json:
            if variant.get("url"):
                files_to_delete.append(variant["url"])
    
    # Delete files
    for file_url in files_to_delete:
        if file_url and file_url.startswith("/storage/"):
            file_path = file_url.replace("/storage/", storage_base + "/")
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass  # Log error but continue

    await db.delete(episode)
    return {"message": "Episode deleted"}


@router.put("/{episode_id}/script", response_model=EpisodeResponse)
async def update_episode_script(
    script_data: EpisodeScriptUpdate,
    episode: Episode = Depends(verify_episode_ownership),
    db: AsyncSession = Depends(get_db)
):
    """Update episode script (manual editing)"""
    episode.script_json = script_data.script_json
    
    # Generate text version if not provided
    if script_data.script_text:
        episode.script_text = chr(10).join([f"{l.get('speaker', 'Unknown')}: {l.get('text', '')}" for l in lines])
    else:
        # Build text from JSON
        # Build text directly
        lines = script_data.script_json.get("lines", [])
        episode.script_text = chr(10).join([f"{l.get('speaker', 'Unknown')}: {l.get('text', '')}" for l in lines])
    
    # Update title from script if auto-generated
    if episode.title_auto_generated and script_data.script_json.get("story_title"):
        episode.title = script_data.script_json["story_title"]
    
    episode.updated_at = datetime.utcnow()
    
    # If status was script_done or later and script is edited, 
    # we may need to regenerate audio
    if episode.status not in [EpisodeStatus.DRAFT.value, EpisodeStatus.SCRIPT_GENERATING.value]:
        episode.status = EpisodeStatus.SCRIPT_DONE.value
    
    cover_variants_count = 0
    if episode.cover_variants_json:
        cover_variants_count = len(episode.cover_variants_json) if isinstance(episode.cover_variants_json, list) else 0
    
    return EpisodeResponse(
        id=episode.id,
        project_id=episode.project_id,
        episode_number=episode.episode_number,
        title=episode.title,
        title_auto_generated=episode.title_auto_generated,
        show_episode_number=episode.show_episode_number,
        description=episode.description,
        target_duration_minutes=episode.target_duration_minutes,
        include_sound_effects=episode.include_sound_effects,
        include_background_music=episode.include_background_music,
        status=episode.status,
        error_message=episode.error_message,
        has_script=bool(episode.script_json),
        script_text=episode.script_text,
        voice_audio_url=episode.voice_audio_url,
        voice_audio_duration_seconds=episode.voice_audio_duration_seconds,
        final_audio_url=episode.final_audio_url,
        final_audio_duration_seconds=episode.final_audio_duration_seconds,
        music_url=episode.music_url,
        cover_url=episode.cover_url,
        cover_variants_count=cover_variants_count,
        summary=episode.summary,
        created_at=episode.created_at,
        updated_at=episode.updated_at
    )


@router.post("/{episode_id}/continuation", response_model=EpisodeResponse, status_code=201)
async def create_continuation(
    cont_data: EpisodeContinuationCreate,
    episode: Episode = Depends(verify_episode_ownership),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a continuation episode"""
    # Check that parent episode is done
    if episode.status != EpisodeStatus.DONE.value:
        raise BusinessLogicError("Parent episode must be completed before creating a continuation")
    
    # Get the project
    project_result = await db.execute(
        select(Project).where(Project.id == episode.project_id)
    )
    project = project_result.scalar_one()
    
    # Get next episode number
    max_result = await db.execute(
        select(func.max(Episode.episode_number))
        .where(Episode.project_id == project.id)
    )
    next_number = (max_result.scalar() or 0) + 1
    
    # Determine generation options (inherit from project if not specified)
    include_sound_effects = (
        cont_data.include_sound_effects 
        if cont_data.include_sound_effects is not None 
        else project.include_sound_effects
    )
    include_background_music = (
        cont_data.include_background_music 
        if cont_data.include_background_music is not None 
        else project.include_background_music
    )
    
    # Create new episode
    new_episode = Episode(
        project_id=project.id,
        episode_number=next_number,
        title=cont_data.title or f"Episode {next_number}",
        title_auto_generated=cont_data.title_auto_generated,
        show_episode_number=cont_data.show_episode_number,
        description=cont_data.description,
        target_duration_minutes=cont_data.target_duration_minutes,
        include_sound_effects=include_sound_effects,
        include_background_music=include_background_music,
        status=EpisodeStatus.DRAFT.value
    )
    
    db.add(new_episode)
    await db.flush()
    
    return EpisodeResponse(
        id=new_episode.id,
        project_id=new_episode.project_id,
        episode_number=new_episode.episode_number,
        title=new_episode.title,
        title_auto_generated=new_episode.title_auto_generated,
        show_episode_number=new_episode.show_episode_number,
        description=new_episode.description,
        target_duration_minutes=new_episode.target_duration_minutes,
        include_sound_effects=new_episode.include_sound_effects,
        include_background_music=new_episode.include_background_music,
        status=new_episode.status,
        error_message=None,
        has_script=False,
        script_text=None,
        voice_audio_url=None,
        voice_audio_duration_seconds=None,
        final_audio_url=None,
        final_audio_duration_seconds=None,
        music_url=None,
        cover_url=None,
        cover_variants_count=0,
        summary=None,
        created_at=new_episode.created_at,
        updated_at=new_episode.updated_at
    )


# Episodes list is under projects router
# These endpoints are for direct episode access by ID


@router.delete("/{episode_id}/cover/{variant_index}")
async def delete_cover_variant(
    episode_id: str,
    variant_index: int,
    episode: Episode = Depends(verify_episode_ownership),
    db: AsyncSession = Depends(get_db)
):
    """Delete a specific cover variant"""
    import os
    
    if not episode.cover_variants_json:
        raise BusinessLogicError("No cover variants available")
    
    variants = episode.cover_variants_json
    if variant_index >= len(variants) or variant_index < 0:
        raise BusinessLogicError(f"Invalid variant index: {variant_index}")
    
    # Get URL of variant to delete
    variant_url = variants[variant_index].get("url")
    
    # Delete file from storage
    if variant_url and variant_url.startswith("/storage/"):
        storage_base = "/var/www/heinercast/storage"
        file_path = variant_url.replace("/storage/", storage_base + "/")
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
    
    # Remove variant from list
    was_selected = variants[variant_index].get("selected", False)
    variants.pop(variant_index)
    
    # If deleted variant was selected, select first remaining
    if was_selected and variants:
        variants[0]["selected"] = True
        episode.cover_url = variants[0]["url"]
    elif not variants:
        episode.cover_url = None
    
    episode.cover_variants_json = variants if variants else None
    
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(episode, "cover_variants_json")
    episode.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Cover variant deleted", "remaining_variants": len(variants) if variants else 0}


@router.delete("/{episode_id}/audio")
async def delete_episode_audio(
    episode: Episode = Depends(verify_episode_ownership),
    db: AsyncSession = Depends(get_db)
):
    """Delete episode audio file"""
    import os
    
    if episode.voice_audio_url:
        file_path = f"/var/www/heinercast/storage{episode.voice_audio_url.replace('/storage', '')}"
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except: pass
        episode.voice_audio_url = None
        episode.voice_audio_duration_seconds = None
    
    if episode.final_audio_url:
        file_path = f"/var/www/heinercast/storage{episode.final_audio_url.replace('/storage', '')}"
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except: pass
        episode.final_audio_url = None
        episode.final_audio_duration_seconds = None
    
    episode.status = EpisodeStatus.SCRIPT_DONE.value
    await db.commit()
    
    return {"message": "Audio deleted"}
