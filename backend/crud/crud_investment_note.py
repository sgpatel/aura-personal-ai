# backend/crud/crud_investment_note.py
from typing import List,Optional  
from sqlalchemy.orm import Session
from sqlalchemy import cast, Date as SQLDate  # Import cast and SQLDate

from backend.crud.base import CRUDBase
from backend.db.models.investment_note import InvestmentNoteDB
from backend.schemas.investment_note import InvestmentNoteCreate, InvestmentNoteUpdate
import datetime

class CRUDInvestmentNote(CRUDBase[InvestmentNoteDB, InvestmentNoteCreate, InvestmentNoteUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: InvestmentNoteCreate, user_id: int
    ) -> InvestmentNoteDB:
        """Creates an investment note associated with a specific user."""
        db_obj = InvestmentNoteDB(**obj_in.dict(), user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self,
        db: Session,
        *,
        user_id: int,
        start_date: Optional[datetime.date] = None,  # Added date filters
        end_date: Optional[datetime.date] = None,    # Added date filters
        skip: int = 0,
        limit: int = 100
    ) -> List[InvestmentNoteDB]:
        """Gets multiple investment notes for a user, optionally filtered by creation date range."""
        query = db.query(self.model).filter(InvestmentNoteDB.user_id == user_id)
        # Apply date filters based on timestamp (casting to date)
        if start_date:
            query = query.filter(cast(InvestmentNoteDB.timestamp, SQLDate) >= start_date)
        if end_date:
            query = query.filter(cast(InvestmentNoteDB.timestamp, SQLDate) <= end_date)
        return (
            query.order_by(InvestmentNoteDB.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

investment_note = CRUDInvestmentNote(InvestmentNoteDB)