import enum

from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class SessionStatus(enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    firebase_token = Column(Text, nullable=False)
    refresh_token = Column(String(500), nullable=True)
    device_info = Column(JSON, nullable=True)  # Browser, OS, IP
    status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE)
    expires_at = Column(DateTime, nullable=False)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="sessions")


__all__ = [UserSession, SessionStatus]
