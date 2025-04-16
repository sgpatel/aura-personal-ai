# backend/crud/crud_spending_log.py
from typing import List, Optional, Union, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, select, and_
import datetime

from backend.crud.base import CRUDBase
from backend.db.models.spending_log import SpendingLogDB
from backend.schemas.spending_log import SpendingLogCreate, SpendingLogUpdate
from backend.core.config import logger

class CRUDSpendingLog(CRUDBase[SpendingLogDB, SpendingLogCreate, SpendingLogUpdate]):
    def create_with_owner(self, db: Session, *, obj_in: SpendingLogCreate, user_id: int) -> SpendingLogDB:
        db_obj = SpendingLogDB(**obj_in.dict(exclude_unset=True), user_id=user_id)
        if db_obj.date is None: db_obj.date = datetime.date.today()
        if db_obj.currency is None: db_obj.currency = 'USD'
        db.add(db_obj); db.commit(); db.refresh(db_obj); return db_obj

    def get_multi_by_owner(
        self,
        db: Session,
        *,
        user_id: int,
        start_date: Optional[datetime.date] = None,  # Added date filters
        end_date: Optional[datetime.date] = None,    # Added date filters
        category: Optional[str] = None,              # Keep category filter
        skip: int = 0,
        limit: int = 100
    ) -> List[SpendingLogDB]:
        """Gets multiple spending logs for a user, optionally filtered by date range and category."""
        query = db.query(self.model).filter(SpendingLogDB.user_id == user_id)
        if start_date:
            query = query.filter(SpendingLogDB.date >= start_date)
        if end_date:
            query = query.filter(SpendingLogDB.date <= end_date)
        if category:
            query = query.filter(SpendingLogDB.category.ilike(f"%{category}%"))
        return (
            query.order_by(SpendingLogDB.date.desc(), SpendingLogDB.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_date(self, db: Session, *, user_id: int, date: datetime.date) -> List[SpendingLogDB]:
            # This can still be useful for fetching a single day's logs
            return (
                db.query(self.model)
                .filter(SpendingLogDB.user_id == user_id, SpendingLogDB.date == date)
                .order_by(SpendingLogDB.timestamp.desc())
                .all()
            )

    # --- Placeholder for Time Range / Category Query ---
    def get_by_time_range(
        self, db: Session, *, user_id: int, time_range: str = "month",
        category: Optional[str] = None, start_date: Optional[datetime.date] = None,
        end_date: Optional[datetime.date] = None, limit: int = 100
    ) -> List[SpendingLogDB]:
        """ Fetches spending logs within a time range and optionally by category. """
        logger.debug(f"CRUD: Getting spending for user {user_id}, range: {time_range}, category: {category}")
        query = db.query(self.model).filter(SpendingLogDB.user_id == user_id)

        # Date Filtering Logic
        if start_date and end_date:
            query = query.filter(SpendingLogDB.date >= start_date, SpendingLogDB.date <= end_date)
        else:
            today = datetime.date.today()
            if time_range == "day":
                query = query.filter(SpendingLogDB.date == today)
            elif time_range == "week":
                start_of_week = today - datetime.timedelta(days=today.weekday())
                query = query.filter(SpendingLogDB.date >= start_of_week)
            elif time_range == "month":
                start_of_month = today.replace(day=1)
                query = query.filter(SpendingLogDB.date >= start_of_month)
            elif time_range == "year":
                start_of_year = today.replace(month=1, day=1)
                query = query.filter(SpendingLogDB.date >= start_of_year)
            # 'all' time_range doesn't need a date filter here

        if category:
            query = query.filter(SpendingLogDB.category.ilike(f"%{category}%"))

        return query.order_by(SpendingLogDB.date.desc(), SpendingLogDB.timestamp.desc()).limit(limit).all()
    # --- End Placeholder ---

    def get_spending_summary_by_date(self, db: Session, *, user_id: int, date: datetime.date) -> Optional[float]:
        total = db.query(func.sum(SpendingLogDB.amount)).filter(SpendingLogDB.user_id == user_id, SpendingLogDB.date == date).scalar()
        return total or 0.0

spending_log = CRUDSpendingLog(SpendingLogDB)