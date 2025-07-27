"""Security utilities."""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token types
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

# Refresh token settings
REFRESH_TOKEN_EXPIRE_DAYS = 30


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update(
        {"exp": expire, "type": ACCESS_TOKEN_TYPE, "iat": datetime.now(timezone.utc)}
    )

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(user_id: str) -> str:
    """Create a refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "sub": user_id,
        "exp": expire,
        "type": REFRESH_TOKEN_TYPE,
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_urlsafe(32),  # Unique token ID
    }

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


async def verify_refresh_token(token: str) -> Optional[str]:
    """
    Verify refresh token and return user ID.

    Args:
        token: Refresh token to verify

    Returns:
        User ID if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        # Check token type
        if payload.get("type") != REFRESH_TOKEN_TYPE:
            logger.warning("Invalid token type for refresh token")
            return None

        # Check if token is blacklisted
        jti = payload.get("jti")
        if jti:
            blacklist_key = f"blacklist:refresh:{jti}"
            is_blacklisted = await cache_service.exists(blacklist_key)
            if is_blacklisted:
                logger.warning(f"Refresh token is blacklisted: {jti}")
                return None

        user_id = payload.get("sub")
        if user_id is None:
            logger.warning("No user ID in refresh token")
            return None

        return user_id

    except JWTError as e:
        logger.warning(f"Refresh token verification failed: {str(e)}")
        return None


async def blacklist_refresh_token(token: str) -> bool:
    """
    Blacklist a refresh token.

    Args:
        token: Refresh token to blacklist

    Returns:
        True if successfully blacklisted, False otherwise
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        jti = payload.get("jti")

        if jti:
            # Calculate remaining TTL for the token
            exp = payload.get("exp")
            if exp:
                expire_time = datetime.fromtimestamp(exp, tz=timezone.utc)
                remaining_seconds = int(
                    (expire_time - datetime.now(timezone.utc)).total_seconds()
                )

                if remaining_seconds > 0:
                    blacklist_key = f"blacklist:refresh:{jti}"
                    await cache_service.set(
                        blacklist_key, "blacklisted", ttl_seconds=remaining_seconds
                    )
                    logger.info(f"Refresh token blacklisted: {jti}")
                    return True

        return False

    except JWTError as e:
        logger.warning(f"Failed to blacklist refresh token: {str(e)}")
        return False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password strength.

    Args:
        password: Password to validate

    Returns:
        Dict with validation results
    """
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")

    if len(password) > 100:
        errors.append("Password must be less than 100 characters long")

    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")

    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Password must contain at least one special character")

    return {"is_valid": len(errors) == 0, "errors": errors}
