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


        # Validate transaction date (not in future)
        if transaction_data.transaction_date > datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction date cannot be in the future",
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

        # Calculate current quantity (all transaction types)
        current_quantity = Decimal(0)
        
        # Calculate average cost (BUY transactions only)
        total_buy_cost = Decimal(0)
        total_buy_quantity = Decimal(0)

        for transaction in transactions:
            # Calculate transaction cost in portfolio currency
            transaction_cost = (transaction.quantity * transaction.price_per_share) + (transaction.fees / transaction.exchange_rate)
            
            if transaction.type in [TransactionType.BUY, TransactionType.TRANSFER_IN]:
                # Add to position
                current_quantity += transaction.quantity
                # Add to cost basis (for average cost calculation)
                total_buy_cost += transaction_cost
                total_buy_quantity += transaction.quantity
            elif transaction.type in [TransactionType.SELL, TransactionType.TRANSFER_OUT]:
                # Reduce position
                current_quantity -= transaction.quantity
                # Don't modify cost basis - average cost based on BUY transactions only
            # Note: DIVIDEND and SPLIT transactions don't affect quantity or cost basis

        # Ensure we don't have negative quantities
        if current_quantity < 0:
            logger.warning(
                f"Negative quantity for holding {holding.symbol}: {current_quantity}"
            )
            current_quantity = Decimal(0)

        # Calculate average cost from BUY transactions only
        average_cost_per_share = (
            total_buy_cost / total_buy_quantity if total_buy_quantity > 0 else Decimal(0)
        )

        # Update holding with calculated values
        holding.current_quantity = current_quantity
        holding.average_cost_per_share = average_cost_per_share
        holding.updated_at = datetime.now(timezone.utc)

        logger.info(
            f"Updated holding {holding.symbol}: quantity={current_quantity}, "
            f"avg_cost={average_cost_per_share} (from {total_buy_quantity} buy shares costing {total_buy_cost})"
        )

    @staticmethod
    def calculate_and_update_transaction_metrics(db: Session, holding: Holding) -> None:
        """Update average_cost_per_share_at_transaction for all transactions in a holding."""
        transactions = (
            db.query(Transaction)
            .filter(Transaction.holding_id == holding.id)
            .order_by(Transaction.transaction_date, Transaction.created_at)
            .all()
        )

        # Track running totals to calculate average cost before each transaction
        running_buy_cost = Decimal(0)
        running_buy_quantity = Decimal(0)

        for transaction in transactions:
            # Calculate average cost BEFORE this transaction
            avg_cost_before = (
                running_buy_cost / running_buy_quantity 
                if running_buy_quantity > 0 
                else Decimal(0)
            )
            
            # Update the transaction's average_cost_per_share_at_transaction
            transaction.average_cost_per_share_at_transaction = avg_cost_before
            transaction.updated_at = datetime.now(timezone.utc)
            
            # Update running totals AFTER processing this transaction
            if transaction.type in [TransactionType.BUY, TransactionType.TRANSFER_IN]:
                transaction_cost = (transaction.quantity * transaction.price_per_share) + (transaction.fees / transaction.exchange_rate)
                running_buy_cost += transaction_cost
                running_buy_quantity += transaction.quantity

        logger.info(
            f"Updated average_cost_per_share_at_transaction for {len(transactions)} transactions in holding {holding.symbol}"
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
            fees=transaction_data.fees,
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
            fees=update_data.fees if update_data.fees is not None else transaction.fees,
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

    @staticmethod
    def recalculate_holding_metrics(
        db: Session, holding_id: str, user_id: str
    ) -> Holding:
        """Recalculate metrics for a specific holding and update transaction fields."""
        # Get holding with ownership verification
        holding = (
            db.query(Holding)
            .join(Portfolio)
            .filter(Holding.id == holding_id, Portfolio.user_id == user_id)
            .first()
        )

        if not holding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found"
            )

        # Recalculate holding metrics
        TransactionService.calculate_holding_metrics(db, holding)
        
        # Update transaction average_cost_per_share_at_transaction fields
        TransactionService.calculate_and_update_transaction_metrics(db, holding)
        
        db.commit()
        db.refresh(holding)

        logger.info(f"Recalculated metrics for holding {holding_id}")
        return holding

    @staticmethod
    def recalculate_portfolio_metrics(
        db: Session, portfolio_id: str, user_id: str
    ) -> List[Holding]:
        """Recalculate metrics for all holdings in a portfolio and update transaction fields."""
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

        # Get all holdings in the portfolio
        holdings = (
            db.query(Holding)
            .filter(Holding.portfolio_id == portfolio_id)
            .all()
        )

        # Recalculate metrics for each holding
        for holding in holdings:
            TransactionService.calculate_holding_metrics(db, holding)
            TransactionService.calculate_and_update_transaction_metrics(db, holding)

        db.commit()

        # Refresh all holdings
        for holding in holdings:
            db.refresh(holding)

        logger.info(
            f"Recalculated metrics for {len(holdings)} holdings in portfolio {portfolio_id}"
        )
        return holdings

    @staticmethod
    def recalculate_all_user_metrics(db: Session, user_id: str) -> int:
        """Recalculate metrics for all holdings belonging to a user and update transaction fields."""
        # Get all holdings for the user
        holdings = (
            db.query(Holding)
            .join(Portfolio)
            .filter(Portfolio.user_id == user_id)
            .all()
        )

        # Recalculate metrics for each holding
        for holding in holdings:
            TransactionService.calculate_holding_metrics(db, holding)
            TransactionService.calculate_and_update_transaction_metrics(db, holding)

        db.commit()

        # Refresh all holdings
        for holding in holdings:
            db.refresh(holding)

        logger.info(f"Recalculated metrics for {len(holdings)} holdings for user {user_id}")
        return len(holdings)


# Global service instance
transaction_service = TransactionService()
