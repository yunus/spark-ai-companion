import structlog
import firebase_admin
from firebase_admin import credentials, auth
from typing import Dict, Optional, Any
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings
from app.core.exceptions import (
    FirebaseTokenVerificationError,
    FirebaseInitializationError,
)

logger = structlog.get_logger(__name__)


class FirebaseClient:
    def __init__(self):
        self._app: Optional[firebase_admin.App] = None
        self._executor = ThreadPoolExecutor(max_workers=10)
        self._is_initialized = False

    async def initialize(self) -> None:
        """
        Initialize Firebase Admin SDK asynchronously.

        Raises:
            FirebaseInitializationError: If initialization fails
        """
        if self._is_initialized:
            logger.info("Firebase Admin SDK already initialized")
            return

        try:
            # Check if Firebase is already initialized globally
            try:
                self._app = firebase_admin.get_app()
                self._is_initialized = True
                logger.info("Using existing Firebase Admin SDK instance")
                return
            except ValueError:
                # Firebase not initialized, continue with initialization
                pass

            credentials_path = settings.firebase_credentials_path

            # Check if credentials file exists
            if not os.path.exists(credentials_path):
                error_msg = f"Firebase credentials file not found at {credentials_path}"
                logger.error(error_msg)
                raise FirebaseInitializationError(error_msg)

            # Initialize Firebase Admin SDK
            cred = credentials.Certificate(credentials_path)
            self._app = firebase_admin.initialize_app(cred)
            self._is_initialized = True

            logger.info("Firebase Admin SDK initialized successfully")

        except FileNotFoundError as e:
            error_msg = f"Firebase credentials file not found: {str(e)}"
            logger.error(error_msg)
            raise FirebaseInitializationError(error_msg)

        except Exception as e:
            error_msg = f"Error initializing Firebase Admin SDK: {str(e)}"
            logger.error(error_msg)
            raise FirebaseInitializationError(error_msg)

    def _ensure_initialized(self):
        """Ensure Firebase is initialized before operations."""
        if not self._is_initialized:
            raise FirebaseInitializationError(
                "Firebase not initialized. Call initialize() first."
            )

    async def verify_token(
        self, token: str, check_revoked: bool = True
    ) -> Dict[str, Any]:
        """
        Verify Firebase ID token and return decoded token.

        Args:
            token: Firebase ID token
            check_revoked: Whether to check if token has been revoked

        Returns:
            dict: Decoded token containing user information

        Raises:
            FirebaseTokenVerificationError: If token is invalid or verification fails
        """
        self._ensure_initialized()

        if not token or not token.strip():
            raise FirebaseTokenVerificationError("Token cannot be empty")

        try:
            # Run token verification in executor to avoid blocking
            loop = asyncio.get_event_loop()
            decoded_token = await loop.run_in_executor(
                self._executor,
                lambda: auth.verify_id_token(token, check_revoked=check_revoked),
            )
            return decoded_token

        except auth.ExpiredIdTokenError as e:
            error_msg = f"Expired Firebase token: {str(e)}"
            logger.warning(error_msg)
            raise FirebaseTokenVerificationError(error_msg)

        except auth.RevokedIdTokenError as e:
            error_msg = f"Revoked Firebase token: {str(e)}"
            logger.warning(error_msg)
            raise FirebaseTokenVerificationError(error_msg)

        except auth.InvalidIdTokenError as e:
            error_msg = f"Invalid Firebase token: {str(e)}"
            logger.warning(error_msg)
            raise FirebaseTokenVerificationError(error_msg)

        except Exception as e:
            error_msg = f"Error verifying Firebase token: {str(e)}"
            logger.error(error_msg)
            raise FirebaseTokenVerificationError(error_msg)
