"""User service."""
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.models.settings import UserSettings
from app.schemas.user import UserCreate


def get_user(db: Session, user_id: str) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user_create: UserCreate) -> User:
    """Create a new user."""
    db_user = User(
        id=str(uuid.uuid4()),
        email=user_create.email,
        hashed_password=get_password_hash(user_create.password),
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
    
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user."""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user