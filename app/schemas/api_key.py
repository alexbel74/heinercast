"""
API Key Pydantic Schemas
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class APIKeyBase(BaseModel):
    """Base API key schema"""
    name: str = Field(max_length=100)
    expires_in_days: Optional[int] = Field(default=365, ge=1, le=3650)


class APIKeyCreate(APIKeyBase):
    """Schema for creating an API key"""
    pass


class APIKeyResponse(BaseModel):
    """Schema for API key response (without the actual key)"""
    id: UUID
    name: str
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class APIKeyCreateResponse(APIKeyResponse):
    """Schema for API key creation response (includes the actual key - shown once)"""
    api_key: str  # The actual key, shown only on creation


class APIKeyListResponse(BaseModel):
    """Schema for API key list response"""
    items: list[APIKeyResponse]
    total: int
