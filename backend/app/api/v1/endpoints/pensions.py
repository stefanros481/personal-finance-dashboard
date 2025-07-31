"""Pension management endpoints."""

import logging
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.schemas.pension import (
    PensionAccount,
    PensionAccountCreate,
    PensionAccountUpdate,
    PensionAccountWithEntries,
    PensionSummary,
    PensionValueEntry,
    PensionValueEntryCreate,
    PensionValueEntryUpdate,
)
from app.schemas.user import User
from app.services.pension import pension_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/pensions", response_model=PensionAccount, status_code=status.HTTP_201_CREATED)
async def create_pension_account(
    account_data: PensionAccountCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Create a new pension account.
    
    - **name**: Unique name for the pension account
    - **provider**: Pension provider name (optional)
    - **currency**: Currency code (default: USD)
    - **description**: Additional notes about the account
    """
    try:
        account = pension_service.create_account(
            db=db, account_data=account_data, user_id=current_user.id
        )
        logger.info(f"Created pension account {account.id} for user {current_user.email}")
        return account
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating pension account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create pension account",
        )


@router.get("/pensions", response_model=List[PensionAccount])
async def get_pension_accounts(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Get all pension accounts for the current user."""
    try:
        accounts = pension_service.get_accounts(db=db, user_id=current_user.id)
        logger.info(f"Retrieved {len(accounts)} pension accounts for user {current_user.email}")
        return accounts
    except Exception as e:
        logger.error(f"Error retrieving pension accounts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pension accounts",
        )


@router.get("/pensions/{account_id}", response_model=PensionAccountWithEntries)
async def get_pension_account(
    account_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    include_entries: bool = Query(default=False, description="Include value entries"),
):
    """
    Get a specific pension account.
    
    - **include_entries**: If true, includes all value entries for the account
    """
    try:
        account = pension_service.get_account(
            db=db, account_id=account_id, user_id=current_user.id
        )
        
        result = PensionAccountWithEntries.model_validate(account)
        
        if include_entries:
            entries = pension_service.get_value_entries(
                db=db, account_id=account_id, user_id=current_user.id, limit=1000
            )
            result.value_entries = entries
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving pension account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pension account",
        )


@router.get("/pensions/{account_id}/summary", response_model=PensionSummary)
async def get_pension_account_summary(
    account_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Get summary statistics for a pension account.
    
    Returns:
    - Latest value
    - Total contributions
    - Total growth amount and percentage
    - Number of value entries
    """
    try:
        summary = pension_service.get_account_summary(
            db=db, account_id=account_id, user_id=current_user.id
        )
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving pension summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pension summary",
        )


@router.put("/pensions/{account_id}", response_model=PensionAccount)
async def update_pension_account(
    account_id: str,
    update_data: PensionAccountUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Update a pension account."""
    try:
        account = pension_service.update_account(
            db=db,
            account_id=account_id,
            update_data=update_data,
            user_id=current_user.id,
        )
        logger.info(f"Updated pension account {account_id} for user {current_user.email}")
        return account
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating pension account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update pension account",
        )


@router.delete("/pensions/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pension_account(
    account_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Delete a pension account and all its value entries."""
    try:
        pension_service.delete_account(
            db=db, account_id=account_id, user_id=current_user.id
        )
        logger.info(f"Deleted pension account {account_id} for user {current_user.email}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting pension account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete pension account",
        )


# Value Entry endpoints
@router.post(
    "/pensions/{account_id}/entries",
    response_model=PensionValueEntry,
    status_code=status.HTTP_201_CREATED,
)
async def create_value_entry(
    account_id: str,
    entry_data: PensionValueEntryCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Add a monthly value entry to a pension account.
    
    - **value**: Current total value of the pension
    - **contributions**: Amount contributed this month (default: 0)
    - **entry_date**: Date of the entry (cannot be in future)
    - **notes**: Optional notes about this entry
    """
    try:
        entry = pension_service.create_value_entry(
            db=db,
            account_id=account_id,
            entry_data=entry_data,
            user_id=current_user.id,
        )
        logger.info(f"Created value entry {entry.id} for account {account_id}")
        return entry
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating value entry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create value entry",
        )


@router.get("/pensions/{account_id}/entries", response_model=List[PensionValueEntry])
async def get_value_entries(
    account_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    limit: int = Query(default=100, ge=1, le=1000, description="Number of entries to return"),
    offset: int = Query(default=0, ge=0, description="Number of entries to skip"),
):
    """
    Get value entries for a pension account.
    
    Returns entries ordered by date (most recent first).
    """
    try:
        entries = pension_service.get_value_entries(
            db=db,
            account_id=account_id,
            user_id=current_user.id,
            limit=limit,
            offset=offset,
        )
        logger.info(f"Retrieved {len(entries)} value entries for account {account_id}")
        return entries
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving value entries: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve value entries",
        )


@router.put("/pensions/entries/{entry_id}", response_model=PensionValueEntry)
async def update_value_entry(
    entry_id: str,
    update_data: PensionValueEntryUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Update a value entry."""
    try:
        entry = pension_service.update_value_entry(
            db=db, entry_id=entry_id, update_data=update_data, user_id=current_user.id
        )
        logger.info(f"Updated value entry {entry_id} for user {current_user.email}")
        return entry
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating value entry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update value entry",
        )


@router.delete("/pensions/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_value_entry(
    entry_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Delete a value entry."""
    try:
        pension_service.delete_value_entry(
            db=db, entry_id=entry_id, user_id=current_user.id
        )
        logger.info(f"Deleted value entry {entry_id} for user {current_user.email}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting value entry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete value entry",
        )