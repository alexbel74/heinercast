"""
Project Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCharacterBase(BaseModel):
    """Base project character schema"""
    voice_id: UUID
    role: str = Field(max_length=100)
    character_name: str = Field(max_length=100)
    sort_order: int = 0


class ProjectCharacterCreate(ProjectCharacterBase):
    """Schema for creating a project character"""
    pass


class ProjectCharacterUpdate(BaseModel):
    """Schema for updating a project character"""
    voice_id: Optional[UUID] = None
    role: Optional[str] = Field(None, max_length=100)
    character_name: Optional[str] = Field(None, max_length=100)
    sort_order: Optional[int] = None


class ProjectCharacterResponse(ProjectCharacterBase):
    """Schema for project character response"""
    id: UUID
    project_id: UUID
    created_at: datetime
    
    # Nested voice info
    voice_name: Optional[str] = None
    elevenlabs_name: Optional[str] = None
    elevenlabs_voice_id: Optional[str] = None

    model_config = {"from_attributes": True}


class ProjectBase(BaseModel):
    """Base project schema"""
    title: str = Field(max_length=200)
    description: str = Field(max_length=5000)
    genre_tone: str = Field(max_length=200)
    musical_atmosphere: Optional[str] = Field(None, max_length=500)
    include_sound_effects: bool = False
    include_background_music: bool = False


class ProjectCreate(ProjectBase):
    """Schema for creating a project"""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project"""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    genre_tone: Optional[str] = Field(None, max_length=200)
    musical_atmosphere: Optional[str] = Field(None, max_length=500)
    include_sound_effects: Optional[bool] = None
    include_background_music: Optional[bool] = None


class ProjectResponse(ProjectBase):
    """Schema for project response"""
    id: UUID
    user_id: UUID
    cover_url: Optional[str] = None
    cover_prompt: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Counts
    episodes_count: int = 0
    characters_count: int = 0

    model_config = {"from_attributes": True}


class ProjectDetailResponse(ProjectResponse):
    """Schema for detailed project response with characters and episodes"""
    characters: List[ProjectCharacterResponse] = []
    
    # Episode summary
    latest_episode_number: int = 0
    latest_episode_status: Optional[str] = None

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    """Schema for project list response"""
    items: List[ProjectResponse]
    total: int
    page: int
    page_size: int
