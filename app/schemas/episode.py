"""
Episode Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID

from pydantic import BaseModel, Field


class ScriptLine(BaseModel):
    """Schema for a single script line"""
    speaker: str
    voice_id: str
    text: str
    sound_effect: Optional[str] = None


class ScriptContent(BaseModel):
    """Schema for full script content"""
    story_title: str
    genre_tone: str
    approx_duration_minutes: int
    lines: List[ScriptLine]


class SoundEffect(BaseModel):
    """Schema for a sound effect"""
    prompt: str
    url: str
    start_time: float
    duration: float


class CoverVariant(BaseModel):
    """Schema for a cover variant"""
    url: str
    selected: bool = False


class EpisodeBase(BaseModel):
    """Base episode schema"""
    title: Optional[str] = Field(None, max_length=200)
    title_auto_generated: bool = True
    show_episode_number: bool = True
    description: str = Field(max_length=5000)
    target_duration_minutes: int = Field(ge=1, le=60, default=10)
    include_sound_effects: bool = False
    include_background_music: bool = False


class EpisodeCreate(EpisodeBase):
    """Schema for creating an episode"""
    pass


class EpisodeUpdate(BaseModel):
    """Schema for updating an episode"""
    title: Optional[str] = Field(None, max_length=200)
    title_auto_generated: Optional[bool] = None
    show_episode_number: Optional[bool] = None
    description: Optional[str] = Field(None, max_length=5000)
    target_duration_minutes: Optional[int] = Field(None, ge=1, le=60)
    include_sound_effects: Optional[bool] = None
    include_background_music: Optional[bool] = None


class EpisodeScriptUpdate(BaseModel):
    """Schema for updating episode script"""
    script_json: dict  # Full script JSON
    script_text: Optional[str] = None  # Optional text version


class EpisodeResponse(BaseModel):
    """Schema for episode response"""
    id: UUID
    project_id: UUID
    episode_number: int
    title: str
    title_auto_generated: bool
    show_episode_number: bool
    description: str
    target_duration_minutes: int
    
    # Generation options
    include_sound_effects: bool
    include_background_music: bool
    
    # Status
    status: str
    error_message: Optional[str] = None
    
    # Script
    has_script: bool = False
    script_text: Optional[str] = None
    
    # Audio
    voice_audio_url: Optional[str] = None
    voice_audio_duration_seconds: Optional[float] = None
    final_audio_url: Optional[str] = None
    final_audio_duration_seconds: Optional[float] = None
    
    # Music
    music_url: Optional[str] = None
    
    # Cover
    cover_url: Optional[str] = None
    cover_variants_count: int = 0
    
    # Summary
    summary: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EpisodeDetailResponse(EpisodeResponse):
    """Schema for detailed episode response"""
    script_json: Optional[dict] = None
    voice_timestamps_json: Optional[dict] = None
    sounds_json: Optional[List[SoundEffect]] = None
    music_composition_plan: Optional[dict] = None
    cover_reference_image_url: Optional[str] = None
    cover_variants_json: Optional[List[CoverVariant]] = None

    model_config = {"from_attributes": True}


class EpisodeListResponse(BaseModel):
    """Schema for episode list response"""
    items: List[EpisodeResponse]
    total: int


class EpisodeContinuationCreate(BaseModel):
    """Schema for creating episode continuation"""
    description: str = Field(max_length=5000)
    title: Optional[str] = Field(None, max_length=200)
    title_auto_generated: bool = True
    show_episode_number: bool = True
    target_duration_minutes: int = Field(ge=1, le=60, default=10)
    include_sound_effects: Optional[bool] = None  # If None, inherit from project
    include_background_music: Optional[bool] = None  # If None, inherit from project
