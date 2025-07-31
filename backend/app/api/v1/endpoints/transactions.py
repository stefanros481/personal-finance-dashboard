"""Transaction management endpoints."""

import logging
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.schemas.portfolio import Holding, Transaction, TransactionCreate, TransactionUpdate
from app.schemas.user import User
from app.services.transaction import transaction_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/portfolios/{portfolio_id}/transactions",
    response_model=Transaction,
    status_code=status.HTTP_201_CREATED,
)
async def create_transaction(
    portfolio_id: str,
    transaction_data: TransactionCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Create a new transaction in a portfolio.

    This endpoint allows you to add buy, sell, dividend, or other transactions
    to a portfolio. The system will automatically:
    - Create holdings if they don't exist
    - Recalculate holding quantities and average costs
    - Validate transaction data for consistency
    """
    try:
        transaction = transaction_service.create_transaction(
            db=db,
            portfolio_id=portfolio_id,
            transaction_data=transaction_data,
            user_id=current_user.id,
        )

        logger.info(
            f"Created transaction {transaction.id} for user {current_user.email}"
        )
        return transaction

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create transaction",
        )


@router.get("/portfolios/{portfolio_id}/transactions", response_model=List[Transaction])
async def get_portfolio_transactions(
    portfolio_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    limit: int = Query(
        default=100, ge=1, le=1000, description="Number of transactions to return"
    ),
    offset: int = Query(default=0, ge=0, description="Number of transactions to skip"),
):
    """
    Get all transactions for a portfolio.

    Returns transactions ordered by date (most recent first).
    Supports pagination through limit and offset parameters.
    """
    try:
        transactions = transaction_service.get_portfolio_transactions(
            db=db,
            portfolio_id=portfolio_id,
            user_id=current_user.id,
            limit=limit,
            offset=offset,
        )

        logger.info(
            f"Retrieved {len(transactions)} transactions for portfolio {portfolio_id}"
        )
        return transactions

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving transactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transactions",
        )


@router.put("/transactions/{transaction_id}", response_model=Transaction)
async def update_transaction(
    transaction_id: str,
    update_data: TransactionUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Update an existing transaction.

    Only the fields provided in the request will be updated.
    The system will recalculate holding metrics after the update.
    """
    try:
        transaction = transaction_service.update_transaction(
            db=db,
            transaction_id=transaction_id,
            update_data=update_data,
            user_id=current_user.id,
        )

        logger.info(
            f"Updated transaction {transaction_id} for user {current_user.email}"
        )
        return transaction

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update transaction",
        )


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Delete a transaction.

    This will recalculate holding metrics after deletion.
    If the holding has no remaining transactions and zero quantity,
    the holding itself may be deleted.
    """
    try:
        transaction_service.delete_transaction(
            db=db, transaction_id=transaction_id, user_id=current_user.id
        )

        logger.info(
            f"Deleted transaction {transaction_id} for user {current_user.email}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete transaction",
        )


@router.post("/portfolios/{portfolio_id}/holdings/{holding_id}/recalculate", response_model=Holding)
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


@router.post("/portfolios/{portfolio_id}/recalculate", response_model=List[Holding])
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


@router.post("/recalculate-all")
async def recalculate_all_user_metrics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Recalculate average cost and quantity metrics for all user holdings.
    
    This endpoint recalculates metrics for all holdings across all portfolios
    belonging to the current user. Use this when you need to fix all metrics
    after a system-wide calculation change.
    """
    try:
        holdings_count = transaction_service.recalculate_all_user_metrics(
            db=db, user_id=current_user.id
        )
        logger.info(f"Recalculated metrics for all user holdings")
        return {
            "message": f"Successfully recalculated metrics for {holdings_count} holdings",
            "holdings_updated": holdings_count,
        }
    except Exception as e:
        logger.error(f"Error recalculating all user metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to recalculate all user metrics",
        )
