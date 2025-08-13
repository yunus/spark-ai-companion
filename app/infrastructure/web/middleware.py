import time
import uuid
from typing import Optional
import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from structlog import BoundLogger

from app.core.logging import get_logger


class MiddlewareManager:
    """Manages application middleware configuration."""

    def __init__(self, logger: Optional[BoundLogger] = None):
        self.logger = logger or get_logger(__name__)

    async def logging_middleware(self, request: Request, call_next):
        """Log request and response information with structured logging."""
        # Clear the context for each new request
        structlog.contextvars.clear_contextvars()

        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Extract request information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        content_length = request.headers.get("content-length")

        # Bind the request context variables
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            client_ip=client_ip,
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params) if request.query_params else None,
        )

        # Log request start
        self.logger.info(
            "Request started",
            request_id=request_id,
            client_ip=client_ip,
            method=request.method,
            path=request.url.path,
            user_agent=user_agent,
            content_length=content_length,
            query_params=dict(request.query_params) if request.query_params else None,
            request_phase="started",
        )

        try:
            # Process the request
            response: Response = await call_next(request)

            # Calculate request duration
            duration_ms = round((time.time() - start_time) * 1000, 2)

            # Extract response information
            response_size = response.headers.get("content-length")

            # Log successful request completion
            self.logger.info(
                "Request finished",
                request_id=request_id,
                client_ip=client_ip,
                status_code=response.status_code,
                duration_ms=duration_ms,
                response_size=response_size,
                request_phase="completed",
                success=True,
            )

            # Add request ID to response headers for tracing
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate duration even for failed requests
            duration_ms = round((time.time() - start_time) * 1000, 2)

            # Log request failure
            self.logger.error(
                "Request failed",
                request_id=request_id,
                client_ip=client_ip,
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                error_type=type(e).__name__,
                error=str(e),
                request_phase="failed",
                success=False,
                exc_info=True,
            )

            # Re-raise the exception to be handled by exception handlers
            raise

    def setup_middleware(self, app: FastAPI) -> None:
        """Configure application middleware."""
        self.logger.info(
            "Setting up application middleware", middleware_phase="setup_started"
        )

        # Add logging middleware first (it will be executed last due to FastAPI's middleware stack)
        app.middleware("http")(self.logging_middleware)

        # CORS middleware configuration
        cors_config = {
            "allow_origins": ["*"],  # In production, specify exact origins
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }

        app.add_middleware(CORSMiddleware, **cors_config)

        self.logger.info(
            "Application middleware setup completed",
            middleware_phase="setup_completed",
            middlewares_configured=["logging", "cors"],
            cors_config=cors_config,
        )
