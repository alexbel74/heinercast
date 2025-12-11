"""
ProjectCharacter Model - Characters assigned to a project
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.voice import Voice


class ProjectCharacter(Base):
    """ProjectCharacter model - links characters to projects with voices"""
    
    __tablename__ = "project_characters"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Foreign keys
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True
    )
    voice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("voices.id", ondelete="RESTRICT"),
        index=True
    )
    
    # Character information
    role: Mapped[str] = mapped_column(String(100))  # Role in project (e.g., "Main character")
    character_name: Mapped[str] = mapped_column(String(100))  # Character name (e.g., "André Heiner")
    
    # Display order
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="characters")
    voice: Mapped["Voice"] = relationship("Voice", back_populates="characters")
    
    def __repr__(self) -> str:
        return f"<ProjectCharacter {self.character_name} ({self.role})>"
