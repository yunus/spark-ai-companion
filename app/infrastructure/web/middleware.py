import time
import uuid
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from structlog import BoundLogger
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.logging import get_logger


class WebSocketFriendlyLoggingMiddleware:
    """Custom ASGI middleware that properly handles both HTTP and WebSocket connections."""

    def __init__(self, app: ASGIApp, logger: Optional[BoundLogger] = None):
        self.app = app
        self.logger = logger or get_logger(__name__)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            await self._handle_http(scope, receive, send)
        elif scope["type"] == "websocket":
            await self._handle_websocket(scope, receive, send)
        else:
            await self.app(scope, receive, send)

    async def _handle_http(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Handle HTTP requests with logging."""
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Extract client info
        client = scope.get("client")
        client_ip = client[0] if client else "unknown"
        path = scope.get("path", "")
        method = scope.get("method", "")

        self.logger.info(
            "HTTP request started",
            request_id=request_id,
            client_ip=client_ip,
            method=method,
            path=path,
            request_phase="started",
        )

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                duration_ms = round((time.time() - start_time) * 1000, 2)
                status_code = message.get("status", 0)

                self.logger.info(
                    "HTTP request finished",
                    request_id=request_id,
                    client_ip=client_ip,
                    method=method,
                    path=path,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    request_phase="completed",
                )

                # Add request ID header
                headers = list(message.get("headers", []))
                headers.append([b"x-request-id", request_id.encode()])
                message["headers"] = headers

            await send(message)

        await self.app(scope, receive, send_wrapper)

    async def _handle_websocket(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        """Handle WebSocket connections with logging."""
        connection_id = str(uuid.uuid4())
        client = scope.get("client")
        client_ip = client[0] if client else "unknown"
        path = scope.get("path", "")

        self.logger.info(
            "WebSocket connection attempt",
            connection_id=connection_id,
            client_ip=client_ip,
            path=path,
            websocket_phase="connecting",
        )

        async def send_wrapper(message):
            if message["type"] == "websocket.accept":
                self.logger.info(
                    "WebSocket connection accepted",
                    connection_id=connection_id,
                    client_ip=client_ip,
                    path=path,
                    websocket_phase="connected",
                )
            elif message["type"] == "websocket.close":
                self.logger.info(
                    "WebSocket connection closed",
                    connection_id=connection_id,
                    client_ip=client_ip,
                    path=path,
                    websocket_phase="disconnected",
                )

            await send(message)

        await self.app(scope, receive, send_wrapper)


class MiddlewareManager:
    """Enhanced middleware manager with WebSocket support."""

    def __init__(self, logger: Optional[BoundLogger] = None):
        self.logger = logger or get_logger(__name__)

    def setup_middleware(self, app: FastAPI) -> None:
        """Configure application middleware with WebSocket support."""
        self.logger.info(
            "Setting up application middleware", middleware_phase="setup_started"
        )

        # CORS middleware - must be first for WebSocket support
        cors_config = {
            "allow_origins": ["*"],  # Configure for production
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }
        app.add_middleware(CORSMiddleware, **cors_config)

        # Custom logging middleware that handles both HTTP and WebSocket
        app.add_middleware(WebSocketFriendlyLoggingMiddleware, logger=self.logger)

        self.logger.info(
            "Application middleware setup completed",
            middleware_phase="setup_completed",
            middlewares_configured=["cors", "websocket_friendly_logging"],
            cors_config=cors_config,
        )
