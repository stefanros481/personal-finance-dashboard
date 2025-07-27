"""Settings service."""
from typing import Optional

from sqlalchemy.orm import Session

from app.models.settings import UserSettings
from app.schemas.settings import UserSettingsUpdate


def get_user_settings(db: Session, user_id: str) -> Optional[UserSettings]:
    """Get user settings."""
    return db.query(UserSettings).filter(UserSettings.user_id == user_id).first()


def update_user_settings(
    db: Session, user_id: str, settings_update: UserSettingsUpdate
) -> Optional[UserSettings]:
    """Update user settings."""
    db_settings = get_user_settings(db, user_id)
    if not db_settings:
        return None
    
    update_data = settings_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_settings, field, value)
    
    db.commit()
    db.refresh(db_settings)
    return db_settings