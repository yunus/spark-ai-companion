import re

from pydantic import Field, model_validator
from typing_extensions import Self

from app.domain.schemas.base import AppBaseModel


class RegistrationRequest(AppBaseModel):
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="User's first name. Required for personalization.",
        examples=["John"],
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="User's last name. Required for personalization.",
        examples=["Doe"],
    )
    phone_number: str = Field(
        ...,
        min_length=10,
        max_length=15,
        description="User's phone number in international format (with country code). Used for verification and travel alerts.",
        examples=["+1234567890"],
    )

    @model_validator(mode="after")
    def validate_phone_number(self) -> Self:
        if not re.match(r"^\+[1-9]\d{1,14}$", self.phone_number):
            raise ValueError(
                "Phone number must be in international format starting with + and country code"
            )
        return self


__all__ = ["RegistrationRequest"]
