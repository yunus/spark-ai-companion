from typing import Annotated
from fastapi import APIRouter, Depends

from app.domain.schemas.request.auth import RegistrationRequest
from app.domain.schemas.response.auth import RegistrationResponse, LoginResponse
from app.domain.schemas.response.exception import StandardErrorResponse
from app.domain.dto.user import UserRegistrationDTO
from app.api.dependencies import get_user_service, verify_custom_header_token
from app.domain.dto.auth import AuthenticatedUser
from app.domain.services.user_service import UserService
from app.api.converters.user_converters import (
    user_dto_to_registration_response,
    user_dto_to_login_response,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    path="/register",
    response_model=RegistrationResponse,
    responses={
        403: {"model": StandardErrorResponse, "description": "Authentication required"},
        422: {"model": StandardErrorResponse, "description": "validation errors"},
    },
)
async def register(
    body: RegistrationRequest,
    user: Annotated[AuthenticatedUser, Depends(verify_custom_header_token)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> RegistrationResponse:
    """Register a new user."""

    # Convert request schema to DTO
    registration_dto = UserRegistrationDTO(
        first_name=body.first_name,
        last_name=body.last_name,
        phone_number=body.phone_number,
    )

    # Call service with DTO
    user_dto = await user_service.register_user(registration_dto, user)

    # Convert DTO to response schema using converter
    return user_dto_to_registration_response(user_dto)


@router.post(
    path="/login",
    response_model=LoginResponse,
    responses={
        404: {"model": StandardErrorResponse, "description": "User not found"},
        403: {"model": StandardErrorResponse, "description": "Authentication required"},
    },
)
async def login(
    user: Annotated[AuthenticatedUser, Depends(verify_custom_header_token)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> LoginResponse:
    """
    Login endpoint that verifies Firebase token and returns user details from database.
    The token verification is handled by the verify_custom_header_token dependency.
    """

    # Call service to get user DTO
    user_dto = await user_service.login_user(user)

    # Convert DTO to response schema using converter
    return user_dto_to_login_response(user_dto)


__all__ = ["router"]
