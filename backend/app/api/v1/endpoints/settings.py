"""Settings endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.schemas.settings import UserSettings, UserSettingsUpdate
from app.services.settings import get_user_settings, update_user_settings

router = APIRouter()


@router.get("/", response_model=UserSettings)
async def read_user_settings(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Get user settings."""
    settings = get_user_settings(db, current_user.id)
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Settings not found"
        )
    return settings


@router.put("/", response_model=UserSettings)
async def update_current_user_settings(
    settings_update: UserSettingsUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Update user settings."""
    settings = update_user_settings(db, current_user.id, settings_update)
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Settings not found"
        )
    return settings
