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
        Search for stocks by ticker or company name with advanced search capabilities.
        
        Args:
            query: Search query (ticker or company name)
            limit: Maximum number of results to return
            
        Returns:
            List of stock matches with comprehensive search coverage
        """
        cache_key = cache_service.generate_stock_search_key(f"{query}_{limit}")
        
        # Try to get from cache first
        cached_data = await cache_service.get(cache_key)
        if cached_data is not None:
            logger.info(f"Returning cached search results for query: {query}")
            return cached_data
        
        try:
            logger.info(f"Performing comprehensive search for query: {query}")
            results = []
            
            # Strategy 1: Try exact ticker match first (for queries like 'AAPL', 'MSFT')
            if len(query) <= 5 and query.isalpha():
                try:
                    ticker = query.upper()
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    
                    if info and 'symbol' in info and info.get('symbol') == ticker:
                        results.append({
                            "ticker": ticker,
                            "name": info.get("longName", info.get("shortName", ticker)),
                            "exchange": info.get("exchange", ""),
                            "currency": info.get("currency", "USD")
                        })
                        logger.info(f"Found exact ticker match: {ticker}")
                except Exception as e:
                    logger.debug(f"No exact ticker match for {query}: {str(e)}")
            
            # Strategy 2: Use yfinance Search for company name or partial matches
            try:
                search_obj = yf.Search(query)
                search_quotes = search_obj.quotes
                
                if search_quotes:
                    logger.info(f"Found {len(search_quotes)} search results for: {query}")
                    
                    # Process search results
                    for quote in search_quotes[:limit]:
                        # Skip if we already have this ticker from exact match
                        ticker = quote.get('symbol', '')
                        if any(r['ticker'] == ticker for r in results):
                            continue
                            
                        # Filter for equity stocks primarily (can be expanded)
                        quote_type = quote.get('quoteType', '').upper()
                        if quote_type in ['EQUITY', 'ETF']:
                            result_item = {
                                "ticker": ticker,
                                "name": quote.get('longname', quote.get('shortname', ticker)),
                                "exchange": quote.get('exchDisp', quote.get('exchange', '')),
                                "currency": "USD"  # Default, could be enhanced
                            }
                            results.append(result_item)
                            
                            if len(results) >= limit:
                                break
                
            except Exception as e:
                logger.warning(f"yfinance Search failed for query '{query}': {str(e)}")
            
            # Strategy 3: For partial company name matching, try common patterns
            # (Run if we have no good results yet, regardless of filtered results from Strategy 2)
            if len(results) == 0 and len(query) > 2:
                common_expansions = {
                    'micro': 'Microsoft',
                    'apple': 'Apple',
                    'tesla': 'Tesla',
                    'amazon': 'Amazon',
                    'google': 'Alphabet',
                    'meta': 'Meta',
                    'netflix': 'Netflix'
                }
                
                expanded_query = common_expansions.get(query.lower())
                if expanded_query and expanded_query.lower() != query.lower():
                    try:
                        logger.info(f"Trying expanded search: {query} -> {expanded_query}")
                        search_obj = yf.Search(expanded_query)
                        search_quotes = search_obj.quotes
                        
                        for quote in search_quotes[:limit]:
                            quote_type = quote.get('quoteType', '').upper()
                            if quote_type in ['EQUITY', 'ETF']:
                                ticker = quote.get('symbol', '')
                                result_item = {
                                    "ticker": ticker,
                                    "name": quote.get('longname', quote.get('shortname', ticker)),
                                    "exchange": quote.get('exchDisp', quote.get('exchange', '')),
                                    "currency": "USD"
                                }
                                results.append(result_item)
                                
                                if len(results) >= limit:
                                    break
                                    
                    except Exception as e:
                        logger.debug(f"Expanded search failed for {expanded_query}: {str(e)}")
            
            # Remove duplicates and limit results
            seen_tickers = set()
            unique_results = []
            for result in results:
                ticker = result['ticker']
                if ticker not in seen_tickers:
                    seen_tickers.add(ticker)
                    unique_results.append(result)
                    if len(unique_results) >= limit:
                        break
            
            # Cache the results
            cache_duration = 900 if unique_results else 300  # 15 min for results, 5 min for empty
            await cache_service.set(cache_key, unique_results, ttl_seconds=cache_duration)
            
            logger.info(f"Search for '{query}' returned {len(unique_results)} results")
            return unique_results
            
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