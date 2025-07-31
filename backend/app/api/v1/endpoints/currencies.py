"""Currency and exchange rate endpoints."""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.schemas.currency import (
    CurrencyConversion,
    ExchangeRate,
    ExchangeRateCreate,
    ExchangeRateHistory,
    SupportedCurrencies,
)
from app.schemas.user import User
from app.services.currency import currency_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/currencies", response_model=SupportedCurrencies)
async def get_supported_currencies():
    """
    Get list of supported currencies.
    
    Returns information about all supported currencies including:
    - Currency code (ISO 4217)
    - Full name
    - Symbol
    - Decimal places for display
    """
    try:
        currencies = currency_service.get_supported_currencies()
        logger.info("Retrieved supported currencies list")
        return currencies
    except Exception as e:
        logger.error(f"Error retrieving supported currencies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve supported currencies",
        )


@router.get("/currencies/convert", response_model=CurrencyConversion)
async def convert_currency(
    amount: Decimal = Query(..., description="Amount to convert"),
    from_currency: str = Query(..., description="Source currency code (e.g., USD)"),
    to_currency: str = Query(..., description="Target currency code (e.g., EUR)"),
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
):
    """
    Convert amount from one currency to another using current exchange rates.
    
    - **amount**: Amount to convert (decimal)
    - **from_currency**: Source currency code (ISO 4217)
    - **to_currency**: Target currency code (ISO 4217)
    
    Returns the converted amount along with the exchange rate used.
    Exchange rates are cached for 15 minutes for performance.
    """
    try:
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be positive",
            )

        conversion = currency_service.convert_currency(amount, from_currency, to_currency)
        logger.info(
            f"Converted {amount} {from_currency} to {conversion.to_amount} {to_currency}"
        )
        return conversion
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting currency: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to convert currency",
        )


@router.get("/currencies/rates/current")
async def get_current_exchange_rate(
    from_currency: str = Query(..., description="Source currency code"),
    to_currency: str = Query(..., description="Target currency code"),
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
):
    """
    Get current exchange rate between two currencies.
    
    Returns the current exchange rate from external market data.
    Results are cached for 15 minutes.
    """
    try:
        rate = currency_service.get_current_exchange_rate(from_currency, to_currency)
        return {
            "from_currency": from_currency.upper(),
            "to_currency": to_currency.upper(),
            "rate": rate,
            "timestamp": datetime.utcnow(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching current exchange rate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch current exchange rate",
        )


@router.post("/currencies/rates", response_model=ExchangeRate, status_code=status.HTTP_201_CREATED)
async def store_exchange_rate(
    rate_data: ExchangeRateCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Store a historical exchange rate.
    
    This endpoint allows storing historical exchange rates for record keeping.
    Useful for importing historical data or recording specific rates.
    
    - **from_currency**: Source currency code
    - **to_currency**: Target currency code  
    - **rate**: Exchange rate value
    - **date**: Date of the exchange rate
    """
    try:
        if rate_data.rate <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exchange rate must be positive",
            )

        if rate_data.date > datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exchange rate date cannot be in the future",
            )

        stored_rate = currency_service.store_exchange_rate(db, rate_data)
        result = ExchangeRate.model_validate(stored_rate)
        
        logger.info(
            f"Stored exchange rate {rate_data.from_currency}/{rate_data.to_currency} "
            f"for {rate_data.date}"
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing exchange rate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store exchange rate",
        )


@router.get("/currencies/rates/history", response_model=ExchangeRateHistory)
async def get_exchange_rate_history(
    from_currency: str = Query(..., description="Source currency code"),
    to_currency: str = Query(..., description="Target currency code"),
    start_date: Optional[datetime] = Query(None, description="Start date for history"),
    end_date: Optional[datetime] = Query(None, description="End date for history"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of rates to return"),
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
):
    """
    Get historical exchange rates between two currencies.
    
    Returns stored historical exchange rates, ordered by date (most recent first).
    
    - **from_currency**: Source currency code
    - **to_currency**: Target currency code
    - **start_date**: Optional start date for filtering (ISO format)
    - **end_date**: Optional end date for filtering (ISO format)
    - **limit**: Maximum number of rates to return (1-1000)
    """
    try:
        history = currency_service.get_exchange_rate_history(
            db=db,
            from_currency=from_currency,
            to_currency=to_currency,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        
        logger.info(
            f"Retrieved {len(history.rates)} historical rates for "
            f"{from_currency}/{to_currency}"
        )
        return history
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving exchange rate history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve exchange rate history",
        )


@router.get("/currencies/rates/latest")
async def get_latest_stored_rate(
    from_currency: str = Query(..., description="Source currency code"),
    to_currency: str = Query(..., description="Target currency code"),
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
):
    """
    Get the latest stored exchange rate between two currencies.
    
    Returns the most recent stored exchange rate from the database.
    This may be different from the current market rate.
    """
    try:
        latest_rate = currency_service.get_latest_exchange_rate(
            db=db, from_currency=from_currency, to_currency=to_currency
        )
        
        if not latest_rate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No stored rates found for {from_currency}/{to_currency}",
            )

        result = ExchangeRate.model_validate(latest_rate)
        logger.info(f"Retrieved latest stored rate for {from_currency}/{to_currency}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving latest stored rate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve latest stored rate",
        )