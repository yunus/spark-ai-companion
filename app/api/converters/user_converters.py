from app.domain.dto.user import UserDTO
from app.domain.schemas.response.auth import (
    RegistrationResponse,
    LoginResponse,
    RegistrationData,
    LoginData,
)


def user_dto_to_registration_response(
    user_dto: UserDTO, message: str = "Registration successful", status_code: int = 201
) -> RegistrationResponse:
    """Convert UserDTO to RegistrationResponse schema."""
    data = RegistrationData(
        firebase_uid=user_dto.firebase_uid,
        email=user_dto.email,
        first_name=user_dto.first_name,
        last_name=user_dto.last_name,
        profile_image_url=user_dto.profile_image_url,
    )

    return RegistrationResponse(message=message, status_code=status_code, data=data)


def user_dto_to_login_response(
    user_dto: UserDTO, message: str = "Login successful", status_code: int = 200
) -> LoginResponse:
    """Convert UserDTO to LoginResponse schema."""
    data = LoginData(
        id=user_dto.id,
        firebase_uid=user_dto.firebase_uid,
        email=user_dto.email,
        first_name=user_dto.first_name,
        last_name=user_dto.last_name,
        phone_number=user_dto.phone_number,
        profile_image_url=user_dto.profile_image_url,
        status=user_dto.status,
        email_verified=user_dto.email_verified,
        phone_verified=user_dto.phone_verified,
        last_login_at=(
            user_dto.last_login_at.isoformat() if user_dto.last_login_at else None
        ),
        created_at=user_dto.created_at.isoformat() if user_dto.created_at else "",
        updated_at=user_dto.updated_at.isoformat() if user_dto.updated_at else "",
    )

    return LoginResponse(message=message, status_code=status_code, data=data)
