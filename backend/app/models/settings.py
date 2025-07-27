"""User settings model."""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserSettings(Base):
    """User settings model."""

    __tablename__ = "user_settings"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    base_currency = Column(String(3), nullable=False, default="USD")
    additional_currencies = Column(JSON, default=list)  # List of currency codes
    retirement_goal = Column(
        JSON, default=dict
    )  # {"target_amount": 0, "target_date": null}
    ynab_budget_id = Column(String)
    theme = Column(String, default="light")  # light or dark
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="settings")
