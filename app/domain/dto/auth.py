from typing import Optional, Dict, Any
from pydantic import BaseModel


class AuthenticatedUser(BaseModel):
    """DTO for authenticated user from Firebase token."""

    uid: str
    email: Optional[str] = None
    email_verified: Optional[bool] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    iss: Optional[str] = None
    aud: Optional[str] = None
    auth_time: Optional[int] = None
    user_id: Optional[str] = None
    sub: Optional[str] = None
    iat: Optional[int] = None
    exp: Optional[int] = None
    firebase: Optional[Dict[str, Any]] = None

    @classmethod
    def from_token(cls, token_data: dict) -> "AuthenticatedUser":
        """Create AuthenticatedUser from decoded Firebase token."""
        # Ensure uid is present, fallback to user_id
        uid = token_data.get("uid") or token_data.get("user_id")
        if not uid:
            raise ValueError("Token must contain either 'uid' or 'user_id'")

        return cls(
            uid=uid,
            email=token_data.get("email"),
            email_verified=token_data.get("email_verified"),
            name=token_data.get("name"),
            picture=token_data.get("picture"),
            iss=token_data.get("iss"),
            aud=token_data.get("aud"),
            auth_time=token_data.get("auth_time"),
            user_id=token_data.get("user_id"),
            sub=token_data.get("sub"),
            iat=token_data.get("iat"),
            exp=token_data.get("exp"),
            firebase=token_data.get("firebase"),
        )
