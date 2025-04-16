# backend/api/v1/endpoints/medical.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import datetime
from typing import List, Optional

from backend.db.session import get_db
from backend.schemas.medical_log import MedicalLog, MedicalLogCreate, MedicalLogUpdate, MedicalLogsOutput
from backend.schemas.user import User
from backend.schemas.api_models import Message
from backend.api import deps
from backend import crud
from backend.core.config import logger

router = APIRouter()

@router.post("/", response_model=MedicalLog, status_code=status.HTTP_201_CREATED)
async def create_new_medical_log(
    log_in: MedicalLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """ Create a new medical log entry for the current user. """
    log_db = crud.medical_log.create_with_owner(db=db, obj_in=log_in, user_id=current_user.id)
    logger.info(f"Medical log {log_db.id} created for user {current_user.id}")
    return log_db

# --- Updated GET / to pass filters to CRUD ---
@router.get("/", response_model=MedicalLogsOutput)
async def read_medical_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    log_type: Optional[str] = Query(None, description="Filter by log type (case-insensitive, partial match)"),
    start_date: Optional[datetime.date] = Query(None, description="Filter logs from this date"),
    end_date: Optional[datetime.date] = Query(None, description="Filter logs up to this date"),
):
    """ Retrieve medical logs for the current user, with optional filters. """
    logs_db = crud.medical_log.get_multi_by_owner(
        db=db, user_id=current_user.id,
        log_type=log_type, start_date=start_date, end_date=end_date, # Pass filters
        skip=skip, limit=limit
    )
    return MedicalLogsOutput(medical_logs=logs_db)
# --- End Update ---

@router.get("/{log_id}", response_model=MedicalLog)
async def read_medical_log_by_id(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """ Get a specific medical log by ID. """
    log_db = crud.medical_log.get(db=db, id=log_id)
    if not log_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical log not found")
    if log_db.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return log_db

@router.put("/{log_id}", response_model=MedicalLog)
async def update_medical_log_by_id(
    log_id: int,
    log_in: MedicalLogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """ Update a specific medical log. """
    log_db = crud.medical_log.get(db=db, id=log_id)
    if not log_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical log not found")
    if log_db.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    updated_log = crud.medical_log.update(db=db, db_obj=log_db, obj_in=log_in)
    return updated_log

@router.delete("/{log_id}", response_model=Message)
async def delete_medical_log_by_id(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """ Delete a specific medical log. """
    log_db = crud.medical_log.get(db=db, id=log_id)
    if not log_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical log not found")
    if log_db.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    crud.medical_log.remove(db=db, id=log_id)
    return {"message": "Medical log deleted successfully"}
