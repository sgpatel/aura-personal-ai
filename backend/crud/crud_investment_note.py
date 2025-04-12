# backend/crud/crud_investment_note.py
from typing import List
from sqlalchemy.orm import Session

from backend.crud.base import CRUDBase
from backend.db.models.investment_note import InvestmentNoteDB
from backend.schemas.investment_note import InvestmentNoteCreate, InvestmentNoteUpdate

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
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[InvestmentNoteDB]:
        """Gets multiple investment notes for a specific user."""
        return (
            db.query(self.model)
            .filter(InvestmentNoteDB.user_id == user_id)
            .order_by(InvestmentNoteDB.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

investment_note = CRUDInvestmentNote(InvestmentNoteDB)