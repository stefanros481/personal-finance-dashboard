"""Pension-related schemas."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class PensionAccountBase(BaseModel):
    """Base pension account schema."""

    name: str
    provider: Optional[str] = None
    currency: str = "USD"
    description: Optional[str] = None


class PensionAccountCreate(PensionAccountBase):
    """Pension account creation schema."""

    pass


class PensionAccountUpdate(BaseModel):
    """Pension account update schema."""

    name: Optional[str] = None
    provider: Optional[str] = None
    currency: Optional[str] = None
    description: Optional[str] = None


class PensionAccount(PensionAccountBase):
    """Pension account schema for API responses."""

    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PensionValueEntryBase(BaseModel):
    """Base pension value entry schema."""

    value: Decimal
    contributions: Decimal = Decimal(0)
    entry_date: datetime
    notes: Optional[str] = None


class PensionValueEntryCreate(PensionValueEntryBase):
    """Pension value entry creation schema."""

    pass


class PensionValueEntryUpdate(BaseModel):
    """Pension value entry update schema."""

    value: Optional[Decimal] = None
    contributions: Optional[Decimal] = None
    entry_date: Optional[datetime] = None
    notes: Optional[str] = None


class PensionValueEntry(PensionValueEntryBase):
    """Pension value entry schema for API responses."""

    id: str
    account_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PensionAccountWithEntries(PensionAccount):
    """Pension account with value entries included."""

    value_entries: List[PensionValueEntry] = []


class PensionSummary(BaseModel):
    """Pension account summary with latest value and growth metrics."""

    account: PensionAccount
    latest_value: Optional[Decimal] = None
    total_contributions: Optional[Decimal] = None
    total_growth: Optional[Decimal] = None
    growth_percentage: Optional[Decimal] = None
    entries_count: int = 0