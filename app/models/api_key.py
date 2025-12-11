"""
APIKey Model - User API keys for programmatic access
"""
import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class APIKey(Base):
    """API Key model for programmatic access"""
    
    __tablename__ = "api_keys"
    
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
    
    # Key information
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)  # SHA256 hash
    name: Mapped[str] = mapped_column(String(100))  # User-defined name
    
    # Expiration and usage
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="api_keys")
    
    def __repr__(self) -> str:
        return f"<APIKey {self.name}>"
