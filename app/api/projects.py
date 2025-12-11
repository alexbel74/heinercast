"""
Projects API Endpoints
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
from app.models.episode import Episode
from app.models.voice import Voice
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectDetailResponse,
    ProjectListResponse, ProjectCharacterCreate, ProjectCharacterUpdate,
    ProjectCharacterResponse
)
from app.core.dependencies import get_current_user, verify_project_ownership
from app.core.exceptions import NotFoundError, MaxCharactersExceededError

router = APIRouter()

MAX_CHARACTERS_PER_PROJECT = 5


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all projects for the current user"""
    # Count total
    count_result = await db.execute(
        select(func.count(Project.id)).where(Project.user_id == current_user.id)
    )
    total = count_result.scalar() or 0
    
    # Get projects with counts
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Project)
        .where(Project.user_id == current_user.id)
        .order_by(Project.updated_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    projects = result.scalars().all()
    
    # Get episode and character counts
    items = []
    for project in projects:
        # Count episodes
        ep_result = await db.execute(
            select(func.count(Episode.id)).where(Episode.project_id == project.id)
        )
        episodes_count = ep_result.scalar() or 0
        
        # Count characters
        char_result = await db.execute(
            select(func.count(ProjectCharacter.id)).where(ProjectCharacter.project_id == project.id)
        )
        characters_count = char_result.scalar() or 0
        
        items.append(ProjectResponse(
            id=project.id,
            user_id=project.user_id,
            title=project.title,
            description=project.description,
            genre_tone=project.genre_tone,
            musical_atmosphere=project.musical_atmosphere,
            include_sound_effects=project.include_sound_effects,
            include_background_music=project.include_background_music,
            cover_url=project.cover_url,
            cover_prompt=project.cover_prompt,
            created_at=project.created_at,
            updated_at=project.updated_at,
            episodes_count=episodes_count,
            characters_count=characters_count
        ))
    
    return ProjectListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new project"""
    project = Project(
        user_id=current_user.id,
        title=project_data.title,
        description=project_data.description,
        genre_tone=project_data.genre_tone,
        musical_atmosphere=project_data.musical_atmosphere,
        include_sound_effects=project_data.include_sound_effects,
        include_background_music=project_data.include_background_music
    )
    
    db.add(project)
    await db.flush()
    
    return ProjectResponse(
        id=project.id,
        user_id=project.user_id,
        title=project.title,
        description=project.description,
        genre_tone=project.genre_tone,
        musical_atmosphere=project.musical_atmosphere,
        include_sound_effects=project.include_sound_effects,
        include_background_music=project.include_background_music,
        cover_url=project.cover_url,
        cover_prompt=project.cover_prompt,
        created_at=project.created_at,
        updated_at=project.updated_at,
        episodes_count=0,
        characters_count=0
    )


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project: Project = Depends(verify_project_ownership),
    db: AsyncSession = Depends(get_db)
):
    """Get project details with characters"""
    # Get characters with voice info
    char_result = await db.execute(
        select(ProjectCharacter)
        .options(selectinload(ProjectCharacter.voice))
        .where(ProjectCharacter.project_id == project.id)
        .order_by(ProjectCharacter.sort_order)
    )
    characters = char_result.scalars().all()
    
    # Get episode count and latest episode info
    ep_result = await db.execute(
        select(Episode)
        .where(Episode.project_id == project.id)
        .order_by(Episode.episode_number.desc())
        .limit(1)
    )
    latest_episode = ep_result.scalar_one_or_none()
    
    ep_count_result = await db.execute(
        select(func.count(Episode.id)).where(Episode.project_id == project.id)
    )
    episodes_count = ep_count_result.scalar() or 0
    
    # Build character responses
    char_responses = []
    for char in characters:
        char_responses.append(ProjectCharacterResponse(
            id=char.id,
            project_id=char.project_id,
            voice_id=char.voice_id,
            role=char.role,
            character_name=char.character_name,
            sort_order=char.sort_order,
            created_at=char.created_at,
            voice_name=char.voice.name if char.voice else None,
            elevenlabs_name=char.voice.elevenlabs_name if char.voice else None,
            elevenlabs_voice_id=char.voice.elevenlabs_voice_id if char.voice else None
        ))
    
    return ProjectDetailResponse(
        id=project.id,
        user_id=project.user_id,
        title=project.title,
        description=project.description,
        genre_tone=project.genre_tone,
        musical_atmosphere=project.musical_atmosphere,
        include_sound_effects=project.include_sound_effects,
        include_background_music=project.include_background_music,
        cover_url=project.cover_url,
        cover_prompt=project.cover_prompt,
        created_at=project.created_at,
        updated_at=project.updated_at,
        episodes_count=episodes_count,
        characters_count=len(characters),
        characters=char_responses,
        latest_episode_number=latest_episode.episode_number if latest_episode else 0,
        latest_episode_status=latest_episode.status if latest_episode else None
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    update_data: ProjectUpdate,
    project: Project = Depends(verify_project_ownership),
    db: AsyncSession = Depends(get_db)
):
    """Update a project"""
    if update_data.title is not None:
        project.title = update_data.title
    if update_data.description is not None:
        project.description = update_data.description
    if update_data.genre_tone is not None:
        project.genre_tone = update_data.genre_tone
    if update_data.musical_atmosphere is not None:
        project.musical_atmosphere = update_data.musical_atmosphere
    if update_data.include_sound_effects is not None:
        project.include_sound_effects = update_data.include_sound_effects
    if update_data.include_background_music is not None:
        project.include_background_music = update_data.include_background_music
    
    project.updated_at = datetime.utcnow()
    
    # Get counts
    ep_count_result = await db.execute(
        select(func.count(Episode.id)).where(Episode.project_id == project.id)
    )
    episodes_count = ep_count_result.scalar() or 0
    
    char_count_result = await db.execute(
        select(func.count(ProjectCharacter.id)).where(ProjectCharacter.project_id == project.id)
    )
    characters_count = char_count_result.scalar() or 0
    
    return ProjectResponse(
        id=project.id,
        user_id=project.user_id,
        title=project.title,
        description=project.description,
        genre_tone=project.genre_tone,
        musical_atmosphere=project.musical_atmosphere,
        include_sound_effects=project.include_sound_effects,
        include_background_music=project.include_background_music,
        cover_url=project.cover_url,
        cover_prompt=project.cover_prompt,
        created_at=project.created_at,
        updated_at=project.updated_at,
        episodes_count=episodes_count,
        characters_count=characters_count
    )


@router.delete("/{project_id}")
async def delete_project(
    project: Project = Depends(verify_project_ownership),
    db: AsyncSession = Depends(get_db)
):
    """Delete a project and all its episodes"""
    await db.delete(project)
    return {"message": "Project deleted"}


# Characters endpoints
@router.get("/{project_id}/characters", response_model=List[ProjectCharacterResponse])
async def list_project_characters(
    project: Project = Depends(verify_project_ownership),
    db: AsyncSession = Depends(get_db)
):
    """List all characters in a project"""
    result = await db.execute(
        select(ProjectCharacter)
        .options(selectinload(ProjectCharacter.voice))
        .where(ProjectCharacter.project_id == project.id)
        .order_by(ProjectCharacter.sort_order)
    )
    characters = result.scalars().all()
    
    return [
        ProjectCharacterResponse(
            id=char.id,
            project_id=char.project_id,
            voice_id=char.voice_id,
            role=char.role,
            character_name=char.character_name,
            sort_order=char.sort_order,
            created_at=char.created_at,
            voice_name=char.voice.name if char.voice else None,
            elevenlabs_name=char.voice.elevenlabs_name if char.voice else None,
            elevenlabs_voice_id=char.voice.elevenlabs_voice_id if char.voice else None
        )
        for char in characters
    ]


@router.post("/{project_id}/characters", response_model=ProjectCharacterResponse, status_code=201)
async def add_character(
    char_data: ProjectCharacterCreate,
    project: Project = Depends(verify_project_ownership),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a character to a project"""
    # Check character limit
    count_result = await db.execute(
        select(func.count(ProjectCharacter.id)).where(ProjectCharacter.project_id == project.id)
    )
    current_count = count_result.scalar() or 0
    
    if current_count >= MAX_CHARACTERS_PER_PROJECT:
        raise MaxCharactersExceededError(MAX_CHARACTERS_PER_PROJECT)
    
    # Verify voice belongs to user
    voice_result = await db.execute(
        select(Voice).where(
            Voice.id == char_data.voice_id,
            Voice.user_id == current_user.id
        )
    )
    voice = voice_result.scalar_one_or_none()
    
    if not voice:
        raise NotFoundError("Voice", str(char_data.voice_id))
    
    # Create character
    character = ProjectCharacter(
        project_id=project.id,
        voice_id=char_data.voice_id,
        role=char_data.role,
        character_name=char_data.character_name,
        sort_order=char_data.sort_order
    )
    
    db.add(character)
    await db.flush()
    
    project.updated_at = datetime.utcnow()
    
    return ProjectCharacterResponse(
        id=character.id,
        project_id=character.project_id,
        voice_id=character.voice_id,
        role=character.role,
        character_name=character.character_name,
        sort_order=character.sort_order,
        created_at=character.created_at,
        voice_name=voice.name,
        elevenlabs_name=voice.elevenlabs_name,
        elevenlabs_voice_id=voice.elevenlabs_voice_id
    )


@router.put("/{project_id}/characters/{character_id}", response_model=ProjectCharacterResponse)
async def update_character(
    character_id: UUID,
    char_data: ProjectCharacterUpdate,
    project: Project = Depends(verify_project_ownership),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a project character"""
    result = await db.execute(
        select(ProjectCharacter)
        .options(selectinload(ProjectCharacter.voice))
        .where(
            ProjectCharacter.id == character_id,
            ProjectCharacter.project_id == project.id
        )
    )
    character = result.scalar_one_or_none()
    
    if not character:
        raise NotFoundError("Character", str(character_id))
    
    # Update voice if provided
    if char_data.voice_id:
        voice_result = await db.execute(
            select(Voice).where(
                Voice.id == char_data.voice_id,
                Voice.user_id == current_user.id
            )
        )
        voice = voice_result.scalar_one_or_none()
        if not voice:
            raise NotFoundError("Voice", str(char_data.voice_id))
        character.voice_id = char_data.voice_id
        character.voice = voice
    
    if char_data.role is not None:
        character.role = char_data.role
    if char_data.character_name is not None:
        character.character_name = char_data.character_name
    if char_data.sort_order is not None:
        character.sort_order = char_data.sort_order
    
    project.updated_at = datetime.utcnow()
    
    return ProjectCharacterResponse(
        id=character.id,
        project_id=character.project_id,
        voice_id=character.voice_id,
        role=character.role,
        character_name=character.character_name,
        sort_order=character.sort_order,
        created_at=character.created_at,
        voice_name=character.voice.name if character.voice else None,
        elevenlabs_name=character.voice.elevenlabs_name if character.voice else None,
        elevenlabs_voice_id=character.voice.elevenlabs_voice_id if character.voice else None
    )


@router.delete("/{project_id}/characters/{character_id}")
async def remove_character(
    character_id: UUID,
    project: Project = Depends(verify_project_ownership),
    db: AsyncSession = Depends(get_db)
):
    """Remove a character from a project"""
    result = await db.execute(
        select(ProjectCharacter).where(
            ProjectCharacter.id == character_id,
            ProjectCharacter.project_id == project.id
        )
    )
    character = result.scalar_one_or_none()
    
    if not character:
        raise NotFoundError("Character", str(character_id))
    
    await db.delete(character)
    project.updated_at = datetime.utcnow()
    
    return {"message": "Character removed"}


# Episodes endpoints
from app.schemas.episode import EpisodeCreate, EpisodeResponse, EpisodeListResponse
from app.models.episode import Episode, EpisodeStatus


@router.get("/{project_id}/episodes", response_model=EpisodeListResponse)
async def list_episodes(
    project: Project = Depends(verify_project_ownership),
    db: AsyncSession = Depends(get_db)
):
    """List all episodes in a project"""
    result = await db.execute(
        select(Episode)
        .where(Episode.project_id == project.id)
        .order_by(Episode.episode_number)
    )
    episodes = result.scalars().all()
    
    items = []
    for ep in episodes:
        cover_variants_count = 0
        if ep.cover_variants_json:
            cover_variants_count = len(ep.cover_variants_json) if isinstance(ep.cover_variants_json, list) else 0
        
        items.append(EpisodeResponse(
            id=ep.id,
            project_id=ep.project_id,
            episode_number=ep.episode_number,
            title=ep.title,
            title_auto_generated=ep.title_auto_generated,
            show_episode_number=ep.show_episode_number,
            description=ep.description,
            target_duration_minutes=ep.target_duration_minutes,
            include_sound_effects=ep.include_sound_effects,
            include_background_music=ep.include_background_music,
            status=ep.status,
            error_message=ep.error_message,
            has_script=bool(ep.script_json),
            script_text=ep.script_text,
            voice_audio_url=ep.voice_audio_url,
            voice_audio_duration_seconds=ep.voice_audio_duration_seconds,
            final_audio_url=ep.final_audio_url,
            final_audio_duration_seconds=ep.final_audio_duration_seconds,
            music_url=ep.music_url,
            cover_url=ep.cover_url,
            cover_variants_count=cover_variants_count,
            summary=ep.summary,
            created_at=ep.created_at,
            updated_at=ep.updated_at
        ))
    
    return EpisodeListResponse(items=items, total=len(items))


@router.post("/{project_id}/episodes", response_model=EpisodeResponse, status_code=201)
async def create_episode(
    episode_data: EpisodeCreate,
    project: Project = Depends(verify_project_ownership),
    db: AsyncSession = Depends(get_db)
):
    """Create a new episode in a project"""
    # Get next episode number
    max_result = await db.execute(
        select(func.max(Episode.episode_number))
        .where(Episode.project_id == project.id)
    )
    next_number = (max_result.scalar() or 0) + 1
    
    # Determine generation options (inherit from project if not specified in episode)
    include_sound_effects = episode_data.include_sound_effects
    include_background_music = episode_data.include_background_music
    
    # If episode options are default (False), check project settings
    if not episode_data.include_sound_effects and project.include_sound_effects:
        include_sound_effects = True
    if not episode_data.include_background_music and project.include_background_music:
        include_background_music = True
    
    # Create episode
    episode = Episode(
        project_id=project.id,
        episode_number=next_number,
        title=episode_data.title or f"Episode {next_number}",
        title_auto_generated=episode_data.title_auto_generated,
        show_episode_number=episode_data.show_episode_number,
        description=episode_data.description,
        target_duration_minutes=episode_data.target_duration_minutes,
        include_sound_effects=include_sound_effects,
        include_background_music=include_background_music,
        status=EpisodeStatus.DRAFT.value
    )
    
    db.add(episode)
    await db.flush()
    
    project.updated_at = datetime.utcnow()
    
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
        created_at=episode.created_at,
        updated_at=episode.updated_at
    )
