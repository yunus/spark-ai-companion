from fastapi import HTTPException, status
from typing import Optional


class AppException(HTTPException):
    """Base exception class for all application-specific exceptions."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "app_error",
        error_type: str = "ApplicationError",
        message: str = "An unexpected error occurred",
        headers: Optional[dict] = None,
        details: Optional[dict] = None,
    ):
        self.error_code = error_code
        self.error_type = error_type
        self.message = message
        self.status_code = status_code
        self.details = details or {}

        # Call the parent with the message; custom handler will format the response
        super().__init__(status_code=status_code, detail=message, headers=headers)


class FirebaseInitializationError(AppException):
    """Raised when Firebase initialization fails."""

    def __init__(
        self,
        message: str = "Failed to initialize Firebase",
        details: Optional[dict] = None,
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="firebase_init_failed",
            error_type="FirebaseInitializationError",
            message=message,
            details=details,
        )


class FirebaseTokenVerificationError(AppException):
    """Raised when Firebase token verification fails."""

    def __init__(
        self,
        message: str = "Firebase token verification failed",
        details: Optional[dict] = None,
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="firebase_token_invalid",
            error_type="FirebaseTokenVerificationError",
            message=message,
            details=details,
        )


class UserAlreadyExistsError(AppException):
    """Raised when attempting to create a user that already exists."""

    def __init__(
        self, message: str = "User already exists", details: Optional[dict] = None
    ):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="user_exists",
            error_type="UserAlreadyExistsError",
            message=message,
            details=details,
        )


class UserNotFoundError(AppException):
    """Raised when a requested user is not found."""

    def __init__(self, message: str = "User not found", details: Optional[dict] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="user_not_found",
            error_type="UserNotFoundError",
            message=message,
            details=details,
        )


class ValidationError(AppException):
    """Raised when input validation fails."""

    def __init__(
        self, message: str = "Validation failed", details: Optional[dict] = None
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="validation_failed",
            error_type="ValidationError",
            message=message,
            details=details,
        )


class AuthorizationError(AppException):
    """Raised when user is not authorized to perform an action."""

    def __init__(self, message: str = "Access denied", details: Optional[dict] = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="access_denied",
            error_type="AuthorizationError",
            message=message,
            details=details,
        )


class AgentNotFoundError(AppException):
    """Raised when a requested agent is not found."""

    def __init__(
        self,
        message: str = "Agent not found",
        details: Optional[dict] = None,
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="agent_not_found",
            error_type="AgentNotFoundError",
            message=message,
            details=details,
        )


class SessionNotFoundError(AppException):
    """Raised when a requested session is not found."""

    def __init__(
        self,
        message: str = "Session not found",
        details: Optional[dict] = None,
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="session_not_found",
            error_type="SessionNotFoundError",
            message=message,
            details=details,
        )


__all__ = [
    "AppException",
    "FirebaseInitializationError",
    "FirebaseTokenVerificationError",
    "UserAlreadyExistsError",
    "UserNotFoundError",
    "ValidationError",
    "AuthorizationError",
    "AgentNotFoundError",
    "SessionNotFoundError",
]
