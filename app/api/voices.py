"""
Voices API Endpoints
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.user import User
from app.models.voice import Voice
from app.schemas.voice import (
    VoiceCreate, VoiceUpdate, VoiceResponse, VoiceTestRequest, VoiceTestResponse
)
from app.core.dependencies import get_current_user, verify_voice_ownership
from app.core.exceptions import NotFoundError
from app.services.elevenlabs_service import ElevenLabsService
from app.services.storage_service import StorageService

router = APIRouter()


@router.get("", response_model=List[VoiceResponse])
async def list_voices(
    search: Optional[str] = Query(None, max_length=100),
    favorites_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all voices in user's library"""
    query = select(Voice).where(Voice.user_id == current_user.id)
    
    if favorites_only:
        query = query.where(Voice.is_favorite == True)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Voice.name.ilike(search_pattern)) |
            (Voice.elevenlabs_name.ilike(search_pattern))
        )
    
    query = query.order_by(Voice.is_favorite.desc(), Voice.name)
    
    result = await db.execute(query)
    voices = result.scalars().all()
    
    return [VoiceResponse.model_validate(voice) for voice in voices]


@router.post("", response_model=VoiceResponse, status_code=201)
async def create_voice(
    voice_data: VoiceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a voice to user's library"""
    voice = Voice(
        user_id=current_user.id,
        name=voice_data.name,
        elevenlabs_name=voice_data.elevenlabs_name,
        elevenlabs_voice_id=voice_data.elevenlabs_voice_id,
        description=voice_data.description,
        is_favorite=voice_data.is_favorite
    )
    
    db.add(voice)
    await db.flush()
    
    return VoiceResponse.model_validate(voice)


@router.get("/{voice_id}", response_model=VoiceResponse)
async def get_voice(
    voice: Voice = Depends(verify_voice_ownership)
):
    """Get voice details"""
    return VoiceResponse.model_validate(voice)


@router.put("/{voice_id}", response_model=VoiceResponse)
async def update_voice(
    update_data: VoiceUpdate,
    voice: Voice = Depends(verify_voice_ownership),
    db: AsyncSession = Depends(get_db)
):
    """Update a voice"""
    if update_data.name is not None:
        voice.name = update_data.name
    if update_data.elevenlabs_name is not None:
        voice.elevenlabs_name = update_data.elevenlabs_name
    if update_data.elevenlabs_voice_id is not None:
        voice.elevenlabs_voice_id = update_data.elevenlabs_voice_id
    if update_data.description is not None:
        voice.description = update_data.description
    if update_data.is_favorite is not None:
        voice.is_favorite = update_data.is_favorite
    
    voice.updated_at = datetime.utcnow()
    
    return VoiceResponse.model_validate(voice)


@router.delete("/{voice_id}")
async def delete_voice(
    voice: Voice = Depends(verify_voice_ownership),
    db: AsyncSession = Depends(get_db)
):
    """Delete a voice from library"""
    await db.delete(voice)
    return {"message": "Voice deleted"}


@router.post("/test", response_model=VoiceTestResponse)
async def test_voice(
    test_data: VoiceTestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Test a voice with a short audio sample"""
    # Initialize services
    elevenlabs_service = ElevenLabsService(current_user)
    storage_service = StorageService(
        current_user.storage_type,
        current_user.google_drive_credentials
    )
    
    # Generate test audio
    audio_bytes = await elevenlabs_service.test_voice(
        voice_id=test_data.voice_id,
        text=test_data.text
    )
    
    # Save to temp storage
    audio_url = await storage_service.save_file(
        audio_bytes,
        subfolder="temp",
        extension="mp3"
    )
    
    # Get duration
    from app.services.audio_service import AudioService
    audio_service = AudioService()
    duration = await audio_service.get_audio_duration(audio_url)
    
    return VoiceTestResponse(
        audio_url=audio_url,
        duration_seconds=duration
    )


@router.get("/elevenlabs/available", response_model=List[dict])
async def get_available_elevenlabs_voices(
    current_user: User = Depends(get_current_user)
):
    """Get list of available voices from ElevenLabs account"""
    elevenlabs_service = ElevenLabsService(current_user)
    voices = await elevenlabs_service.get_voices()
    
    return [
        {
            "voice_id": voice.get("voice_id"),
            "name": voice.get("name"),
            "category": voice.get("category"),
            "description": voice.get("description"),
            "preview_url": voice.get("preview_url"),
            "labels": voice.get("labels", {})
        }
        for voice in voices
    ]


@router.post("/import-from-elevenlabs", response_model=VoiceResponse, status_code=201)
async def import_voice_from_elevenlabs(
    voice_id: str,
    name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Import a voice from ElevenLabs to user's library"""
    # Get voice info from ElevenLabs
    elevenlabs_service = ElevenLabsService(current_user)
    voices = await elevenlabs_service.get_voices()
    
    # Find the voice
    elevenlabs_voice = None
    for voice in voices:
        if voice.get("voice_id") == voice_id:
            elevenlabs_voice = voice
            break
    
    if not elevenlabs_voice:
        raise NotFoundError("ElevenLabs voice", voice_id)
    
    # Create voice in library
    voice = Voice(
        user_id=current_user.id,
        name=name or elevenlabs_voice.get("name", "Imported Voice"),
        elevenlabs_name=elevenlabs_voice.get("name", ""),
        elevenlabs_voice_id=voice_id,
        description=elevenlabs_voice.get("description"),
        is_favorite=False
    )
    
    db.add(voice)
    await db.flush()
    
    return VoiceResponse.model_validate(voice)
