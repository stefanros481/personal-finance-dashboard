"""Market data models."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Decimal as SQLDecimal, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class StockMetadata(Base):
    """Stock metadata model."""

    __tablename__ = "stock_metadata"

    symbol = Column(String, primary_key=True, index=True)
    name = Column(String)
    exchange = Column(String)
    currency = Column(String(3))
    sector = Column(String)
    industry = Column(String)
    description = Column(Text)
    logo_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HistoricalStockPrice(Base):
    """Historical stock price model."""

    __tablename__ = "historical_stock_prices"
    __table_args__ = (UniqueConstraint("symbol", "date", name="uq_symbol_date"),)

    id = Column(String, primary_key=True, index=True)
    symbol = Column(String, nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    open = Column(SQLDecimal(20, 8))
    high = Column(SQLDecimal(20, 8))
    low = Column(SQLDecimal(20, 8))
    close = Column(SQLDecimal(20, 8), nullable=False)
    adjusted_close = Column(SQLDecimal(20, 8))
    volume = Column(SQLDecimal(20, 0))
    created_at = Column(DateTime, default=datetime.utcnow)


class HistoricalExchangeRate(Base):
    """Historical exchange rate model."""

    __tablename__ = "historical_exchange_rates"
    __table_args__ = (UniqueConstraint("from_currency", "to_currency", "date", name="uq_currency_pair_date"),)

    id = Column(String, primary_key=True, index=True)
    from_currency = Column(String(3), nullable=False, index=True)
    to_currency = Column(String(3), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    rate = Column(SQLDecimal(20, 8), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)