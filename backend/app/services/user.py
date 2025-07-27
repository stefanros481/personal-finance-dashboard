"""User service."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.settings import UserSettings
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


async def get_user(db: Session, user_id: str) -> Optional[User]:
    """Get user by ID with caching."""
    # Try cache first
    cache_key = f"user:id:{user_id}"
    cached_user = await cache_service.get(cache_key)

    if cached_user is not None:
        logger.debug(f"User found in cache: {user_id}")
        # Note: In production, you'd want to reconstruct the User object
        # For now, we'll still query the database for simplicity

    user = db.query(User).filter(User.id == user_id).first()

    if user:
        # Cache for 5 minutes
        await cache_service.set(
            cache_key, {"id": user.id, "email": user.email}, ttl_seconds=300
        )
        logger.debug(f"User cached: {user_id}")

    return user


async def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email with caching."""
    # Try cache first
    cache_key = f"user:email:{email.lower()}"
    cached_user = await cache_service.get(cache_key)

    if cached_user is not None:
        logger.debug(f"User found in cache by email: {email}")
        # Query database to get full User object
        # In production, you might cache the full user data

    user = db.query(User).filter(User.email == email).first()

    if user:
        # Cache for 5 minutes
        await cache_service.set(
            cache_key, {"id": user.id, "email": user.email}, ttl_seconds=300
        )
        logger.debug(f"User cached by email: {email}")

    return user


def create_user(db: Session, user_create: UserCreate) -> User:
    """Create a new user."""
    logger.info(f"Creating new user: {user_create.email}")

    db_user = User(
        id=str(uuid.uuid4()),
        email=user_create.email,
        hashed_password=get_password_hash(user_create.password),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create default settings for the user
    user_settings = UserSettings(
        id=str(uuid.uuid4()),
        user_id=db_user.id,
    )
    db.add(user_settings)
    db.commit()

    logger.info(f"User created successfully: {db_user.id}")
    return db_user


async def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user with enhanced logging."""
    logger.info(f"Authentication attempt for email: {email}")

    user = await get_user_by_email(db, email)
    if not user:
        logger.warning(f"Authentication failed - user not found: {email}")
        return None

    if not user.is_active:
        logger.warning(f"Authentication failed - user inactive: {email}")
        return None

    if not verify_password(password, user.hashed_password):
        logger.warning(f"Authentication failed - invalid password: {email}")
        return None

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    db.commit()

    logger.info(f"Authentication successful: {email}")
    return user


async def update_user_login_info(
    db: Session, user: User, ip_address: str = None
) -> None:
    """Update user login information."""
    user.last_login_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)

    if ip_address:
        # In a more sophisticated system, you might track login history
        logger.info(f"User login from IP: {user.email} from {ip_address}")

    db.commit()

    # Clear user cache to ensure fresh data on next request
    cache_key_id = f"user:id:{user.id}"
    cache_key_email = f"user:email:{user.email.lower()}"
    await cache_service.delete(cache_key_id)
    await cache_service.delete(cache_key_email)
