"""
Project Model - Series/Project container
"""
import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.project_character import ProjectCharacter
    from app.models.episode import Episode


class Project(Base):
    """Project model - represents a series/audiobook project"""
    
    __tablename__ = "projects"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Foreign key
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )
    
    # Project information
    title: Mapped[str] = mapped_column(String(200))  # "Город без работы"
    description: Mapped[str] = mapped_column(Text)  # Brief description
    genre_tone: Mapped[str] = mapped_column(String(200))  # "Антиутопия, социальная драма"
    
    # Musical atmosphere for background music generation (future)
    musical_atmosphere: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )  # "Atmospheric ambient with industrial sounds"
    
    # Default generation options (inherited by episodes)
    include_sound_effects: Mapped[bool] = mapped_column(Boolean, default=False)
    include_background_music: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Project cover
    cover_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cover_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
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
    user: Mapped["User"] = relationship("User", back_populates="projects")
    characters: Mapped[List["ProjectCharacter"]] = relationship(
        "ProjectCharacter",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectCharacter.sort_order"
    )
    episodes: Mapped[List["Episode"]] = relationship(
        "Episode",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Episode.episode_number"
    )
    
    def __repr__(self) -> str:
        return f"<Project {self.title}>"
