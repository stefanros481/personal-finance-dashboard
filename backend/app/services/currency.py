"""Currency and exchange rate service."""

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

import yfinance as yf
from fastapi import HTTPException, status
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from app.models.market_data import HistoricalExchangeRate
from app.schemas.currency import (
    CurrencyConversion,
    CurrencyInfo,
    ExchangeRate,
    ExchangeRateCreate,
    ExchangeRateHistory,
    SupportedCurrencies,
)
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class CurrencyService:
    """Service for currency and exchange rate operations."""

    # Major currencies with their display information
    SUPPORTED_CURRENCIES = {
        "USD": {"name": "US Dollar", "symbol": "$", "decimal_places": 2},
        "EUR": {"name": "Euro", "symbol": "€", "decimal_places": 2},
        "GBP": {"name": "British Pound", "symbol": "£", "decimal_places": 2},
        "JPY": {"name": "Japanese Yen", "symbol": "¥", "decimal_places": 0},
        "CHF": {"name": "Swiss Franc", "symbol": "CHF", "decimal_places": 2},
        "CAD": {"name": "Canadian Dollar", "symbol": "C$", "decimal_places": 2},
        "AUD": {"name": "Australian Dollar", "symbol": "A$", "decimal_places": 2},
        "SEK": {"name": "Swedish Krona", "symbol": "kr", "decimal_places": 2},
        "NOK": {"name": "Norwegian Krone", "symbol": "kr", "decimal_places": 2},
        "DKK": {"name": "Danish Krone", "symbol": "kr", "decimal_places": 2},
        "CNY": {"name": "Chinese Yuan", "symbol": "¥", "decimal_places": 2},
        "INR": {"name": "Indian Rupee", "symbol": "₹", "decimal_places": 2},
        "BRL": {"name": "Brazilian Real", "symbol": "R$", "decimal_places": 2},
        "ZAR": {"name": "South African Rand", "symbol": "R", "decimal_places": 2},
        "KRW": {"name": "South Korean Won", "symbol": "₩", "decimal_places": 0},
        "SGD": {"name": "Singapore Dollar", "symbol": "S$", "decimal_places": 2},
        "HKD": {"name": "Hong Kong Dollar", "symbol": "HK$", "decimal_places": 2},
        "NZD": {"name": "New Zealand Dollar", "symbol": "NZ$", "decimal_places": 2},
        "MXN": {"name": "Mexican Peso", "symbol": "$", "decimal_places": 2},
        "RUB": {"name": "Russian Ruble", "symbol": "₽", "decimal_places": 2},
    }

    @staticmethod
    def get_supported_currencies() -> SupportedCurrencies:
        """Get list of supported currencies."""
        currencies = [
            CurrencyInfo(
                code=code,
                name=info["name"],
                symbol=info["symbol"],
                decimal_places=info["decimal_places"],
            )
            for code, info in CurrencyService.SUPPORTED_CURRENCIES.items()
        ]
        
        return SupportedCurrencies(currencies=currencies, base_currency="USD")

    @staticmethod
    def validate_currency_code(currency: str) -> str:
        """Validate and normalize currency code."""
        currency = currency.upper()
        if currency not in CurrencyService.SUPPORTED_CURRENCIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported currency: {currency}",
            )
        return currency

    @staticmethod
    def get_current_exchange_rate(from_currency: str, to_currency: str) -> Decimal:
        """Get current exchange rate from external API with caching."""
        from_currency = CurrencyService.validate_currency_code(from_currency)
        to_currency = CurrencyService.validate_currency_code(to_currency)

        # Same currency
        if from_currency == to_currency:
            return Decimal("1.0")

        # Check cache first
        cache_key = f"exchange_rate:{from_currency}:{to_currency}"
        cached_rate = cache_service.get(cache_key)
        if cached_rate:
            logger.info(f"Using cached exchange rate for {from_currency}/{to_currency}")
            return Decimal(str(cached_rate))

        try:
            # Use yfinance to get exchange rate
            # Format: USDEUR=X for USD to EUR
            if from_currency == "USD":
                ticker_symbol = f"{from_currency}{to_currency}=X"
            elif to_currency == "USD":
                ticker_symbol = f"{from_currency}{to_currency}=X"
            else:
                # For non-USD pairs, convert through USD
                usd_from_rate = CurrencyService.get_current_exchange_rate(from_currency, "USD")
                usd_to_rate = CurrencyService.get_current_exchange_rate("USD", to_currency)
                rate = usd_from_rate * usd_to_rate
                
                # Cache the result
                cache_service.set(cache_key, float(rate), expire=900)  # 15 minutes
                return rate

            ticker = yf.Ticker(ticker_symbol)
            data = ticker.history(period="1d", interval="1d")
            
            if data.empty:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Exchange rate not available for {from_currency}/{to_currency}",
                )

            rate = Decimal(str(data["Close"].iloc[-1]))
            
            # Cache the result
            cache_service.set(cache_key, float(rate), expire=900)  # 15 minutes
            
            logger.info(f"Retrieved exchange rate {from_currency}/{to_currency}: {rate}")
            return rate

        except Exception as e:
            logger.error(f"Error fetching exchange rate {from_currency}/{to_currency}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Exchange rate service temporarily unavailable",
            )

    @staticmethod
    def convert_currency(
        amount: Decimal, from_currency: str, to_currency: str
    ) -> CurrencyConversion:
        """Convert amount from one currency to another."""
        rate = CurrencyService.get_current_exchange_rate(from_currency, to_currency)
        converted_amount = amount * rate

        return CurrencyConversion(
            from_currency=from_currency,
            to_currency=to_currency,
            from_amount=amount,
            to_amount=converted_amount,
            exchange_rate=rate,
            rate_date=datetime.now(timezone.utc),
        )

    @staticmethod
    def store_exchange_rate(
        db: Session, rate_data: ExchangeRateCreate
    ) -> HistoricalExchangeRate:
        """Store historical exchange rate."""
        from_currency = CurrencyService.validate_currency_code(rate_data.from_currency)
        to_currency = CurrencyService.validate_currency_code(rate_data.to_currency)

        # Check if rate already exists for this date
        existing = (
            db.query(HistoricalExchangeRate)
            .filter(
                and_(
                    HistoricalExchangeRate.from_currency == from_currency,
                    HistoricalExchangeRate.to_currency == to_currency,
                    func.date(HistoricalExchangeRate.date) == rate_data.date.date(),
                )
            )
            .first()
        )

        if existing:
            # Update existing rate
            existing.rate = rate_data.rate
            existing.date = rate_data.date
            db.commit()
            db.refresh(existing)
            logger.info(f"Updated exchange rate {from_currency}/{to_currency} for {rate_data.date}")
            return existing

        # Create new rate
        rate_entry = HistoricalExchangeRate(
            id=str(uuid.uuid4()),
            from_currency=from_currency,
            to_currency=to_currency,
            date=rate_data.date,
            rate=rate_data.rate,
            created_at=datetime.now(timezone.utc),
        )

        db.add(rate_entry)
        db.commit()
        db.refresh(rate_entry)

        logger.info(f"Stored exchange rate {from_currency}/{to_currency} for {rate_data.date}")
        return rate_entry

    @staticmethod
    def get_exchange_rate_history(
        db: Session,
        from_currency: str,
        to_currency: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> ExchangeRateHistory:
        """Get historical exchange rates."""
        from_currency = CurrencyService.validate_currency_code(from_currency)
        to_currency = CurrencyService.validate_currency_code(to_currency)

        query = db.query(HistoricalExchangeRate).filter(
            and_(
                HistoricalExchangeRate.from_currency == from_currency,
                HistoricalExchangeRate.to_currency == to_currency,
            )
        )

        if start_date:
            query = query.filter(HistoricalExchangeRate.date >= start_date)
        if end_date:
            query = query.filter(HistoricalExchangeRate.date <= end_date)

        rates = (
            query.order_by(desc(HistoricalExchangeRate.date))
            .limit(limit)
            .all()
        )

        return ExchangeRateHistory(
            from_currency=from_currency,
            to_currency=to_currency,
            rates=[ExchangeRate.model_validate(rate) for rate in rates],
            period_start=start_date,
            period_end=end_date,
        )

    @staticmethod
    def get_latest_exchange_rate(
        db: Session, from_currency: str, to_currency: str
    ) -> Optional[HistoricalExchangeRate]:
        """Get the latest stored exchange rate."""
        from_currency = CurrencyService.validate_currency_code(from_currency)
        to_currency = CurrencyService.validate_currency_code(to_currency)

        return (
            db.query(HistoricalExchangeRate)
            .filter(
                and_(
                    HistoricalExchangeRate.from_currency == from_currency,
                    HistoricalExchangeRate.to_currency == to_currency,
                )
            )
            .order_by(desc(HistoricalExchangeRate.date))
            .first()
        )


# Global service instance
currency_service = CurrencyService()