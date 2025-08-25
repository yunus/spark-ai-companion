from typing import Optional
from pydantic import Field

from app.domain.schemas.response.base import StandardResponse
from app.domain.schemas.base import AppBaseModel


class ErrorData(AppBaseModel):
    """Error data portion of the response"""

    error_code: str = Field(..., description="Specific error code for client handling")
    error_type: str = Field(..., description="Type/category of the error")
    timestamp: str = Field(..., description="ISO format timestamp when error occurred")
    path: str = Field(..., description="API path where error occurred")
    details: Optional[dict] = Field(None, description="Additional error details")


class StandardErrorResponse(StandardResponse[ErrorData]):
    """Standardized error response format"""

    pass
