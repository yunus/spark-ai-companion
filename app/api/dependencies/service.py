from typing import Annotated
from fastapi import Depends

from app.infrastructure.database.repositories.user_repository import UserRepository
from app.domain.services.user_service import UserService
from app.api.dependencies.database import get_user_repository


async def get_user_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    """Dependency to get user service."""
    return UserService(user_repository)
