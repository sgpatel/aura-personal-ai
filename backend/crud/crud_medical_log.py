# backend/crud/crud_medical_log.py
from typing import List, Optional
from sqlalchemy.orm import Session
import datetime

from backend.crud.base import CRUDBase
from backend.db.models.medical_log import MedicalLogDB
from backend.schemas.medical_log import MedicalLogCreate, MedicalLogUpdate

class CRUDMedicalLog(CRUDBase[MedicalLogDB, MedicalLogCreate, MedicalLogUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: MedicalLogCreate, user_id: int
    ) -> MedicalLogDB:
        """Creates a medical log associated with a specific user."""
        db_obj = MedicalLogDB(
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
        self,
        db: Session,
        *,
        user_id: int,
        log_type: Optional[str] = None,
        start_date: Optional[datetime.date] = None,  # Added date filters
        end_date: Optional[datetime.date] = None,    # Added date filters
        skip: int = 0,
        limit: int = 100
    ) -> List[MedicalLogDB]:
        """Gets multiple medical logs for a user, optionally filtered by type and date range."""
        query = db.query(self.model).filter(MedicalLogDB.user_id == user_id)
        if log_type:
            query = query.filter(MedicalLogDB.log_type.ilike(f"%{log_type}%"))  # Allow partial match for type
        # Apply date filters
        if start_date:
            query = query.filter(MedicalLogDB.date >= start_date)
        if end_date:
            query = query.filter(MedicalLogDB.date <= end_date)
        return (
            query.order_by(MedicalLogDB.date.desc(), MedicalLogDB.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
    def get_by_date(self, db: Session, *, user_id: int, date: datetime.date) -> List[MedicalLogDB]:
        # This can still be useful for fetching a single day's logs
        return (
            db.query(self.model)
            .filter(MedicalLogDB.user_id == user_id, MedicalLogDB.date == date)
            .order_by(MedicalLogDB.timestamp.desc())
            .all()
        )

medical_log = CRUDMedicalLog(MedicalLogDB)