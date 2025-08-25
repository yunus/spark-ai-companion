from typing import Generic, TypeVar

from pydantic import Field

from app.domain.schemas.base import AppBaseModel

# Generic type for response data
T = TypeVar("T")


class StandardResponse(AppBaseModel, Generic[T]):
    """Standard API response wrapper"""

    message: str = Field(..., description="Response message")
    status_code: int = Field(..., description="HTTP status code")
    data: T = Field(..., description="Response data")


__all__ = ["StandardResponse"]
