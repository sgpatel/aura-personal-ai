# backend/crud/crud_reminder.py
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
import datetime

from backend.crud.base import CRUDBase
from backend.db.models.reminder import ReminderDB
from backend.schemas.reminder import ReminderCreate, ReminderUpdate

class CRUDReminder(CRUDBase[ReminderDB, ReminderCreate, ReminderUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: ReminderCreate, user_id: int
    ) -> ReminderDB:
        db_obj = ReminderDB(**obj_in.dict(), user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100, only_active: bool = False
    ) -> List[ReminderDB]:
        query = db.query(self.model).filter(ReminderDB.user_id == user_id)
        if only_active:
            query = query.filter(ReminderDB.is_active == True)
        return query.order_by(ReminderDB.remind_at.asc()).offset(skip).limit(limit).all()

    def get_upcoming_reminders(
        self, db: Session, *, user_id: int, within_minutes: int = 60
    ) -> List[ReminderDB]:
        """ Gets active reminders due within a certain time frame. """
        now = datetime.datetime.now(datetime.timezone.utc)
        future_time = now + datetime.timedelta(minutes=within_minutes)
        return (
            db.query(self.model)
            .filter(
                ReminderDB.user_id == user_id,
                ReminderDB.is_active == True,
                ReminderDB.remind_at >= now,
                ReminderDB.remind_at <= future_time
            )
            .order_by(ReminderDB.remind_at.asc())
            .all()
        )

    # Add methods to update (e.g., mark as inactive) or delete reminders

reminder = CRUDReminder(ReminderDB)