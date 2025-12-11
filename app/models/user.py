"""
User Model
"""
import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.config import DEFAULT_AI_WRITER_PROMPT, DEFAULT_COVER_PROMPT_TEMPLATE

if TYPE_CHECKING:
    from app.models.voice import Voice
    from app.models.project import Project
    from app.models.api_key import APIKey


class User(Base):
    """User model for authentication and settings"""
    
    __tablename__ = "users"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Authentication
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    
    # LLM Settings
    llm_provider: Mapped[str] = mapped_column(
        String(50),
        default="openrouter"
    )  # "openrouter" | "polza" | "openai"
    llm_api_key: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )  # Encrypted
    llm_model: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    
    # ElevenLabs Settings
    elevenlabs_api_key: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )  # Encrypted
    
    # kie.ai Settings
    kieai_api_key: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )  # Encrypted
    
    # Storage Settings
    storage_type: Mapped[str] = mapped_column(
        String(20),
        default="local"
    )  # "local" | "google_drive"
    google_drive_credentials: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True
    )
    
    # Telegram Settings (Phase 2)
    telegram_chat_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    
    # AI Prompts
    ai_writer_prompt: Mapped[str] = mapped_column(
        Text,
        default=DEFAULT_AI_WRITER_PROMPT
    )
    cover_prompt_template: Mapped[str] = mapped_column(
        Text,
        default=DEFAULT_COVER_PROMPT_TEMPLATE
    )
    
    # UI Settings
    language: Mapped[str] = mapped_column(
        String(5),
        default="en"
    )  # "ru" | "en" | "de"
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    voices: Mapped[List["Voice"]] = relationship(
        "Voice",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    projects: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    api_keys: Mapped[List["APIKey"]] = relationship(
        "APIKey",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User {self.username}>"
