"""Portfolio service."""

import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.portfolio import Holding, Portfolio, Transaction
from app.schemas.portfolio import PortfolioCreate, PortfolioUpdate, TransactionCreate


def create_portfolio(
    db: Session, portfolio: PortfolioCreate, user_id: str
) -> Portfolio:
    """Create a new portfolio."""
    # Get the next order value
    max_order = db.query(Portfolio).filter(Portfolio.user_id == user_id).count()

    db_portfolio = Portfolio(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=portfolio.name,
        description=portfolio.description,
        currency=portfolio.currency,
        order=max_order,
    )
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio


def get_portfolios(db: Session, user_id: str) -> List[Portfolio]:
    """Get all portfolios for a user."""
    return (
        db.query(Portfolio)
        .filter(Portfolio.user_id == user_id)
        .order_by(Portfolio.order)
        .all()
    )


def get_portfolio(db: Session, portfolio_id: str, user_id: str) -> Optional[Portfolio]:
    """Get a specific portfolio by ID."""
    return (
        db.query(Portfolio)
        .filter(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
        .first()
    )


def update_portfolio(
    db: Session, portfolio_id: str, user_id: str, portfolio_update: PortfolioUpdate
) -> Optional[Portfolio]:
    """Update a portfolio."""
    db_portfolio = get_portfolio(db, portfolio_id, user_id)
    if not db_portfolio:
        return None

    update_data = portfolio_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_portfolio, field, value)

    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio


def delete_portfolio(db: Session, portfolio_id: str, user_id: str) -> bool:
    """Delete a portfolio."""
    db_portfolio = get_portfolio(db, portfolio_id, user_id)
    if not db_portfolio:
        return False

    db.delete(db_portfolio)
    db.commit()
    return True


def get_holdings(db: Session, portfolio_id: str, user_id: str) -> List[Holding]:
    """Get all holdings for a portfolio."""
    # First verify the portfolio belongs to the user
    portfolio = get_portfolio(db, portfolio_id, user_id)
    if not portfolio:
        return []

    return db.query(Holding).filter(Holding.portfolio_id == portfolio_id).all()


def get_holding(db: Session, holding_id: str, user_id: str) -> Optional[Holding]:
    """Get a specific holding by ID."""
    return (
        db.query(Holding)
        .join(Portfolio)
        .filter(Holding.id == holding_id, Portfolio.user_id == user_id)
        .first()
    )


def create_transaction(
    db: Session, transaction: TransactionCreate, portfolio_id: str, user_id: str
) -> Optional[Transaction]:
    """Create a new transaction."""
    # Verify portfolio belongs to user
    portfolio = get_portfolio(db, portfolio_id, user_id)
    if not portfolio:
        return None

    # Get or create holding
    holding = (
        db.query(Holding)
        .filter(
            Holding.portfolio_id == portfolio_id, Holding.symbol == transaction.symbol
        )
        .first()
    )

    if not holding:
        holding = Holding(
            id=str(uuid.uuid4()),
            portfolio_id=portfolio_id,
            symbol=transaction.symbol,
            current_quantity=Decimal(0),
            average_cost_per_share=Decimal(0),
        )
        db.add(holding)
        db.flush()  # Flush to get the holding ID

    # Calculate new average cost per share
    current_quantity = holding.current_quantity
    current_avg_cost = holding.average_cost_per_share
    transaction_quantity = transaction.quantity
    transaction_price = transaction.price_per_share

    if transaction.type in ["BUY", "TRANSFER_IN"]:
        new_quantity = current_quantity + transaction_quantity
        if new_quantity > 0:
            new_avg_cost = (
                (current_quantity * current_avg_cost)
                + (transaction_quantity * transaction_price)
            ) / new_quantity
        else:
            new_avg_cost = Decimal(0)
    elif transaction.type in ["SELL", "TRANSFER_OUT"]:
        new_quantity = current_quantity - transaction_quantity
        new_avg_cost = current_avg_cost  # Keep the same average cost
    else:
        # For dividends and splits, quantity might not change
        new_quantity = current_quantity
        new_avg_cost = current_avg_cost

    # Create transaction
    db_transaction = Transaction(
        id=str(uuid.uuid4()),
        holding_id=holding.id,
        type=transaction.type,
        quantity=transaction.quantity,
        price_per_share=transaction.price_per_share,
        total_amount=transaction.total_amount,
        fees=transaction.fees,
        currency=transaction.currency,
        exchange_rate=transaction.exchange_rate,
        notes=transaction.notes,
        transaction_date=transaction.transaction_date,
        average_cost_per_share_at_transaction=current_avg_cost,
    )

    # Update holding
    holding.current_quantity = new_quantity
    holding.average_cost_per_share = new_avg_cost

    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    return db_transaction
