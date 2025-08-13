from typing import Optional
from app.domain.dto.auth import AuthenticatedUser
from app.domain.dto.user import UserDTO, CreateUserDTO, UserRegistrationDTO
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.core.exceptions import UserAlreadyExistsError, UserNotFoundError


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def register_user(
        self,
        registration_data: UserRegistrationDTO,
        authenticated_user: AuthenticatedUser,
    ) -> UserDTO:
        """Register a new user with the provided data."""

        # Check if user already exists
        if await self.user_repository.user_exists_by_firebase_uid(
            authenticated_user.uid
        ):
            raise UserAlreadyExistsError(
                f"User with Firebase UID '{authenticated_user.uid}' already exists"
            )

        # Email is required in your model, so we need to ensure it exists
        if not authenticated_user.email:
            raise ValueError("Email is required for registration")

        # Create DTO for user creation
        create_user_dto = CreateUserDTO(
            firebase_uid=authenticated_user.uid,
            email=authenticated_user.email,
            first_name=registration_data.first_name,
            last_name=registration_data.last_name,
            phone_number=registration_data.phone_number,
            profile_image_url=authenticated_user.picture,
            email_verified=authenticated_user.email_verified or False,
        )

        # Create user in database
        user = await self.user_repository.create_user(create_user_dto)

        # Convert to UserDTO and return
        return self._convert_user_entity_to_dto(user)

    async def get_user_by_firebase_uid(self, firebase_uid: str) -> UserDTO:
        """Get user details by Firebase UID."""
        user = await self.user_repository.get_by_firebase_uid(firebase_uid)
        if not user:
            raise UserNotFoundError(
                f"User with Firebase UID '{firebase_uid}' not found"
            )
        return self._convert_user_entity_to_dto(user)

    async def get_user_by_email(self, email: str) -> Optional[UserDTO]:
        """Get user details by email - alternative login method."""
        user = await self.user_repository.get_by_email(email)
        if not user:
            raise UserNotFoundError(
                f"User with email '{email}' not registered"
            )
        return self._convert_user_entity_to_dto(user)

    async def get_user_by_id(self, user_id: str) -> Optional[UserDTO]:
        """Get user details by user ID."""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return None
        return self._convert_user_entity_to_dto(user)

    async def login_user(self, authenticated_user: AuthenticatedUser) -> UserDTO:
        """
        Complete login flow - get user by Firebase UID and update last login.
        Returns UserDTO if found, None otherwise.
        """
        await self.get_user_by_email(authenticated_user.email)

        # Update last login timestamp
        await self.update_user_login(authenticated_user.email)

        # Refresh user data to get updated last_login_at
        user_dto = await self.get_user_by_email(authenticated_user.email)

        return user_dto

    async def update_user_login(self, email: str) -> bool:
        """Update user's last login timestamp."""
        user = await self.user_repository.update_last_login(email)
        return user is not None

    @classmethod
    def _convert_user_entity_to_dto(cls, user) -> UserDTO:
        """Convert User entity to UserDTO for service layer communication."""
        return UserDTO(
            id=user.id,
            firebase_uid=user.firebase_uid,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone_number=user.phone_number,
            profile_image_url=user.profile_image_url,
            status=user.status.value,
            email_verified=user.email_verified,
            phone_verified=user.phone_verified,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
