"""Currency and exchange rate schemas."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class ExchangeRateBase(BaseModel):
    """Base exchange rate schema."""

    from_currency: str
    to_currency: str
    rate: Decimal
    date: datetime


class ExchangeRateCreate(ExchangeRateBase):
    """Exchange rate creation schema."""

    pass


class ExchangeRate(ExchangeRateBase):
    """Exchange rate schema for API responses."""

    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class CurrencyPair(BaseModel):
    """Currency pair for conversion requests."""

    from_currency: str
    to_currency: str


class CurrencyConversion(BaseModel):
    """Currency conversion result."""

    from_currency: str
    to_currency: str
    from_amount: Decimal
    to_amount: Decimal
    exchange_rate: Decimal
    rate_date: datetime


class CurrencyInfo(BaseModel):
    """Currency information."""

    code: str
    name: str
    symbol: str
    decimal_places: int = 2


class SupportedCurrencies(BaseModel):
    """List of supported currencies."""

    currencies: List[CurrencyInfo]
    base_currency: str = "USD"


class ExchangeRateHistoryRequest(BaseModel):
    """Request for historical exchange rates."""

    from_currency: str
    to_currency: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100


class ExchangeRateHistory(BaseModel):
    """Historical exchange rates response."""

    from_currency: str
    to_currency: str
    rates: List[ExchangeRate]
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None