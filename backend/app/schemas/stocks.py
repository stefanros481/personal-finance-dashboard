"""Stock-related Pydantic schemas."""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class StockPrice(BaseModel):
    """Schema for current stock price information."""
    ticker: str = Field(..., description="Stock ticker symbol")
    name: str = Field(..., description="Company name")
    current_price: float = Field(..., description="Current stock price")
    previous_close: Optional[float] = Field(None, description="Previous closing price")
    price_change: Optional[float] = Field(None, description="Price change from previous close")
    price_change_percent: Optional[float] = Field(None, description="Price change percentage")
    currency: str = Field("USD", description="Currency of the price")
    market_state: str = Field("UNKNOWN", description="Current market state")
    last_updated: str = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "current_price": 175.25,
                "previous_close": 174.50,
                "price_change": 0.75,
                "price_change_percent": 0.43,
                "currency": "USD",
                "market_state": "REGULAR",
                "last_updated": "2024-01-15T10:30:00"
            }
        }


class StockSearch(BaseModel):
    """Schema for stock search results."""
    ticker: str = Field(..., description="Stock ticker symbol")
    name: str = Field(..., description="Company name")
    exchange: str = Field("", description="Stock exchange")
    currency: str = Field("USD", description="Trading currency")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "exchange": "NASDAQ",
                "currency": "USD"
            }
        }


class HistoricalDataPoint(BaseModel):
    """Schema for a single historical data point."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="Highest price")
    low: float = Field(..., description="Lowest price")
    close: float = Field(..., description="Closing price")
    volume: int = Field(..., description="Trading volume")

    class Config:
        from_attributes = True


class HistoricalData(BaseModel):
    """Schema for historical stock data."""
    ticker: str = Field(..., description="Stock ticker symbol")
    period: str = Field(..., description="Time period")
    interval: str = Field(..., description="Data interval")
    data: List[HistoricalDataPoint] = Field(..., description="Historical data points")
    last_updated: str = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "period": "1mo",
                "interval": "1d",
                "data": [
                    {
                        "date": "2024-01-15",
                        "open": 174.25,
                        "high": 175.50,
                        "low": 173.80,
                        "close": 175.25,
                        "volume": 45123456
                    }
                ],
                "last_updated": "2024-01-15T10:30:00"
            }
        }