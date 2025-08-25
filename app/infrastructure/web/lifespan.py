import sys
from typing import Optional
from structlog import BoundLogger

from app.core.config import Settings
from app.core.logging import get_logger
from app.core.exceptions import FirebaseInitializationError
from app.infrastructure.external.firebase_client import FirebaseClient


class LifespanManager:
    """Manages application startup and shutdown lifecycle."""

    def __init__(
        self, logger: Optional[BoundLogger] = None, settings: Optional[Settings] = None
    ):
        self.logger = logger or get_logger(__name__)
        self.settings = settings

    async def startup(self) -> FirebaseClient:
        """Initialize application services on startup."""
        try:
            # settings logging
            self.logger.info(**self.settings.model_dump())

            # Initialize Firebase
            self.logger.info("Initializing Firebase Admin SDK...")

            firebase_client = FirebaseClient()
            await firebase_client.initialize()

            self.logger.info(
                "Firebase Admin SDK initialized successfully",
                service="firebase",
                status="initialized",
            )
            self.logger.info("✓ Firebase initialized successfully")

            self.logger.info(
                "🚀 Application startup completed successfully",
                startup_phase="complete",
                services_initialized=["firebase"],
            )

            return firebase_client

        except FirebaseInitializationError as e:
            self.logger.error(
                "Failed to initialize Firebase",
                service="firebase",
                error_type="FirebaseInitializationError",
                error=str(e),
                startup_phase="firebase_init",
                exc_info=True,
            )
            sys.exit(1)
        except Exception as e:
            self.logger.error(
                "Unexpected error during startup",
                error_type=type(e).__name__,
                error=str(e),
                startup_phase="unknown",
                exc_info=True,
            )
            sys.exit(1)

    async def shutdown(self, firebase_client: Optional[FirebaseClient] = None) -> None:
        """Cleanup application services on shutdown."""
        self.logger.info(
            "Shutting down AI Travel Agent API...", shutdown_phase="starting"
        )

        cleanup_results = []

        try:
            # Cleanup Firebase (if needed)
            if firebase_client:
                try:
                    # Firebase Admin SDK doesn't require explicit cleanup
                    # but we can cleanup our thread pool if it exists
                    if hasattr(firebase_client, "_executor"):
                        firebase_client._executor.shutdown(wait=True)
                        self.logger.info(
                            "Firebase executor shutdown completed",
                            service="firebase",
                            component="executor",
                            status="cleaned_up",
                        )

                    self.logger.info(
                        "✓ Firebase client cleaned up",
                        service="firebase",
                        status="cleaned_up",
                    )
                    cleanup_results.append({"service": "firebase", "status": "success"})

                except Exception as e:
                    self.logger.error(
                        "Error cleaning up Firebase client",
                        service="firebase",
                        error_type=type(e).__name__,
                        error=str(e),
                        exc_info=True,
                    )
                    cleanup_results.append(
                        {"service": "firebase", "status": "error", "error": str(e)}
                    )
            else:
                self.logger.info(
                    "No Firebase client to cleanup",
                    service="firebase",
                    status="skipped",
                )
                cleanup_results.append({"service": "firebase", "status": "skipped"})

        except Exception as e:
            self.logger.error(
                "Error during shutdown",
                error_type=type(e).__name__,
                error=str(e),
                shutdown_phase="cleanup",
                exc_info=True,
            )
            cleanup_results.append({"error": str(e), "status": "error"})

        self.logger.info(
            "👋 Application shutdown completed",
            shutdown_phase="complete",
            cleanup_results=cleanup_results,
        )
