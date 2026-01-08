from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database import Base

class ProjectTemplate(Base):
    __tablename__ = "project_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    genre_tone = Column(String(200))
    musical_atmosphere = Column(String(500))
    include_sound_effects = Column(Boolean, default=True)
    include_background_music = Column(Boolean, default=True)
    target_duration_minutes = Column(Integer, default=10)
    cover_style = Column(String(50))
    characters_json = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
