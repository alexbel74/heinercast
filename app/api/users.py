"""
Users API Endpoints
"""
from datetime import datetime, timedelta
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.api_key import APIKey
from app.schemas.user import (
    UserUpdate, UserResponse, UserSettingsLLM, UserSettingsElevenLabs,
    UserSettingsKieAI, UserSettingsStorage, UserSettingsPrompts, UserSettingsResponse
)
from app.schemas.api_key import (
    APIKeyCreate, APIKeyResponse, APIKeyCreateResponse, APIKeyListResponse
)
from app.core.security import encrypt_api_key, generate_api_key
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError, AlreadyExistsError
from app.config import LLM_PROVIDERS

router = APIRouter()


@router.get("/settings", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user: User = Depends(get_current_user)
):
    """Get all user settings"""
    return UserSettingsResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        language=current_user.language,
        llm_provider=current_user.llm_provider,
        llm_model=current_user.llm_model,
        has_llm_api_key=bool(current_user.llm_api_key),
        has_elevenlabs_api_key=bool(current_user.elevenlabs_api_key),
        has_kieai_api_key=bool(current_user.kieai_api_key),
        storage_type=current_user.storage_type,
        has_google_drive_credentials=bool(current_user.google_drive_credentials),
        ai_writer_prompt=current_user.ai_writer_prompt,
        cover_prompt_template=current_user.cover_prompt_template,
        telegram_chat_id=current_user.telegram_chat_id
    )


@router.put("/settings", response_model=UserResponse)
async def update_user_settings(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile settings"""
    # Check email uniqueness if changing
    if update_data.email and update_data.email != current_user.email:
        result = await db.execute(select(User).where(User.email == update_data.email))
        if result.scalar_one_or_none():
            raise AlreadyExistsError("User", "email")
        current_user.email = update_data.email
    
    # Check username uniqueness if changing
    if update_data.username and update_data.username != current_user.username:
        result = await db.execute(select(User).where(User.username == update_data.username))
        if result.scalar_one_or_none():
            raise AlreadyExistsError("User", "username")
        current_user.username = update_data.username
    
    if update_data.language:
        current_user.language = update_data.language
    
    current_user.updated_at = datetime.utcnow()
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        language=current_user.language,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        has_llm_api_key=bool(current_user.llm_api_key),
        has_elevenlabs_api_key=bool(current_user.elevenlabs_api_key),
        has_kieai_api_key=bool(current_user.kieai_api_key),
        llm_provider=current_user.llm_provider,
        llm_model=current_user.llm_model,
        storage_type=current_user.storage_type
    )


@router.put("/settings/llm")
async def update_llm_settings(
    settings_data: UserSettingsLLM,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update LLM provider settings"""
    current_user.llm_provider = settings_data.llm_provider
    
    if settings_data.llm_api_key:
        current_user.llm_api_key = encrypt_api_key(settings_data.llm_api_key)
    
    if settings_data.llm_model:
        # Validate model is available for the provider
        available_models = LLM_PROVIDERS.get(settings_data.llm_provider, {}).get("models", [])
        if settings_data.llm_model in available_models or not available_models:
            current_user.llm_model = settings_data.llm_model
    
    current_user.updated_at = datetime.utcnow()
    
    return {
        "message": "LLM settings updated",
        "provider": current_user.llm_provider,
        "model": current_user.llm_model,
        "has_api_key": bool(current_user.llm_api_key)
    }


@router.put("/settings/elevenlabs")
async def update_elevenlabs_settings(
    settings_data: UserSettingsElevenLabs,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update ElevenLabs API key"""
    current_user.elevenlabs_api_key = encrypt_api_key(settings_data.elevenlabs_api_key)
    current_user.updated_at = datetime.utcnow()
    
    return {"message": "ElevenLabs API key updated"}


@router.put("/settings/kieai")
async def update_kieai_settings(
    settings_data: UserSettingsKieAI,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update kie.ai API key"""
    current_user.kieai_api_key = encrypt_api_key(settings_data.kieai_api_key)
    current_user.updated_at = datetime.utcnow()
    
    return {"message": "kie.ai API key updated"}


@router.put("/settings/storage")
async def update_storage_settings(
    settings_data: UserSettingsStorage,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update storage settings"""
    current_user.storage_type = settings_data.storage_type
    
    if settings_data.google_drive_credentials:
        current_user.google_drive_credentials = settings_data.google_drive_credentials
    
    current_user.updated_at = datetime.utcnow()
    
    return {
        "message": "Storage settings updated",
        "storage_type": current_user.storage_type
    }


@router.put("/settings/prompts")
async def update_prompts_settings(
    settings_data: UserSettingsPrompts,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update AI prompts"""
    if settings_data.ai_writer_prompt is not None:
        current_user.ai_writer_prompt = settings_data.ai_writer_prompt
    
    if settings_data.cover_prompt_template is not None:
        current_user.cover_prompt_template = settings_data.cover_prompt_template
    
    current_user.updated_at = datetime.utcnow()
    
    return {"message": "Prompts updated"}


@router.post("/settings/prompts/reset")
async def reset_prompts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reset prompts to defaults"""
    from app.config import DEFAULT_AI_WRITER_PROMPT, DEFAULT_COVER_PROMPT_TEMPLATE
    
    current_user.ai_writer_prompt = DEFAULT_AI_WRITER_PROMPT
    current_user.cover_prompt_template = DEFAULT_COVER_PROMPT_TEMPLATE
    current_user.updated_at = datetime.utcnow()
    
    return {"message": "Prompts reset to defaults"}


# API Keys management
@router.get("/api-keys", response_model=APIKeyListResponse)
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all API keys for the current user"""
    result = await db.execute(
        select(APIKey)
        .where(APIKey.user_id == current_user.id)
        .order_by(APIKey.created_at.desc())
    )
    keys = result.scalars().all()
    
    return APIKeyListResponse(
        items=[APIKeyResponse.model_validate(key) for key in keys],
        total=len(keys)
    )


@router.post("/api-keys", response_model=APIKeyCreateResponse, status_code=201)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new API key"""
    # Generate key
    plain_key, hashed_key = generate_api_key()
    
    # Calculate expiration
    expires_at = None
    if key_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)
    
    # Create API key record
    api_key = APIKey(
        user_id=current_user.id,
        key_hash=hashed_key,
        name=key_data.name,
        expires_at=expires_at
    )
    
    db.add(api_key)
    await db.flush()
    
    return APIKeyCreateResponse(
        id=api_key.id,
        name=api_key.name,
        expires_at=api_key.expires_at,
        last_used_at=api_key.last_used_at,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        api_key=plain_key  # Only shown once!
    )


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Revoke an API key"""
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == current_user.id
        )
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise NotFoundError("API key", str(key_id))
    
    api_key.is_active = False
    
    return {"message": "API key revoked"}


@router.get("/llm-models")
async def get_llm_models(
    provider: str = "openrouter"
):
    """Get available LLM models for a provider"""
    models = LLM_PROVIDERS.get(provider, {}).get("models", [])
    return {
        "provider": provider,
        "models": models
    }
