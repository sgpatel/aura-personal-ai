# backend/api/v1/endpoints/reminders.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import datetime

from backend.db.session import get_db
from backend.schemas.reminder import Reminder, ReminderCreate, ReminderUpdate, RemindersOutput
from backend.schemas.user import User
from backend.schemas.api_models import Message
from backend.api import deps
from backend import crud
from backend.core.config import logger
from backend.services import reminder_service

router = APIRouter()


@router.post("/", response_model=Reminder, status_code=status.HTTP_201_CREATED)
async def create_new_reminder(
    reminder_in: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    reminder_data = reminder_in.dict()
    success = reminder_service.schedule_new_reminder(
        db=db, reminder_data=reminder_data, user_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create/schedule reminder.")

    logger.warning("Returning input data as response for created reminder.")

    temp_response_data = reminder_in.dict()
    temp_response_data['id'] = -1
    temp_response_data['user_id'] = current_user.id
    temp_response_data['created_at'] = datetime.datetime.now(datetime.timezone.utc)
    return temp_response_data


@router.get("/", response_model=List[Reminder])
def read_reminders(
    active_only: bool = Query(True),
    time_filter: str = Query("week"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    reminders_db = crud.reminder.get_filtered_reminders(
        db,
        user_id=current_user.id,
        time_filter=time_filter,
        is_active=active_only
    )
    return reminders_db


@router.get("/upcoming", response_model=RemindersOutput)
async def read_upcoming_reminders(
    minutes: int = 60,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    reminders_db = crud.reminder.get_upcoming_reminders(
        db=db, user_id=current_user.id, within_minutes=minutes
    )
    return RemindersOutput(reminders=reminders_db)


@router.put("/{reminder_id}", response_model=Reminder)
async def update_reminder_details(
    reminder_id: int,
    reminder_in: ReminderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    reminder_db = crud.reminder.get(db=db, id=reminder_id)
    if not reminder_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")
    if reminder_db.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    updated_reminder = crud.reminder.update(db=db, db_obj=reminder_db, obj_in=reminder_in)
    logger.info(f"Reminder {reminder_id} updated.")
    return updated_reminder


@router.delete("/{reminder_id}", response_model=Message)
async def delete_reminder_item(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    reminder_db = crud.reminder.get(db=db, id=reminder_id)
    if not reminder_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")
    if reminder_db.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    crud.reminder.remove(db=db, id=reminder_id)
    logger.info(f"Reminder {reminder_id} deleted.")
    return {"message": "Reminder deleted successfully"}
