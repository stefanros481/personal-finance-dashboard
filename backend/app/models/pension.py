"""Pension-related models."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class PensionAccount(Base):
    """Pension account model."""

    __tablename__ = "pension_accounts"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    provider = Column(String)
    currency = Column(String(3), nullable=False, default="USD")
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="pension_accounts")
    value_entries = relationship(
        "PensionValueEntry", back_populates="account", cascade="all, delete-orphan"
    )


class PensionValueEntry(Base):
    """Monthly pension value entry model."""

    __tablename__ = "pension_value_entries"

    id = Column(String, primary_key=True, index=True)
    account_id = Column(String, ForeignKey("pension_accounts.id"), nullable=False)
    value = Column(Numeric(20, 2), nullable=False)
    contributions = Column(Numeric(20, 2), default=0)
    entry_date = Column(DateTime, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    account = relationship("PensionAccount", back_populates="value_entries")
