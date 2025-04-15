# backend/crud/crud_reminder.py
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import between, and_
import datetime
from datetime import timezone

from backend.crud.base import CRUDBase
from backend.db.models.reminder import ReminderDB
from backend.schemas.reminder import ReminderCreate, ReminderUpdate

class CRUDReminder(CRUDBase[ReminderDB, ReminderCreate, ReminderUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: ReminderCreate, user_id: int
    ) -> ReminderDB:
        """Create reminder with timezone-aware datetime"""
        # Ensure remind_at is timezone-aware
        if obj_in.remind_at.tzinfo is None:
            obj_in.remind_at = obj_in.remind_at.replace(tzinfo=timezone.utc)
            
        db_obj = ReminderDB(**obj_in.dict(), user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_filtered_reminders(
        self, 
        db: Session, 
        *,
        user_id: int,
        time_filter: str = "week",
        is_active: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReminderDB]:
        """
        Get reminders with advanced filtering:
        - time_filter: today/week/month/all
        - is_active: filter by active status
        """
        now = datetime.datetime.now(timezone.utc)
        query = db.query(self.model).filter(
            ReminderDB.user_id == user_id,
            ReminderDB.is_active == is_active
        )

        # Time filter logic
        if time_filter == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + datetime.timedelta(days=1)
            query = query.filter(between(ReminderDB.remind_at, start, end))
        elif time_filter == "week":
            end = now + datetime.timedelta(days=7)
            query = query.filter(ReminderDB.remind_at <= end)
        elif time_filter == "month":
            end = now + datetime.timedelta(days=30)
            query = query.filter(ReminderDB.remind_at <= end)
        elif time_filter != "all":
            # Default to week if invalid filter
            end = now + datetime.timedelta(days=7)
            query = query.filter(ReminderDB.remind_at <= end)

        return query.order_by(ReminderDB.remind_at.asc()
                            ).offset(skip).limit(limit).all()

    def get_upcoming_reminders(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        within_minutes: int = 60
    ) -> List[ReminderDB]:
        """Get active reminders within time window"""
        now = datetime.datetime.now(timezone.utc)
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
    
    def get_multi_by_owner(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100,
        only_active: bool = False
    ) -> List[ReminderDB]:
        return self.get_filtered_reminders(
            db,
            user_id=user_id,
            time_filter="all",
            is_active=only_active,
            skip=skip,
            limit=limit
        )

    def mark_as_inactive(
        self, 
        db: Session, 
        *, 
        reminder_id: int, 
        user_id: int
    ) -> Optional[ReminderDB]:
        """Soft delete a reminder"""
        reminder = db.query(self.model).filter(
            ReminderDB.id == reminder_id,
            ReminderDB.user_id == user_id
        ).first()
        
        if reminder:
            reminder.is_active = False
            db.commit()
            db.refresh(reminder)
        return reminder

reminder = CRUDReminder(ReminderDB)