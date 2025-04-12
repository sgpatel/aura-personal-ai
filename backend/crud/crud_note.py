# backend/crud/crud_note.py
from typing import List, Any, Dict, Optional # Import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_ # Import or_ for keyword search
import datetime

from backend.crud.base import CRUDBase
from backend.db.models.note import NoteDB
from backend.db.models.spending_log import SpendingLogDB
from backend.db.models.medical_log import MedicalLogDB
from backend.schemas.note import NoteCreate, NoteUpdate

class CRUDNote(CRUDBase[NoteDB, NoteCreate, NoteUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: NoteCreate, user_id: int
    ) -> NoteDB:
        db_obj = NoteDB(**obj_in.dict(), user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[NoteDB]:
        return (
            db.query(self.model)
            .filter(NoteDB.user_id == user_id)
            .order_by(NoteDB.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_date(
        self, db: Session, *, user_id: int, date: datetime.date
    ) -> List[NoteDB]:
        return (
            db.query(self.model)
            .filter(NoteDB.user_id == user_id, NoteDB.date_associated == date)
            .order_by(NoteDB.timestamp.desc())
            .all()
        )

    def get_global(
        self, db: Session, *, user_id: int
    ) -> List[NoteDB]:
        return (
            db.query(self.model)
            .filter(NoteDB.user_id == user_id, NoteDB.is_global == True)
            .order_by(NoteDB.timestamp.desc())
            .all()
        )

    def get_logs_for_date(
        self, db: Session, *, user_id: int, date: datetime.date
    ) -> List[Dict[str, Any]]:
        combined_logs = []
        notes = self.get_by_date(db=db, user_id=user_id, date=date)
        for note in notes:
            combined_logs.append({"type": "note", "content": note.content, "timestamp": note.timestamp})

        from backend import crud
        spending_logs = crud.spending_log.get_by_date(db=db, user_id=user_id, date=date)
        for log in spending_logs:
             combined_logs.append({"type": "spending", "content": f"{log.description}: ${log.amount:.2f}", "timestamp": log.timestamp})

        medical_logs = crud.medical_log.get_by_date(db=db, user_id=user_id, date=date)
        for log in medical_logs:
              combined_logs.append({"type": "medical", "content": f"{log.log_type}: {log.content}", "timestamp": log.timestamp})

        combined_logs.sort(key=lambda x: x.get("timestamp"), reverse=True)
        return combined_logs

    # --- New Function for Tag/Keyword Search ---
    def get_notes_by_tags_keywords(
        self,
        db: Session,
        *,
        user_id: int,
        tags: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[NoteDB]:
        """
        Retrieves notes for a user, filtered by tags (AND logic) and keywords (OR logic in content).
        NOTE: Requires appropriate indexing (GIN for tags, potentially full-text for content)
              in PostgreSQL for good performance on large datasets.
        """
        query = db.query(self.model).filter(NoteDB.user_id == user_id)

        # Tag filtering (requires all provided tags to be present)
        if tags:
            # Use the array contains operator (@>) for PostgreSQL
            # Ensure tags are lowercase or handle case-insensitivity as needed
            query = query.filter(NoteDB.tags.contains(tags)) # Assumes tags is List[str]

        # Keyword filtering (requires any keyword to be present in content)
        if keywords:
            keyword_filters = [NoteDB.content.ilike(f"%{keyword}%") for keyword in keywords]
            query = query.filter(or_(*keyword_filters))

        return query.order_by(NoteDB.timestamp.desc()).offset(skip).limit(limit).all()
    # --- End New Function ---

note = CRUDNote(NoteDB)