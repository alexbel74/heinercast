"""
Authentication API Endpoints
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Response, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, TokenResponse, TokenRefresh, PasswordChange
)
from app.core.security import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    verify_refresh_token
)
from app.core.exceptions import (
    InvalidCredentialsError, AlreadyExistsError, AuthenticationError
)
from app.core.dependencies import get_current_user
from app.config import get_settings

settings = get_settings()
router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    user_data: UserCreate,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise AlreadyExistsError("User", "email")
    
    # Check if username already exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise AlreadyExistsError("User", "username")
    
    # Create user
    user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        language=user_data.language
    )
    
    db.add(user)
    await db.flush()
    
    # Generate tokens
    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id)
    
    # Set cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=settings.access_token_expire_hours * 3600
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_hours * 3600
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Login and get tokens"""
    # Get login identifier (email or username)
    login_id = credentials.email or credentials.username
    if not login_id:
        raise InvalidCredentialsError()
    
    # Find user by username or email
    result = await db.execute(
        select(User).where(
            (User.username == login_id) | 
            (User.email == login_id)
        )
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise InvalidCredentialsError()
    
    if not user.is_active:
        raise AuthenticationError("Account is deactivated")
    
    # Generate tokens
    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id)
    
    # Set cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=settings.access_token_expire_hours * 3600
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_hours * 3600
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token"""
    payload = verify_refresh_token(token_data.refresh_token)
    user_id = payload["sub"]
    
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise AuthenticationError("Invalid refresh token")
    
    # Generate new tokens
    access_token = create_access_token(user.id, user.email)
    new_refresh_token = create_refresh_token(user.id)
    
    # Set cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=settings.access_token_expire_hours * 3600
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_hours * 3600
    )


@router.post("/logout")
async def logout(response: Response):
    """Logout and clear cookies"""
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
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


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise InvalidCredentialsError()
    
    # Update password
    current_user.password_hash = hash_password(password_data.new_password)
    current_user.updated_at = datetime.utcnow()
    
    return {"message": "Password changed successfully"}
