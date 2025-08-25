import enum

from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class UserStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    firebase_uid = Column(String, unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    email_verified = Column(Boolean, default=False)
    phone_number = Column(String(20), nullable=True)
    phone_verified = Column(Boolean, default=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    profile_image_url = Column(String(500), nullable=True)
    status = Column(Enum(UserStatus), default=UserStatus.PENDING_VERIFICATION)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subscription = relationship(
        "UserSubscription", back_populates="user", uselist=False
    )
    sessions = relationship("UserSession", back_populates="user")


__all__ = [User, UserStatus]
