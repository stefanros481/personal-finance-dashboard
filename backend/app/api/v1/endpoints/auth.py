"""Authentication endpoints."""

import logging
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.rate_limiting import rate_limit_service
from app.core.security import (
    blacklist_refresh_token,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.schemas.auth import (
    ErrorResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
)
from app.schemas.user import User
from app.services.user import authenticate_user, get_user, update_user_login_info

logger = logging.getLogger(__name__)
router = APIRouter()


def get_client_ip(request: Request) -> str:
    """Get client IP address."""
    # Check for forwarded headers first (for reverse proxy setups)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback to direct connection
    return request.client.host if request.client else "unknown"


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """Enhanced login endpoint with rate limiting and comprehensive logging."""
    client_ip = get_client_ip(request)
    email = form_data.username.lower().strip()

    logger.info(f"Login attempt from {client_ip} for email: {email}")

    # Check rate limiting for both IP and email
    ip_rate_limited = await rate_limit_service.is_rate_limited(client_ip)
    email_rate_limited = await rate_limit_service.is_rate_limited(email)

    if ip_rate_limited or email_rate_limited:
        remaining_attempts_ip = await rate_limit_service.get_remaining_attempts(
            client_ip
        )
        remaining_attempts_email = await rate_limit_service.get_remaining_attempts(
            email
        )
        lockout_time = await rate_limit_service.get_lockout_time_remaining(email)

        logger.warning(f"Rate limited login attempt from {client_ip} for {email}")

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "too_many_attempts",
                "message": "Too many failed login attempts. Please try again later.",
                "remaining_attempts_ip": remaining_attempts_ip,
                "remaining_attempts_email": remaining_attempts_email,
                "lockout_time_seconds": lockout_time,
            },
        )

    # Attempt authentication
    try:
        user = await authenticate_user(db, email, form_data.password)

        if not user:
            # Record failed attempt for both IP and email
            await rate_limit_service.record_failed_attempt(client_ip)
            await rate_limit_service.record_failed_attempt(email)

            remaining_attempts = await rate_limit_service.get_remaining_attempts(email)

            logger.warning(f"Failed login attempt from {client_ip} for {email}")

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "invalid_credentials",
                    "message": "Incorrect email or password",
                    "remaining_attempts": remaining_attempts,
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Clear rate limiting on successful login
        await rate_limit_service.record_successful_attempt(client_ip)
        await rate_limit_service.record_successful_attempt(email)

        # Update user login information
        await update_user_login_info(db, user, client_ip)

        # Create tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(user.id)

        logger.info(f"Successful login for {email} from {client_ip}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "email": user.email,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login_at": (
                    user.last_login_at.isoformat() if user.last_login_at else None
                ),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error during login from {client_ip} for {email}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred during login",
            },
        )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    refresh_data: RefreshTokenRequest,
):
    """Refresh access token using refresh token."""
    client_ip = get_client_ip(request)

    logger.info(f"Token refresh attempt from {client_ip}")

    # Verify refresh token
    user_id = await verify_refresh_token(refresh_data.refresh_token)
    if not user_id:
        logger.warning(f"Invalid refresh token from {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_refresh_token",
                "message": "Invalid or expired refresh token",
            },
        )

    # Get user
    user = await get_user(db, user_id)
    if not user or not user.is_active:
        logger.warning(f"Refresh token for inactive/missing user: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "user_not_found", "message": "User not found or inactive"},
        )

    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    logger.info(f"Token refreshed successfully for user: {user.email}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/logout")
async def logout(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)],
    refresh_token: str = None,
):
    """Logout and blacklist refresh token."""
    client_ip = get_client_ip(request)

    logger.info(f"Logout request from {client_ip} for user: {current_user.email}")

    if refresh_token:
        # Blacklist the refresh token
        blacklisted = await blacklist_refresh_token(refresh_token)
        if blacklisted:
            logger.info(f"Refresh token blacklisted for user: {current_user.email}")
        else:
            logger.warning(
                f"Failed to blacklist refresh token for user: {current_user.email}"
            )

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Get current user info."""
    return current_user
