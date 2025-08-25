import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.core.exceptions import UserAlreadyExistsError
from app.infrastructure.database.models.user import User, UserStatus
from app.domain.dto.user import CreateUserDTO


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, create_user_dto: CreateUserDTO) -> User:
        """Create a new user in the database using DTO."""
        try:
            user = User(
                id=str(uuid.uuid4()),  # Generate UUID for primary key
                firebase_uid=create_user_dto.firebase_uid,
                email=create_user_dto.email,
                first_name=create_user_dto.first_name,
                last_name=create_user_dto.last_name,
                phone_number=create_user_dto.phone_number,
                profile_image_url=create_user_dto.profile_image_url,
                email_verified=create_user_dto.email_verified,
                status=UserStatus.ACTIVE,
            )
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            return user
        except IntegrityError as e:
            await self.session.rollback()
            if "firebase_uid" in str(e.orig):
                raise UserAlreadyExistsError(
                    f"User with firebase_uid '{create_user_dto.firebase_uid}' already exists"
                )
            elif "email" in str(e.orig):
                raise UserAlreadyExistsError(
                    f"User with email '{create_user_dto.email}' already exists"
                )
            else:
                raise

    async def get_by_firebase_uid(self, firebase_uid: str) -> Optional[User]:
        """Get user by Firebase UID."""
        result = await self.session.execute(
            select(User).where(User.firebase_uid == firebase_uid)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def user_exists_by_firebase_uid(self, firebase_uid: str) -> bool:
        """Check if user exists by Firebase UID."""
        user = await self.get_by_firebase_uid(firebase_uid)
        return user is not None

    async def update_last_login(self, email: str) -> Optional[User]:
        """Update user's last login timestamp."""
        user = await self.get_by_email(email)
        if user:
            user.last_login_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(user)
        return user

    async def update_user_status(
        self, firebase_uid: str, status: UserStatus
    ) -> Optional[User]:
        """Update user's status."""
        user = await self.get_by_firebase_uid(firebase_uid)
        if user:
            user.status = status
            user.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(user)
        return user
