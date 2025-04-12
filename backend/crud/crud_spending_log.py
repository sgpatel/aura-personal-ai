# backend/crud/crud_spending_log.py
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, select
import datetime

from backend.crud.base import CRUDBase
from backend.db.models.spending_log import SpendingLogDB
from backend.schemas.spending_log import SpendingLogCreate, SpendingLogUpdate

class CRUDSpendingLog(CRUDBase[SpendingLogDB, SpendingLogCreate, SpendingLogUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: SpendingLogCreate, user_id: int
    ) -> SpendingLogDB:
        """Creates a spending log associated with a specific user."""
        db_obj = SpendingLogDB(
            **obj_in.dict(exclude_unset=True), # Handle optional date
            user_id=user_id
        )
        # Set default date if not provided
        if db_obj.date is None:
            db_obj.date = datetime.date.today()
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[SpendingLogDB]:
        """Gets multiple spending logs for a specific user."""
        return (
            db.query(self.model)
            .filter(SpendingLogDB.user_id == user_id)
            .order_by(SpendingLogDB.date.desc(), SpendingLogDB.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_date(
        self, db: Session, *, user_id: int, date: datetime.date
    ) -> List[SpendingLogDB]:
        """Gets spending logs for a specific user and date."""
        return (
            db.query(self.model)
            .filter(SpendingLogDB.user_id == user_id, SpendingLogDB.date == date)
            .order_by(SpendingLogDB.timestamp.desc())
            .all()
        )

    def get_spending_summary_by_date(
        self, db: Session, *, user_id: int, date: datetime.date
    ) -> Optional[float]:
        """Calculates the total spending for a specific user and date."""
        total = db.query(func.sum(SpendingLogDB.amount)).filter(
            SpendingLogDB.user_id == user_id, SpendingLogDB.date == date
        ).scalar()
        return total or 0.0 # Return 0.0 if total is None

spending_log = CRUDSpendingLog(SpendingLogDB)
