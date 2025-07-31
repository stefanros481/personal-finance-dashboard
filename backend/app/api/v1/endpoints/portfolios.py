"""Portfolio endpoints."""

import logging
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.schemas.portfolio import (
    Holding,
    Portfolio,
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioWithHoldings,
)
from app.services.portfolio import (
    create_portfolio,
    delete_portfolio,
    get_holdings,
    get_portfolio,
    get_portfolios,
    update_portfolio,
)
from app.services.transaction import transaction_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=Portfolio, status_code=status.HTTP_201_CREATED)
async def create_user_portfolio(
    portfolio: PortfolioCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Create a new portfolio."""
    return create_portfolio(db, portfolio, current_user.id)


@router.get("/", response_model=List[Portfolio])
async def read_portfolios(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Get all portfolios for the current user."""
    return get_portfolios(db, current_user.id)


@router.get("/{portfolio_id}", response_model=PortfolioWithHoldings)
async def read_portfolio(
    portfolio_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Get a specific portfolio with holdings."""
    portfolio = get_portfolio(db, portfolio_id, current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found"
        )

    # Get holdings for this portfolio
    holdings = get_holdings(db, portfolio_id, current_user.id)

    # Convert to response model
    portfolio_dict = portfolio.__dict__.copy()
    portfolio_dict["holdings"] = holdings

    return PortfolioWithHoldings(**portfolio_dict)


@router.put("/{portfolio_id}", response_model=Portfolio)
async def update_user_portfolio(
    portfolio_id: str,
    portfolio_update: PortfolioUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Update a portfolio."""
    portfolio = update_portfolio(db, portfolio_id, current_user.id, portfolio_update)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found"
        )
    return portfolio


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_portfolio(
    portfolio_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Delete a portfolio."""
    success = delete_portfolio(db, portfolio_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found"
        )


@router.get("/{portfolio_id}/holdings", response_model=List[Holding])
async def read_portfolio_holdings(
    portfolio_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Get all holdings for a portfolio."""
    holdings = get_holdings(db, portfolio_id, current_user.id)
    return holdings


@router.post("/{portfolio_id}/holdings/{holding_id}/recalculate", response_model=Holding)
async def recalculate_holding_metrics(
    portfolio_id: str,
    holding_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Recalculate average cost and quantity metrics for a specific holding.
    
    This endpoint is useful when you need to fix metrics after correcting
    transaction data or when metrics appear incorrect.
    """
    try:
        holding = transaction_service.recalculate_holding_metrics(
            db=db, holding_id=holding_id, user_id=current_user.id
        )
        logger.info(f"Recalculated metrics for holding {holding_id} in portfolio {portfolio_id}")
        return holding
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recalculating holding metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to recalculate holding metrics",
        )


@router.post("/{portfolio_id}/recalculate", response_model=List[Holding])
async def recalculate_portfolio_metrics(
    portfolio_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Recalculate average cost and quantity metrics for all holdings in a portfolio.
    
    This endpoint recalculates metrics for all holdings within the specified
    portfolio, ensuring all calculations are based on current transaction data.
    """
    try:
        holdings = transaction_service.recalculate_portfolio_metrics(
            db=db, portfolio_id=portfolio_id, user_id=current_user.id
        )
        logger.info(f"Recalculated metrics for portfolio {portfolio_id}")
        return holdings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recalculating portfolio metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to recalculate portfolio metrics",
        )
