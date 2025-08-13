from typing import Optional

from pydantic import Field

from app.domain.schemas.response.base import StandardResponse
from app.domain.schemas.base import AppBaseModel


class RegistrationData(AppBaseModel):
    """Data portion of registration response"""

    firebase_uid: str = Field(..., description="Firebase UID of the registered user")
    email: Optional[str] = Field(None, description="User's email address")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    profile_image_url: Optional[str] = Field(
        None, description="URL to user's profile image"
    )


class LoginData(AppBaseModel):
    """Data portion of login response"""

    id: str = Field(..., description="Unique user ID")
    firebase_uid: str = Field(..., description="Firebase UID of the user")
    email: str = Field(..., description="User's email address")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    phone_number: Optional[str] = Field(
        None,
        description="User's phone number in international format",
        examples=["+1234567890"],
    )
    profile_image_url: Optional[str] = Field(
        None, description="URL to user's profile image"
    )
    status: str = Field(..., description="User account status (ACTIVE, INACTIVE, etc.)")
    email_verified: bool = Field(
        ..., description="Whether the user's email is verified"
    )
    phone_verified: bool = Field(
        ..., description="Whether the user's phone number is verified"
    )
    last_login_at: Optional[str] = Field(
        None, description="ISO format timestamp of user's last login"
    )
    created_at: str = Field(
        ..., description="ISO format timestamp when user was created"
    )
    updated_at: str = Field(
        ..., description="ISO format timestamp when user was last updated"
    )


# Concrete response types
class RegistrationResponse(StandardResponse[RegistrationData]):
    """Registration API response"""

    pass


class LoginResponse(StandardResponse[LoginData]):
    """Login API response"""

    pass


__all__ = ["RegistrationResponse", "LoginResponse", "RegistrationData", "LoginData"]
