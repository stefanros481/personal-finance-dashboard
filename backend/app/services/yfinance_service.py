"""YFinance service for stock data integration."""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

import yfinance as yf
from fastapi import HTTPException

from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class YFinanceService:
    """Service for fetching stock data from yfinance."""

    def __init__(self):
        """Initialize the YFinance service."""
        self.cache_duration = timedelta(minutes=15)  # 15-minute cache duration

    async def get_current_price(self, ticker: str) -> Dict[str, any]:
        """
        Get current stock price for a ticker with 15-minute caching.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
            
        Returns:
            Dict containing current price information
            
        Raises:
            HTTPException: If ticker is invalid or data cannot be fetched
        """
        ticker = ticker.upper()
        cache_key = cache_service.generate_stock_price_key(ticker)
        
        # Try to get from cache first
        cached_data = await cache_service.get(cache_key)
        if cached_data is not None:
            logger.info(f"Returning cached price data for ticker: {ticker}")
            return cached_data
        
        try:
            logger.info(f"Fetching fresh price data for ticker: {ticker}")
            
            # Create yfinance ticker object
            stock = yf.Ticker(ticker)
            
            # Get current data
            info = stock.info
            
            # Check if ticker is valid (yfinance returns empty dict for invalid tickers)
            if not info or 'symbol' not in info:
                logger.warning(f"Invalid ticker symbol: {ticker}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Ticker '{ticker}' not found"
                )
            
            # Extract current price information
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            previous_close = info.get('previousClose')
            
            if current_price is None:
                logger.warning(f"No current price available for ticker: {ticker}")
                raise HTTPException(
                    status_code=404,
                    detail=f"No current price data available for ticker '{ticker}'"
                )
            
            # Calculate price change
            price_change = None
            price_change_percent = None
            if previous_close:
                price_change = current_price - previous_close
                price_change_percent = (price_change / previous_close) * 100
            
            result = {
                "ticker": ticker,
                "name": info.get("longName", ticker),
                "current_price": current_price,
                "previous_close": previous_close,
                "price_change": price_change,
                "price_change_percent": price_change_percent,
                "currency": info.get("currency", "USD"),
                "market_state": info.get("marketState", "UNKNOWN"),
                "last_updated": datetime.now().isoformat()
            }
            
            # Cache the result for 15 minutes
            await cache_service.set(cache_key, result)
            
            logger.info(f"Successfully fetched and cached price for {ticker}: ${current_price}")
            return result
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Error fetching price for ticker {ticker}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch stock data for '{ticker}'"
            )

    async def search_stocks(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Search for stocks by ticker or company name with caching.
        
        Args:
            query: Search query (ticker or company name)
            limit: Maximum number of results to return
            
        Returns:
            List of stock matches
            
        Note:
            This is a placeholder implementation. In a production system,
            you might want to use a dedicated search API or maintain
            a local database of stock symbols.
        """
        cache_key = cache_service.generate_stock_search_key(f"{query}_{limit}")
        
        # Try to get from cache first
        cached_data = await cache_service.get(cache_key)
        if cached_data is not None:
            logger.info(f"Returning cached search results for query: {query}")
            return cached_data
        
        try:
            logger.info(f"Performing fresh search for query: {query}")
            
            # For now, implement a simple search by trying the query as a ticker
            # In production, you'd want to use a proper search API
            ticker = query.upper()
            
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                if info and 'symbol' in info:
                    result = [{
                        "ticker": ticker,
                        "name": info.get("longName", ticker),
                        "exchange": info.get("exchange", ""),
                        "currency": info.get("currency", "USD")
                    }]
                    # Cache the successful result
                    await cache_service.set(cache_key, result)
                    return result
            except Exception:
                pass
            
            # Return empty list if no matches found
            result = []
            # Cache empty results for shorter time (5 minutes)
            await cache_service.set(cache_key, result, ttl_seconds=300)
            return result
            
        except Exception as e:
            logger.error(f"Error searching stocks for query {query}: {str(e)}")
            return []

    async def get_historical_data(
        self, 
        ticker: str, 
        period: str = "1mo", 
        interval: str = "1d"
    ) -> Dict[str, any]:
        """
        Get historical stock data with caching.
        
        Args:
            ticker: Stock ticker symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            
        Returns:
            Dict containing historical data
            
        Raises:
            HTTPException: If ticker is invalid or data cannot be fetched
        """
        ticker = ticker.upper()
        cache_key = cache_service.generate_stock_history_key(ticker, period, interval)
        
        # Try to get from cache first
        cached_data = await cache_service.get(cache_key)
        if cached_data is not None:
            logger.info(f"Returning cached historical data for {ticker} ({period}, {interval})")
            return cached_data
        
        try:
            logger.info(f"Fetching fresh historical data for {ticker} (period: {period}, interval: {interval})")
            
            stock = yf.Ticker(ticker.upper())
            
            # Get historical data
            hist = stock.history(period=period, interval=interval)
            
            if hist.empty:
                raise HTTPException(
                    status_code=404,
                    detail=f"No historical data available for ticker '{ticker}'"
                )
            
            # Convert to list of dictionaries
            historical_data = []
            for date, row in hist.iterrows():
                historical_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]) if row["Volume"] == row["Volume"] else 0  # NaN check
                })
            
            result = {
                "ticker": ticker,
                "period": period,
                "interval": interval,
                "data": historical_data,
                "last_updated": datetime.now().isoformat()
            }
            
            # Cache historical data for longer period (60 minutes) since it changes less frequently
            await cache_service.set(cache_key, result, ttl_seconds=3600)
            
            logger.info(f"Successfully fetched and cached historical data for {ticker}")
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching historical data for {ticker}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch historical data for '{ticker}'"
            )


# Global service instance
yfinance_service = YFinanceService()