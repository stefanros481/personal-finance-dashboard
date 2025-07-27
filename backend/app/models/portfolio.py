"""Portfolio, Holding, and Transaction models."""
from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class TransactionType(str, Enum):
    """Transaction type enum."""
    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"
    SPLIT = "SPLIT"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"


class Portfolio(Base):
    """Portfolio model."""

    __tablename__ = "portfolios"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    currency = Column(String(3), nullable=False, default="USD")
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="portfolios")
    holdings = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")


class Holding(Base):
    """Holding model."""

    __tablename__ = "holdings"

    id = Column(String, primary_key=True, index=True)
    portfolio_id = Column(String, ForeignKey("portfolios.id"), nullable=False)
    symbol = Column(String, nullable=False, index=True)
    name = Column(String)
    current_quantity = Column(Numeric(20, 8), nullable=False, default=0)
    average_cost_per_share = Column(Numeric(20, 8), nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")
    transactions = relationship("Transaction", back_populates="holding", cascade="all, delete-orphan")


class Transaction(Base):
    """Transaction model."""

    __tablename__ = "transactions"

    id = Column(String, primary_key=True, index=True)
    holding_id = Column(String, ForeignKey("holdings.id"), nullable=False)
    type = Column(SQLEnum(TransactionType), nullable=False)
    quantity = Column(Numeric(20, 8), nullable=False)
    price_per_share = Column(Numeric(20, 8), nullable=False)
    total_amount = Column(Numeric(20, 8), nullable=False)
    fees = Column(Numeric(20, 8), default=0)
    currency = Column(String(3), nullable=False)
    exchange_rate = Column(Numeric(20, 8), default=1)  # To portfolio currency
    average_cost_per_share_at_transaction = Column(Numeric(20, 8))
    notes = Column(Text)
    transaction_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    holding = relationship("Holding", back_populates="transactions")