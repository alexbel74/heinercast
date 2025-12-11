"""
Episode Model - Individual episodes within a project
"""
import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from enum import Enum

from sqlalchemy import String, Text, Boolean, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project


class EpisodeStatus(str, Enum):
    """Episode status enumeration"""
    DRAFT = "draft"
    SCRIPT_GENERATING = "script_generating"
    SCRIPT_DONE = "script_done"
    VOICEOVER_GENERATING = "voiceover_generating"
    VOICEOVER_DONE = "voiceover_done"
    SOUNDS_GENERATING = "sounds_generating"
    SOUNDS_DONE = "sounds_done"
    MUSIC_GENERATING = "music_generating"
    MUSIC_DONE = "music_done"
    MERGING = "merging"
    AUDIO_DONE = "audio_done"
    COVER_GENERATING = "cover_generating"
    DONE = "done"
    ERROR = "error"


class Episode(Base):
    """Episode model - individual episode in a project"""
    
    __tablename__ = "episodes"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Foreign key
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True
    )
    
    # Episode information
    episode_number: Mapped[int] = mapped_column(Integer)  # 1, 2, 3...
    title: Mapped[str] = mapped_column(String(200))  # Episode title
    title_auto_generated: Mapped[bool] = mapped_column(Boolean, default=True)
    show_episode_number: Mapped[bool] = mapped_column(Boolean, default=True)  # Show "Part N" in title
    
    # Description and duration
    description: Mapped[str] = mapped_column(Text)  # Brief description
    target_duration_minutes: Mapped[int] = mapped_column(Integer, default=10)
    
    # Script
    script_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Format: {"story_title": "", "genre_tone": "", "approx_duration_minutes": 0, 
    #          "lines": [{"speaker": "", "voice_id": "", "text": "", "sound_effect": null}]}
    script_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Text version for display
    
    # Summary for continuation context
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Generation options (can override project defaults)
    include_sound_effects: Mapped[bool] = mapped_column(Boolean, default=False)
    include_background_music: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Voice audio results
    voice_audio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    voice_audio_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    voice_timestamps_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Sound effects
    sounds_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Format: [{"prompt": "", "url": "", "start_time": 0, "duration": 0}]
    
    # Background music
    music_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    music_composition_plan: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Final audio
    final_audio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    final_audio_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Cover
    cover_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cover_reference_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cover_variants_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Format: [{"url": "", "selected": true/false}]
    
    # Status
    status: Mapped[str] = mapped_column(
        String(30),
        default=EpisodeStatus.DRAFT.value
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
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
    project: Mapped["Project"] = relationship("Project", back_populates="episodes")
    
    def __repr__(self) -> str:
        return f"<Episode #{self.episode_number}: {self.title}>"
    
    @property
    def display_title(self) -> str:
        """Get display title with optional episode number"""
        if self.show_episode_number:
            return f"Часть {self.episode_number}: {self.title}"
        return self.title
