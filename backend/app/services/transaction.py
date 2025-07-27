"""Transaction service for portfolio management."""

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.portfolio import Holding, Portfolio, Transaction, TransactionType
from app.schemas.portfolio import TransactionCreate, TransactionUpdate

logger = logging.getLogger(__name__)


class TransactionService:
    """Service for transaction operations."""

    @staticmethod
    def validate_transaction_data(transaction_data: TransactionCreate) -> None:
        """Validate transaction data for business rules."""
        # Ensure positive values for quantity and price
        if transaction_data.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction quantity must be positive",
            )

        if transaction_data.price_per_share <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price per share must be positive",
            )

        # Validate total amount consistency
        expected_total = (
            transaction_data.quantity * transaction_data.price_per_share
        ) + transaction_data.fees
        if abs(expected_total - transaction_data.total_amount) > Decimal("0.01"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Total amount {transaction_data.total_amount} doesn't match calculated value {expected_total}",
            )

        # Validate transaction date (not in future)
        if transaction_data.transaction_date > datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction date cannot be in the future",
            )

        # Validate currency code format
        if len(transaction_data.currency) != 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Currency must be a 3-letter code (e.g., USD, EUR)",
            )

        # Validate exchange rate
        if transaction_data.exchange_rate <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exchange rate must be positive",
            )

    @staticmethod
    def get_or_create_holding(
        db: Session, portfolio_id: str, symbol: str, name: Optional[str] = None
    ) -> Holding:
        """Get existing holding or create new one for the symbol."""
        # Check if holding already exists
        holding = (
            db.query(Holding)
            .filter(
                Holding.portfolio_id == portfolio_id, Holding.symbol == symbol.upper()
            )
            .first()
        )

        if holding:
            return holding

        # Create new holding
        holding = Holding(
            id=str(uuid.uuid4()),
            portfolio_id=portfolio_id,
            symbol=symbol.upper(),
            name=name or symbol.upper(),
            current_quantity=Decimal(0),
            average_cost_per_share=Decimal(0),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        db.add(holding)
        db.flush()  # Flush to get the ID without committing
        logger.info(f"Created new holding for {symbol} in portfolio {portfolio_id}")

        return holding

    @staticmethod
    def calculate_holding_metrics(db: Session, holding: Holding) -> None:
        """Recalculate holding metrics based on all transactions."""
        transactions = (
            db.query(Transaction)
            .filter(Transaction.holding_id == holding.id)
            .order_by(Transaction.transaction_date)
            .all()
        )

        total_quantity = Decimal(0)
        total_cost = Decimal(0)

        for transaction in transactions:
            if transaction.type == TransactionType.BUY:
                # Add to position
                total_cost += transaction.total_amount * transaction.exchange_rate
                total_quantity += transaction.quantity
            elif transaction.type == TransactionType.SELL:
                # Reduce position (FIFO basis for cost calculation)
                if total_quantity > 0:
                    # Calculate current average cost
                    current_avg_cost = (
                        total_cost / total_quantity
                        if total_quantity > 0
                        else Decimal(0)
                    )

                    # Reduce cost basis proportionally
                    cost_reduction = current_avg_cost * transaction.quantity
                    total_cost -= cost_reduction
                    total_quantity -= transaction.quantity

                    # Ensure we don't go negative
                    if total_quantity < 0:
                        logger.warning(
                            f"Negative quantity for holding {holding.symbol}: {total_quantity}"
                        )
                        total_quantity = Decimal(0)
                        total_cost = Decimal(0)

        # Update holding with calculated values
        holding.current_quantity = total_quantity
        holding.average_cost_per_share = (
            total_cost / total_quantity if total_quantity > 0 else Decimal(0)
        )
        holding.updated_at = datetime.now(timezone.utc)

        logger.info(
            f"Updated holding {holding.symbol}: quantity={total_quantity}, "
            f"avg_cost={holding.average_cost_per_share}"
        )

    @staticmethod
    def create_transaction(
        db: Session,
        portfolio_id: str,
        transaction_data: TransactionCreate,
        user_id: str,
    ) -> Transaction:
        """Create a new transaction."""
        # Verify portfolio ownership
        portfolio = (
            db.query(Portfolio)
            .filter(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
            .first()
        )

        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found"
            )

        # Validate transaction data
        TransactionService.validate_transaction_data(transaction_data)

        # Get or create holding
        holding = TransactionService.get_or_create_holding(
            db, portfolio_id, transaction_data.symbol, transaction_data.symbol
        )

        # Calculate average cost per share at transaction (before this transaction)
        avg_cost_at_transaction = holding.average_cost_per_share

        # Create transaction
        transaction = Transaction(
            id=str(uuid.uuid4()),
            holding_id=holding.id,
            type=transaction_data.type,
            quantity=transaction_data.quantity,
            price_per_share=transaction_data.price_per_share,
            total_amount=transaction_data.total_amount,
            fees=transaction_data.fees,
            currency=transaction_data.currency,
            exchange_rate=transaction_data.exchange_rate,
            average_cost_per_share_at_transaction=avg_cost_at_transaction,
            notes=transaction_data.notes,
            transaction_date=transaction_data.transaction_date,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        db.add(transaction)
        db.flush()

        # Recalculate holding metrics
        TransactionService.calculate_holding_metrics(db, holding)

        db.commit()
        db.refresh(transaction)

        logger.info(
            f"Created transaction {transaction.id} for {transaction_data.symbol}"
        )
        return transaction

    @staticmethod
    def update_transaction(
        db: Session, transaction_id: str, update_data: TransactionUpdate, user_id: str
    ) -> Transaction:
        """Update an existing transaction."""
        # Get transaction with ownership verification
        transaction = (
            db.query(Transaction)
            .join(Holding)
            .join(Portfolio)
            .filter(Transaction.id == transaction_id, Portfolio.user_id == user_id)
            .first()
        )

        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
            )

        # Store original values for validation
        original_data = TransactionCreate(
            symbol="",  # Not needed for validation
            type=update_data.type or transaction.type,
            quantity=update_data.quantity or transaction.quantity,
            price_per_share=update_data.price_per_share or transaction.price_per_share,
            total_amount=update_data.total_amount or transaction.total_amount,
            fees=update_data.fees if update_data.fees is not None else transaction.fees,
            currency=update_data.currency or transaction.currency,
            exchange_rate=update_data.exchange_rate or transaction.exchange_rate,
            notes=update_data.notes,
            transaction_date=update_data.transaction_date
            or transaction.transaction_date,
        )

        # Validate updated data
        TransactionService.validate_transaction_data(original_data)

        # Update transaction fields
        for field, value in update_data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(transaction, field, value)

        transaction.updated_at = datetime.now(timezone.utc)

        # Recalculate holding metrics
        TransactionService.calculate_holding_metrics(db, transaction.holding)

        db.commit()
        db.refresh(transaction)

        logger.info(f"Updated transaction {transaction_id}")
        return transaction

    @staticmethod
    def delete_transaction(db: Session, transaction_id: str, user_id: str) -> bool:
        """Delete a transaction."""
        # Get transaction with ownership verification
        transaction = (
            db.query(Transaction)
            .join(Holding)
            .join(Portfolio)
            .filter(Transaction.id == transaction_id, Portfolio.user_id == user_id)
            .first()
        )

        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
            )

        holding = transaction.holding

        # Delete transaction
        db.delete(transaction)

        # Recalculate holding metrics
        TransactionService.calculate_holding_metrics(db, holding)

        # If holding has no more transactions and zero quantity, optionally delete it
        remaining_transactions = (
            db.query(Transaction).filter(Transaction.holding_id == holding.id).count()
        )

        if remaining_transactions == 0 and holding.current_quantity == 0:
            logger.info(f"Deleting empty holding {holding.symbol}")
            db.delete(holding)

        db.commit()

        logger.info(f"Deleted transaction {transaction_id}")
        return True

    @staticmethod
    def get_portfolio_transactions(
        db: Session, portfolio_id: str, user_id: str, limit: int = 100, offset: int = 0
    ) -> List[Transaction]:
        """Get all transactions for a portfolio."""
        # Verify portfolio ownership
        portfolio = (
            db.query(Portfolio)
            .filter(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
            .first()
        )

        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found"
            )

        transactions = (
            db.query(Transaction)
            .join(Holding)
            .filter(Holding.portfolio_id == portfolio_id)
            .order_by(Transaction.transaction_date.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return transactions


# Global service instance
transaction_service = TransactionService()
