from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.infrastructure.external.firebase_client import FirebaseClient
from app.domain.dto.auth import AuthenticatedUser
from app.domain.dto.user import UserDTO
from app.domain.services.user_service import UserService
from app.api.dependencies.service import get_user_service

security = HTTPBearer()


async def get_firebase_client(request: Request) -> FirebaseClient:
    """Dependency to get Firebase client from app state."""
    return request.app.state.firebase_client


async def verify_custom_header_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    firebase_client: Annotated[FirebaseClient, Depends(get_firebase_client)],
) -> AuthenticatedUser:
    id_token = credentials.credentials
    decoded_token = await firebase_client.verify_token(id_token)
    return AuthenticatedUser.from_token(decoded_token)


async def get_current_user(
    user: Annotated[AuthenticatedUser, Depends(verify_custom_header_token)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserDTO:
    return await user_service.get_user_by_firebase_uid(firebase_uid=user.uid)
