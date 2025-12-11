"""
Voice Pydantic Schemas
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class VoiceBase(BaseModel):
    """Base voice schema"""
    name: str = Field(max_length=100)
    elevenlabs_name: str = Field(max_length=100)
    elevenlabs_voice_id: str = Field(max_length=50, pattern=r"^[a-zA-Z0-9]+$")
    description: Optional[str] = None
    is_favorite: bool = False


class VoiceCreate(VoiceBase):
    """Schema for creating a voice"""
    pass


class VoiceUpdate(BaseModel):
    """Schema for updating a voice"""
    name: Optional[str] = Field(None, max_length=100)
    elevenlabs_name: Optional[str] = Field(None, max_length=100)
    elevenlabs_voice_id: Optional[str] = Field(None, max_length=50, pattern=r"^[a-zA-Z0-9]+$")
    description: Optional[str] = None
    is_favorite: Optional[bool] = None


class VoiceResponse(VoiceBase):
    """Schema for voice response"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VoiceTestRequest(BaseModel):
    """Schema for voice test request"""
    voice_id: str = Field(max_length=50)
    text: str = Field(max_length=500, default="Hello, this is a voice test.")


class VoiceTestResponse(BaseModel):
    """Schema for voice test response"""
    audio_url: str
    duration_seconds: float
