"""Portfolio schemas."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel

from app.models.portfolio import TransactionType


class PortfolioBase(BaseModel):
    """Base portfolio schema."""

    name: str
    description: Optional[str] = None
    currency: str = "USD"


class PortfolioCreate(PortfolioBase):
    """Portfolio creation schema."""

    pass


class PortfolioUpdate(BaseModel):
    """Portfolio update schema."""

    name: Optional[str] = None
    description: Optional[str] = None
    currency: Optional[str] = None
    order: Optional[int] = None


class Portfolio(PortfolioBase):
    """Portfolio schema for API responses."""

    id: str
    user_id: str
    order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HoldingBase(BaseModel):
    """Base holding schema."""

    symbol: str
    name: Optional[str] = None


class Holding(HoldingBase):
    """Holding schema for API responses."""

    id: str
    portfolio_id: str
    current_quantity: Decimal
    average_cost_per_share: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TransactionBase(BaseModel):
    """Base transaction schema."""

    type: TransactionType
    quantity: Decimal
    price_per_share: Decimal
    total_amount: Decimal
    fees: Decimal = Decimal(0)
    currency: str
    exchange_rate: Decimal = Decimal(1)
    notes: Optional[str] = None
    transaction_date: datetime


class TransactionCreate(TransactionBase):
    """Transaction creation schema."""

    symbol: str  # For creating the holding if it doesn't exist


class TransactionUpdate(BaseModel):
    """Transaction update schema."""

    type: Optional[TransactionType] = None
    quantity: Optional[Decimal] = None
    price_per_share: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    fees: Optional[Decimal] = None
    currency: Optional[str] = None
    exchange_rate: Optional[Decimal] = None
    notes: Optional[str] = None
    transaction_date: Optional[datetime] = None


class Transaction(TransactionBase):
    """Transaction schema for API responses."""

    id: str
    holding_id: str
    average_cost_per_share_at_transaction: Optional[Decimal]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PortfolioWithHoldings(Portfolio):
    """Portfolio with holdings included."""

    holdings: List[Holding] = []


class HoldingWithTransactions(Holding):
    """Holding with transactions included."""

    transactions: List[Transaction] = []
