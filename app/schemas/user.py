"""
User Pydantic Schemas
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    language: str = Field(default="en", pattern=r"^(ru|en|de)$")


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(min_length=8, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login - accepts email or username"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: str
    
    @field_validator('username', mode='before')
    @classmethod
    def check_login_field(cls, v, info):
        # Allow login with email or username
        return v


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    language: Optional[str] = Field(None, pattern=r"^(ru|en|de)$")


class UserResponse(BaseModel):
    """Schema for user response"""
    id: UUID
    email: str
    username: str
    language: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Settings presence indicators (not actual values for security)
    has_llm_api_key: bool = False
    has_elevenlabs_api_key: bool = False
    has_kieai_api_key: bool = False
    llm_provider: str = "openrouter"
    llm_model: Optional[str] = None
    storage_type: str = "local"

    model_config = {"from_attributes": True}


class UserSettingsLLM(BaseModel):
    """Schema for LLM settings"""
    llm_provider: str = Field(pattern=r"^(openrouter|polza|openai)$")
    llm_api_key: Optional[str] = None  # Optional - can use default
    llm_model: Optional[str] = None


class UserSettingsElevenLabs(BaseModel):
    """Schema for ElevenLabs settings"""
    elevenlabs_api_key: str


class UserSettingsKieAI(BaseModel):
    """Schema for kie.ai settings"""
    kieai_api_key: str


class UserSettingsStorage(BaseModel):
    """Schema for storage settings"""
    storage_type: str = Field(pattern=r"^(local|google_drive)$")
    google_drive_credentials: Optional[dict] = None


class UserSettingsPrompts(BaseModel):
    """Schema for AI prompts settings"""
    ai_writer_prompt: Optional[str] = None
    cover_prompt_template: Optional[str] = None


class UserSettingsResponse(BaseModel):
    """Schema for full user settings response"""
    id: UUID
    email: str
    username: str
    language: str
    
    # LLM settings
    llm_provider: str
    llm_model: Optional[str]
    has_llm_api_key: bool
    
    # API keys (presence only)
    has_elevenlabs_api_key: bool
    has_kieai_api_key: bool
    
    # Storage
    storage_type: str
    has_google_drive_credentials: bool
    
    # Prompts
    ai_writer_prompt: str
    cover_prompt_template: str
    
    # Telegram
    telegram_chat_id: Optional[str]

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Schema for authentication token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenRefresh(BaseModel):
    """Schema for token refresh request"""
    refresh_token: str


class PasswordChange(BaseModel):
    """Schema for password change"""
    current_password: str
    new_password: str = Field(min_length=8, max_length=100)
