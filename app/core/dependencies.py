"""
HeinerCast FastAPI Dependencies
"""
from typing import Optional
from uuid import UUID

from fastapi import Depends, Header, Cookie, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.security import verify_access_token, verify_api_key, hash_api_key
from app.core.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    NotFoundError
)
from app.models.user import User
from app.models.api_key import APIKey

# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    access_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current authenticated user.
    Supports:
    - Bearer token in Authorization header
    - API key in X-API-Key header
    - Access token in cookie
    """
    user_id = None
    
    # Try Bearer token first
    if credentials and credentials.credentials:
        try:
            payload = verify_access_token(credentials.credentials)
            user_id = UUID(payload["sub"])
        except (InvalidTokenError, ValueError):
            pass
    
    # Try cookie token
    if not user_id and access_token:
        try:
            payload = verify_access_token(access_token)
            user_id = UUID(payload["sub"])
        except (InvalidTokenError, ValueError):
            pass
    
    # Try API key
    if not user_id and x_api_key:
        key_hash = hash_api_key(x_api_key)
        result = await db.execute(
            select(APIKey).where(
                APIKey.key_hash == key_hash,
                APIKey.is_active == True
            )
        )
        api_key = result.scalar_one_or_none()
        
        if api_key:
            # Check expiration
            from datetime import datetime
            if api_key.expires_at and api_key.expires_at < datetime.utcnow():
                raise AuthenticationError("API key has expired")
            
            # Update last used timestamp
            api_key.last_used_at = datetime.utcnow()
            user_id = api_key.user_id
    
    if not user_id:
        raise AuthenticationError("Not authenticated")
    
    # Get user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise NotFoundError("User")
    
    if not user.is_active:
        raise AuthenticationError("User account is deactivated")
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    access_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get the current user if authenticated, otherwise return None"""
    try:
        return await get_current_user(credentials, x_api_key, access_token, db)
    except AuthenticationError:
        return None


class UserLanguage:
    """Dependency for getting user's preferred language"""
    
    def __init__(
        self,
        accept_language: Optional[str] = Header(None),
        user: Optional[User] = None
    ):
        self.language = "en"  # Default
        
        # Priority: User setting > Accept-Language header > Default
        if user and user.language:
            self.language = user.language
        elif accept_language:
            # Parse Accept-Language header
            for lang in ["ru", "en", "de"]:
                if lang in accept_language.lower():
                    self.language = lang
                    break


async def get_user_language(
    accept_language: Optional[str] = Header(None),
    user: Optional[User] = Depends(get_current_user_optional)
) -> str:
    """Get user's preferred language"""
    if user and user.language:
        return user.language
    
    if accept_language:
        for lang in ["ru", "en", "de"]:
            if lang in accept_language.lower():
                return lang
    
    return "en"


# Project ownership check
async def verify_project_ownership(
    project_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify that the current user owns the project"""
    from app.models.project import Project
    
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == user.id
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", str(project_id))
    
    return project


# Episode ownership check
async def verify_episode_ownership(
    episode_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify that the current user owns the episode (via project)"""
    from app.models.episode import Episode
    from app.models.project import Project
    
    result = await db.execute(
        select(Episode)
        .join(Project)
        .where(
            Episode.id == episode_id,
            Project.user_id == user.id
        )
    )
    episode = result.scalar_one_or_none()
    
    if not episode:
        raise NotFoundError("Episode", str(episode_id))
    
    return episode


# Voice ownership check
async def verify_voice_ownership(
    voice_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify that the current user owns the voice"""
    from app.models.voice import Voice
    
    result = await db.execute(
        select(Voice).where(
            Voice.id == voice_id,
            Voice.user_id == user.id
        )
    )
    voice = result.scalar_one_or_none()
    
    if not voice:
        raise NotFoundError("Voice", str(voice_id))
    
    return voice
