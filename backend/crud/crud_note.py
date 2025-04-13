# backend/crud/crud_note.py
from typing import List, Any, Dict, Optional
from sqlalchemy.orm import Session
# Import additional SQLAlchemy functions/types needed for date casting/filtering
from sqlalchemy import or_, and_, cast, Date as SQLDate
import datetime

from backend.crud.base import CRUDBase
from backend.db.models.note import NoteDB
from backend.db.models.spending_log import SpendingLogDB
from backend.db.models.medical_log import MedicalLogDB
from backend.schemas.note import NoteCreate, NoteUpdate
from backend.core.config import logger # Import logger

class CRUDNote(CRUDBase[NoteDB, NoteCreate, NoteUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: NoteCreate, user_id: int
    ) -> NoteDB:
        # Ensure date_associated is handled correctly (Pydantic might pass None)
        db_obj = NoteDB(
            content=obj_in.content,
            tags=obj_in.tags,
            is_global=obj_in.is_global,
            date_associated=obj_in.date_associated, # Will be None if not provided
            user_id=user_id
        )
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

    # --- Updated get_by_date logic ---
    def get_by_date(
        self, db: Session, *, user_id: int, date: datetime.date
    ) -> List[NoteDB]:
        """
        Gets notes for a specific user that are either explicitly associated
        with the given date OR are global notes created on that date.
        """
        logger.debug(f"CRUD: Getting notes for user {user_id} relevant to date {date}")
        # Filter for notes matching the user_id
        query = db.query(self.model).filter(NoteDB.user_id == user_id)

        # Add filter: EITHER date_associated matches OR (it's global AND timestamp date matches)
        query = query.filter(
            or_(
                # Condition 1: Note is specifically associated with the date
                NoteDB.date_associated == date,
                # Condition 2: Note is global AND was created on that date
                and_(
                    NoteDB.is_global == True,
                    # Cast the timestamp to date for comparison
                    # Note: This might be database-specific (works well on PostgreSQL)
                    cast(NoteDB.timestamp, SQLDate) == date
                )
            )
        )

        return query.order_by(NoteDB.timestamp.desc()).all()
    # --- End Updated get_by_date logic ---

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
        # This function now implicitly uses the updated get_by_date logic when fetching notes
        combined_logs = []
        notes = self.get_by_date(db=db, user_id=user_id, date=date) # Calls updated logic
        for note in notes: combined_logs.append({"type": "note", "content": note.content, "timestamp": note.timestamp})

        from backend import crud
        # Fetch other logs based on their specific date field
        spending_logs = crud.spending_log.get_by_date(db=db, user_id=user_id, date=date)
        for log in spending_logs: combined_logs.append({"type": "spending", "content": f"{log.description}: ${log.amount:.2f}", "timestamp": log.timestamp})
        medical_logs = crud.medical_log.get_by_date(db=db, user_id=user_id, date=date)
        for log in medical_logs: combined_logs.append({"type": "medical", "content": f"{log.log_type}: {log.content}", "timestamp": log.timestamp})

        combined_logs.sort(key=lambda x: x.get("timestamp"), reverse=True); return combined_logs

    def get_notes_by_tags_keywords(
        self, db: Session, *, user_id: int, tags: Optional[List[str]] = None, keywords: Optional[List[str]] = None, skip: int = 0, limit: int = 100
    ) -> List[NoteDB]:
        query = db.query(self.model).filter(NoteDB.user_id == user_id)
        if tags: query = query.filter(NoteDB.tags.contains(tags)) # Use array @> operator (PostgreSQL)
        if keywords: keyword_filters = [NoteDB.content.ilike(f"%{keyword}%") for keyword in keywords]; query = query.filter(or_(*keyword_filters))
        return query.order_by(NoteDB.timestamp.desc()).offset(skip).limit(limit).all()

note = CRUDNote(NoteDB)
