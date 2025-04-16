# backend/api/v1/endpoints/spending.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import datetime
from typing import List, Optional

from backend.db.session import get_db
from backend.schemas.spending_log import SpendingLog, SpendingLogCreate, SpendingLogUpdate, SpendingLogsOutput
from backend.schemas.user import User
from backend.schemas.api_models import Message
from backend.api import deps
from backend import crud
from backend.core.config import logger

router = APIRouter()

@router.post("/", response_model=SpendingLog, status_code=status.HTTP_201_CREATED)
async def create_new_spending_log(
    log_in: SpendingLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """ Create a new spending log entry for the current user. """
    log_db = crud.spending_log.create_with_owner(db=db, obj_in=log_in, user_id=current_user.id)
    logger.info(f"Spending log {log_db.id} created for user {current_user.id}")
    return log_db

# --- Updated GET / to pass filters to CRUD ---
@router.get("/", response_model=SpendingLogsOutput)
async def read_spending_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[datetime.date] = Query(None, description="Filter logs from this date"),
    end_date: Optional[datetime.date] = Query(None, description="Filter logs up to this date"),
    category: Optional[str] = Query(None, description="Filter by category (case-insensitive, partial match)"),
):
    """Retrieve spending logs for the current user, with optional date and category filters."""
    logs_db = crud.spending_log.get_multi_by_owner(
        db=db,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        category=category,  # Pass filters to CRUD
        skip=skip,
        limit=limit
    )
    # TODO: Calculate total based on fetched logs if needed, or add dedicated summary endpoint
    total = None
    # Example client-side calculation: 
    if logs_db: total = sum(log.amount for log in logs_db)
    return SpendingLogsOutput(spending_logs=logs_db, total_amount=total)
# --- End Update ---



@router.get("/{log_id}", response_model=SpendingLog)
async def read_spending_log_by_id(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """ Get a specific spending log by ID. """
    log_db = crud.spending_log.get(db=db, id=log_id)
    if not log_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spending log not found")
    if log_db.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return log_db

@router.put("/{log_id}", response_model=SpendingLog)
async def update_spending_log_by_id(
    log_id: int,
    log_in: SpendingLogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """ Update a specific spending log. """
    log_db = crud.spending_log.get(db=db, id=log_id)
    if not log_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spending log not found")
    if log_db.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    updated_log = crud.spending_log.update(db=db, db_obj=log_db, obj_in=log_in)
    return updated_log

@router.delete("/{log_id}", response_model=Message)
async def delete_spending_log_by_id(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """ Delete a specific spending log. """
    log_db = crud.spending_log.get(db=db, id=log_id)
    if not log_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spending log not found")
    if log_db.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    crud.spending_log.remove(db=db, id=log_id)
    return {"message": "Spending log deleted successfully"}