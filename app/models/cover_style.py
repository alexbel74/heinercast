from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.database import Base


class CoverStyle(Base):
    __tablename__ = "cover_styles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    emoji = Column(String(10), default='🎨')
    instructions = Column(Text, nullable=False)
    mood = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
