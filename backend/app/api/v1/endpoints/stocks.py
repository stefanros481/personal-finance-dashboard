"""Stock-related API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.stocks import HistoricalData, StockPrice, StockSearch
from app.services.yfinance_service import yfinance_service

router = APIRouter()


@router.get("/{ticker}/price", response_model=StockPrice)
async def get_stock_price(ticker: str, current_user: User = Depends(get_current_user)):
    """
    Get current stock price for a ticker.

    - **ticker**: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
    """
    return await yfinance_service.get_current_price(ticker)


@router.get("/search", response_model=List[StockSearch])
async def search_stocks(
    q: str = Query(..., description="Search query (ticker or company name)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    current_user: User = Depends(get_current_user),
):
    """
    Search for stocks by ticker or company name.

    - **q**: Search query
    - **limit**: Maximum number of results (1-50)
    """
    return await yfinance_service.search_stocks(q, limit)


@router.get("/{ticker}/history", response_model=HistoricalData)
async def get_historical_data(
    ticker: str,
    period: str = Query(
        "1mo",
        description="Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)",
    ),
    interval: str = Query(
        "1d",
        description="Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)",
    ),
    current_user: User = Depends(get_current_user),
):
    """
    Get historical stock data.

    - **ticker**: Stock ticker symbol
    - **period**: Time period for historical data
    - **interval**: Data granularity interval
    """
    return await yfinance_service.get_historical_data(ticker, period, interval)
