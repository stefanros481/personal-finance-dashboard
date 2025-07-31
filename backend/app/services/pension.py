"""Pension service for managing pension accounts and value entries."""

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.pension import PensionAccount, PensionValueEntry
from app.models.user import User
from app.schemas.pension import (
    PensionAccountCreate,
    PensionAccountUpdate,
    PensionSummary,
    PensionValueEntryCreate,
    PensionValueEntryUpdate,
)

logger = logging.getLogger(__name__)


class PensionService:
    """Service for pension operations."""

    @staticmethod
    def create_account(
        db: Session, account_data: PensionAccountCreate, user_id: str
    ) -> PensionAccount:
        """Create a new pension account."""
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Check for duplicate names for the user
        existing = (
            db.query(PensionAccount)
            .filter(
                PensionAccount.user_id == user_id,
                PensionAccount.name == account_data.name,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pension account with this name already exists",
            )

        # Create pension account
        account = PensionAccount(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=account_data.name,
            provider=account_data.provider,
            currency=account_data.currency,
            description=account_data.description,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        db.add(account)
        db.commit()
        db.refresh(account)

        logger.info(f"Created pension account {account.id} for user {user_id}")
        return account

    @staticmethod
    def get_accounts(db: Session, user_id: str) -> List[PensionAccount]:
        """Get all pension accounts for a user."""
        accounts = (
            db.query(PensionAccount)
            .filter(PensionAccount.user_id == user_id)
            .order_by(PensionAccount.name)
            .all()
        )
        return accounts

    @staticmethod
    def get_account(db: Session, account_id: str, user_id: str) -> PensionAccount:
        """Get a specific pension account."""
        account = (
            db.query(PensionAccount)
            .filter(
                PensionAccount.id == account_id, PensionAccount.user_id == user_id
            )
            .first()
        )

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pension account not found",
            )

        return account

    @staticmethod
    def update_account(
        db: Session,
        account_id: str,
        update_data: PensionAccountUpdate,
        user_id: str,
    ) -> PensionAccount:
        """Update a pension account."""
        account = PensionService.get_account(db, account_id, user_id)

        # Check for duplicate names if name is being updated
        if update_data.name and update_data.name != account.name:
            existing = (
                db.query(PensionAccount)
                .filter(
                    PensionAccount.user_id == user_id,
                    PensionAccount.name == update_data.name,
                    PensionAccount.id != account_id,
                )
                .first()
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Pension account with this name already exists",
                )

        # Update fields
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(account, field, value)

        account.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(account)

        logger.info(f"Updated pension account {account_id}")
        return account

    @staticmethod
    def delete_account(db: Session, account_id: str, user_id: str) -> bool:
        """Delete a pension account."""
        account = PensionService.get_account(db, account_id, user_id)

        db.delete(account)
        db.commit()

        logger.info(f"Deleted pension account {account_id}")
        return True

    @staticmethod
    def create_value_entry(
        db: Session,
        account_id: str,
        entry_data: PensionValueEntryCreate,
        user_id: str,
    ) -> PensionValueEntry:
        """Create a new value entry for a pension account."""
        # Verify account ownership
        account = PensionService.get_account(db, account_id, user_id)

        # Check for duplicate entries on the same date
        existing = (
            db.query(PensionValueEntry)
            .filter(
                PensionValueEntry.account_id == account_id,
                func.date(PensionValueEntry.entry_date)
                == entry_data.entry_date.date(),
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Value entry already exists for this date",
            )

        # Validate entry date (not in future)
        if entry_data.entry_date > datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Entry date cannot be in the future",
            )

        # Create value entry
        entry = PensionValueEntry(
            id=str(uuid.uuid4()),
            account_id=account_id,
            value=entry_data.value,
            contributions=entry_data.contributions,
            entry_date=entry_data.entry_date,
            notes=entry_data.notes,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        db.add(entry)
        db.commit()
        db.refresh(entry)

        logger.info(f"Created value entry {entry.id} for account {account_id}")
        return entry

    @staticmethod
    def get_value_entries(
        db: Session,
        account_id: str,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[PensionValueEntry]:
        """Get value entries for a pension account."""
        # Verify account ownership
        PensionService.get_account(db, account_id, user_id)

        entries = (
            db.query(PensionValueEntry)
            .filter(PensionValueEntry.account_id == account_id)
            .order_by(desc(PensionValueEntry.entry_date))
            .offset(offset)
            .limit(limit)
            .all()
        )

        return entries

    @staticmethod
    def update_value_entry(
        db: Session,
        entry_id: str,
        update_data: PensionValueEntryUpdate,
        user_id: str,
    ) -> PensionValueEntry:
        """Update a value entry."""
        # Get entry with ownership verification
        entry = (
            db.query(PensionValueEntry)
            .join(PensionAccount)
            .filter(
                PensionValueEntry.id == entry_id, PensionAccount.user_id == user_id
            )
            .first()
        )

        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Value entry not found"
            )

        # Check for duplicate entries on the same date if date is being updated
        if update_data.entry_date and update_data.entry_date != entry.entry_date:
            existing = (
                db.query(PensionValueEntry)
                .filter(
                    PensionValueEntry.account_id == entry.account_id,
                    func.date(PensionValueEntry.entry_date)
                    == update_data.entry_date.date(),
                    PensionValueEntry.id != entry_id,
                )
                .first()
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Value entry already exists for this date",
                )

            # Validate new date (not in future)
            if update_data.entry_date > datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Entry date cannot be in the future",
                )

        # Update fields
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(entry, field, value)

        entry.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(entry)

        logger.info(f"Updated value entry {entry_id}")
        return entry

    @staticmethod
    def delete_value_entry(db: Session, entry_id: str, user_id: str) -> bool:
        """Delete a value entry."""
        # Get entry with ownership verification
        entry = (
            db.query(PensionValueEntry)
            .join(PensionAccount)
            .filter(
                PensionValueEntry.id == entry_id, PensionAccount.user_id == user_id
            )
            .first()
        )

        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Value entry not found"
            )

        db.delete(entry)
        db.commit()

        logger.info(f"Deleted value entry {entry_id}")
        return True

    @staticmethod
    def get_account_summary(
        db: Session, account_id: str, user_id: str
    ) -> PensionSummary:
        """Get summary statistics for a pension account."""
        account = PensionService.get_account(db, account_id, user_id)

        # Get latest value entry
        latest_entry = (
            db.query(PensionValueEntry)
            .filter(PensionValueEntry.account_id == account_id)
            .order_by(desc(PensionValueEntry.entry_date))
            .first()
        )

        # Calculate total contributions
        total_contributions = (
            db.query(func.sum(PensionValueEntry.contributions))
            .filter(PensionValueEntry.account_id == account_id)
            .scalar()
            or Decimal(0)
        )

        # Count entries
        entries_count = (
            db.query(func.count(PensionValueEntry.id))
            .filter(PensionValueEntry.account_id == account_id)
            .scalar()
            or 0
        )

        # Calculate growth
        latest_value = latest_entry.value if latest_entry else None
        total_growth = None
        growth_percentage = None

        if latest_value and total_contributions:
            total_growth = latest_value - total_contributions
            if total_contributions > 0:
                growth_percentage = (total_growth / total_contributions) * 100

        return PensionSummary(
            account=account,
            latest_value=latest_value,
            total_contributions=total_contributions,
            total_growth=total_growth,
            growth_percentage=growth_percentage,
            entries_count=entries_count,
        )


# Global service instance
pension_service = PensionService()