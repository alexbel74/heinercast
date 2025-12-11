"""
Generation Pydantic Schemas
"""
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class GenerateScriptRequest(BaseModel):
    """Schema for script generation request"""
    # Optional overrides
    custom_prompt: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class GenerateScriptResponse(BaseModel):
    """Schema for script generation response"""
    episode_id: UUID
    status: str
    story_title: Optional[str] = None
    lines_count: int = 0
    estimated_duration_minutes: int = 0


class GenerateVoiceoverRequest(BaseModel):
    """Schema for voiceover generation request"""
    # No additional parameters needed, uses episode script
    pass


class GenerateVoiceoverResponse(BaseModel):
    """Schema for voiceover generation response"""
    episode_id: UUID
    status: str
    audio_url: Optional[str] = None
    duration_seconds: Optional[float] = None
    parts_count: int = 1


class GenerateSoundsRequest(BaseModel):
    """Schema for sound effects generation request"""
    # Optional sound-specific settings
    prompt_influence: float = Field(default=0.3, ge=0.0, le=1.0)
    default_duration_seconds: float = Field(default=3.0, ge=1.0, le=10.0)


class GenerateSoundsResponse(BaseModel):
    """Schema for sound effects generation response"""
    episode_id: UUID
    status: str
    sounds_count: int = 0
    sounds: List[dict] = []


class GenerateMusicRequest(BaseModel):
    """Schema for music generation request"""
    # Optional music-specific settings
    force_instrumental: bool = True


class GenerateMusicResponse(BaseModel):
    """Schema for music generation response"""
    episode_id: UUID
    status: str
    music_url: Optional[str] = None
    duration_seconds: Optional[float] = None


class MergeAudioRequest(BaseModel):
    """Schema for audio merge request"""
    # Volume settings
    voice_volume: float = Field(default=1.0, ge=0.0, le=2.0)
    sounds_volume: float = Field(default=0.8, ge=0.0, le=2.0)
    music_volume: float = Field(default=0.3, ge=0.0, le=1.0)


class MergeAudioResponse(BaseModel):
    """Schema for audio merge response"""
    episode_id: UUID
    status: str
    final_audio_url: Optional[str] = None
    duration_seconds: Optional[float] = None


class GenerateCoverRequest(BaseModel):
    """Schema for cover generation request"""
    variants_count: int = Field(default=1, ge=1, le=4)
    reference_image_url: Optional[str] = None
    custom_prompt: Optional[str] = None


class GenerateCoverResponse(BaseModel):
    """Schema for cover generation response"""
    episode_id: UUID
    status: str
    cover_url: Optional[str] = None
    variants: List[dict] = []


class SelectCoverRequest(BaseModel):
    """Schema for selecting a cover variant"""
    variant_index: int = Field(ge=0, le=3)


class GenerateFullRequest(BaseModel):
    """Schema for full pipeline generation request"""
    # Include optional parameters for each step
    generate_cover: bool = True
    cover_variants_count: int = Field(default=1, ge=1, le=4)
    cover_reference_image_url: Optional[str] = None
    
    # Volume settings for merge
    voice_volume: float = Field(default=1.0, ge=0.0, le=2.0)
    sounds_volume: float = Field(default=0.8, ge=0.0, le=2.0)
    music_volume: float = Field(default=0.3, ge=0.0, le=1.0)


class GenerateFullResponse(BaseModel):
    """Schema for full pipeline generation response"""
    episode_id: UUID
    status: str
    
    # Status of each step
    script_status: str = "pending"
    voiceover_status: str = "pending"
    sounds_status: str = "pending"  # or "skipped"
    music_status: str = "pending"   # or "skipped"
    merge_status: str = "pending"
    cover_status: str = "pending"   # or "skipped"
    
    # Results
    final_audio_url: Optional[str] = None
    final_audio_duration_seconds: Optional[float] = None
    cover_url: Optional[str] = None


class GenerationStatusResponse(BaseModel):
    """Schema for generation status response"""
    episode_id: UUID
    status: str
    
    # Detailed progress
    current_step: str
    steps_completed: List[str]
    steps_remaining: List[str]
    
    # Error info if any
    error_message: Optional[str] = None
    
    # Results so far
    script_ready: bool = False
    voiceover_ready: bool = False
    sounds_ready: bool = False
    music_ready: bool = False
    audio_ready: bool = False
    cover_ready: bool = False
