from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserDTO(BaseModel):
    """Data Transfer Object for User entity - used for service layer communication"""

    id: str
    firebase_uid: str
    email: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    profile_image_url: Optional[str] = None
    status: str = Field(default="ACTIVE")
    email_verified: bool = Field(default=False)
    phone_verified: bool = Field(default=False)
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CreateUserDTO(BaseModel):
    """DTO for creating a new user"""

    firebase_uid: str
    email: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    profile_image_url: Optional[str] = None
    email_verified: bool = Field(default=False)


class UserRegistrationDTO(BaseModel):
    """DTO for user registration data"""

    first_name: str
    last_name: str
    phone_number: str
