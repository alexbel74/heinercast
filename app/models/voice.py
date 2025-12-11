"""
Voice Model - User's voice library
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


class Voice(Base):
    """Voice model for user's voice library"""
    
    __tablename__ = "voices"
    
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
    
    # Voice information
    name: Mapped[str] = mapped_column(String(100))  # Name in user's library (e.g., "Narrator")
    elevenlabs_name: Mapped[str] = mapped_column(String(100))  # Name in ElevenLabs (e.g., "Captain Commercial")
    elevenlabs_voice_id: Mapped[str] = mapped_column(String(50))  # ElevenLabs voice ID
    
    # Optional description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Favorite status for quick access
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    
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
    user: Mapped["User"] = relationship("User", back_populates="voices")
    characters: Mapped[List["ProjectCharacter"]] = relationship(
        "ProjectCharacter",
        back_populates="voice"
    )
    
    def __repr__(self) -> str:
        return f"<Voice {self.name} ({self.elevenlabs_name})>"
