from datetime import datetime
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse
from structlog import BoundLogger

from app.core.config import Settings
from app.core.exceptions import AppException
from app.domain.schemas.response.exception import StandardErrorResponse, ErrorData


class ExceptionHandlerManager:
    """Manages application exception handlers."""

    def __init__(self, logger: BoundLogger, settings: Settings):
        self.logger = logger
        self.settings = settings

    @classmethod
    def create_error_response(
        cls,
        message: str,
        status_code: int,
        error_code: str,
        error_type: str,
        path: str,
        details: dict = None,
    ) -> StandardErrorResponse:
        """Create a standardized error response using Pydantic schema"""
        error_data = ErrorData(
            error_code=error_code,
            error_type=error_type,
            timestamp=datetime.now().isoformat(),
            path=path,
            details=details or {},
        )

        return StandardErrorResponse(
            message=message, status_code=status_code, data=error_data
        )

    def setup_exception_handlers(self, app: FastAPI) -> None:
        """Setup global exception handlers."""

        # Handle Pydantic validation errors
        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(
            request: Request, exc: RequestValidationError
        ):
            """Handle Pydantic validation errors with consistent format."""

            # Extract validation error details
            validation_errors = []
            first_error_msg = "Validation failed"

            for error in exc.errors():
                field_name = " -> ".join(
                    str(loc) for loc in error["loc"][1:]
                )  # Skip 'body'
                error_detail = {
                    "field": field_name,
                    "message": error["msg"],
                    "type": error["type"],
                    "input": error.get("input"),
                }
                if "ctx" in error:
                    error_detail["context"] = error["ctx"]

                validation_errors.append(error_detail)

                # Use the first error message for the main message
                if len(validation_errors) == 1:
                    first_error_msg = (
                        f"Validation failed for {field_name}: {error['msg']}"
                    )

            # Log the validation error
            self.logger.warning(
                "Validation error occurred",
                error_count=len(validation_errors),
                path=request.url.path,
                method=request.method,
                validation_errors=validation_errors,
            )

            error_response = self.create_error_response(
                message=first_error_msg,
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                error_code="validation_failed",
                error_type="ValidationError",
                path=request.url.path,
                details={"validation_errors": validation_errors},
            )

            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=error_response.model_dump(),
            )

        # Universal handler for all AppException and its subclasses
        @app.exception_handler(AppException)
        async def app_exception_handler(request: Request, exc: AppException):
            """Handle all custom application exceptions with consistent format."""

            # Log the exception
            self.logger.error(
                "Application exception occurred",
                error_type=exc.error_type,
                error_code=exc.error_code,
                message=exc.message,
                status_code=exc.status_code,
                path=request.url.path,
                method=request.method,
            )

            error_response = self.create_error_response(
                message=exc.message,
                status_code=exc.status_code,
                error_code=exc.error_code,
                error_type=exc.error_type,
                path=request.url.path,
                details=exc.details,
            )

            return JSONResponse(
                status_code=exc.status_code,
                content=error_response.model_dump(),
                headers=exc.headers,
            )

        @app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            """Handle FastAPI HTTPException with consistent format."""

            # Map common HTTP exceptions to error codes
            error_code_mapping = {
                401: "authentication_required",
                403: "forbidden",
                404: "not_found",
                422: "validation_error",
                429: "rate_limit_exceeded",
            }

            error_type_mapping = {
                401: "AuthenticationError",
                403: "AuthorizationError",
                404: "NotFoundError",
                422: "ValidationError",
                429: "RateLimitError",
            }

            error_code = error_code_mapping.get(exc.status_code, "http_error")
            error_type = error_type_mapping.get(exc.status_code, "HTTPError")

            # Log the exception
            self.logger.error(
                "HTTP exception occurred",
                error_type=error_type,
                error_code=error_code,
                message=exc.detail,
                status_code=exc.status_code,
                path=request.url.path,
                method=request.method,
            )

            # Handle validation errors with more details
            details = None
            if (
                exc.status_code == 422
                and hasattr(exc, "detail")
                and isinstance(exc.detail, list)
            ):
                details = {"validation_errors": exc.detail}

            error_response = self.create_error_response(
                message=(
                    exc.detail
                    if isinstance(exc.detail, str)
                    else "Validation error occurred"
                ),
                status_code=exc.status_code,
                error_code=error_code,
                error_type=error_type,
                path=request.url.path,
                details=details,
            )

            return JSONResponse(
                status_code=exc.status_code,
                content=error_response.model_dump(),
                headers=exc.headers,
            )

        # Handle unexpected exceptions
        @app.exception_handler(Exception)
        async def generic_exception_handler(request: Request, exc: Exception):
            """Handle unexpected exceptions."""

            # Log the unexpected exception
            self.logger.error(
                "Unexpected exception occurred",
                exception_type=type(exc).__name__,
                exception_message=str(exc),
                path=request.url.path,
                method=request.method,
                exc_info=True,
            )

            # Don't expose internal error details in production
            if self.settings.DEBUG:
                message = f"Internal server error: {str(exc)}"
                error_type = type(exc).__name__
                details = {"exception_details": str(exc)}
            else:
                message = "An unexpected error occurred. Please try again later."
                error_type = "InternalServerError"
                details = {}

            error_response = self.create_error_response(
                message=message,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_code="internal_server_error",
                error_type=error_type,
                path=request.url.path,
                details=details,
            )

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response.model_dump(),
            )
