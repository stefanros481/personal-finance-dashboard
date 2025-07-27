"""Authentication schemas."""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request schema with validation."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ..., min_length=8, max_length=100, description="User password"
    )


class Token(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str
    expires_in: int
    user_id: str
    email: str


class TokenData(BaseModel):
    """Token data schema."""

    username: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Refresh token response schema."""

    access_token: str
    token_type: str
    expires_in: int


class LoginResponse(BaseModel):
    """Comprehensive login response."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: dict


class ErrorResponse(BaseModel):
    """Structured error response."""

    error: str
    message: str
    details: Optional[dict] = None
