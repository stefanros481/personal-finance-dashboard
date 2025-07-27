"""Settings schemas."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class UserSettingsBase(BaseModel):
    """Base user settings schema."""
    base_currency: str = "USD"
    additional_currencies: List[str] = []
    retirement_goal: Dict[str, Any] = {}
    ynab_budget_id: Optional[str] = None
    theme: str = "light"


class UserSettingsUpdate(BaseModel):
    """User settings update schema."""
    base_currency: Optional[str] = None
    additional_currencies: Optional[List[str]] = None
    retirement_goal: Optional[Dict[str, Any]] = None
    ynab_budget_id: Optional[str] = None
    theme: Optional[str] = None


class UserSettings(UserSettingsBase):
    """User settings schema for API responses."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True