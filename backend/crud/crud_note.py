# backend/crud/crud_note.py
from typing import List, Any, Dict, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, cast, Date as SQLDate, func
import datetime
import numpy as np
from sentence_transformers import SentenceTransformer

from backend.crud.base import CRUDBase
from backend.db.models.note import NoteDB
from backend.schemas.note import NoteCreate, NoteUpdate
from backend.core.config import logger

# Embedding Model Init
try:
    logger.info("Loading sentence-transformer model ('all-MiniLM-L6-v2')...")
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
    logger.info("Sentence-transformer model loaded successfully.")
    EMBEDDING_DIM_CHECK = embedding_model.get_sentence_embedding_dimension()
    from backend.db.models.note import EMBEDDING_DIM
    if EMBEDDING_DIM_CHECK != EMBEDDING_DIM:
        logger.warning(f"Model embedding dimension ({EMBEDDING_DIM_CHECK}) != DB model dimension ({EMBEDDING_DIM})!")
except Exception as e:
    logger.error(f"Failed to load sentence-transformer model: {e}", exc_info=True)
    embedding_model = None

class CRUDNote(CRUDBase[NoteDB, NoteCreate, NoteUpdate]):

    def generate_embedding(self, text: str) -> Optional[np.ndarray]:
        if embedding_model is None:
            logger.error("Embedding model not loaded.")
            return None
        if not text or not isinstance(text, str):
            logger.warning("Invalid text for embedding.")
            return None
        try:
            return embedding_model.encode(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            return None

    def create_with_owner(self, db: Session, *, obj_in: NoteCreate, user_id: int) -> NoteDB:
        db_obj = NoteDB(
            content=obj_in.content,
            tags=obj_in.tags,
            is_global=obj_in.is_global,
            date_associated=obj_in.date_associated,
            user_id=user_id
        )
        if obj_in.content:
            embedding = self.generate_embedding(obj_in.content)
            if embedding is not None:
                db_obj.embedding = embedding.tolist()
                logger.debug(f"Generated embedding for new note.")
            else:
                logger.warning(f"Could not generate embedding for new note.")
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: NoteDB, obj_in: Union[NoteUpdate, Dict[str, Any]]) -> NoteDB:
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.dict(exclude_unset=True)
        regenerate_embedding = 'content' in update_data and update_data['content'] != db_obj.content
        # Perform non-embedding updates first
        for field, value in update_data.items():
             if hasattr(db_obj, field):
                 setattr(db_obj, field, value)

        # Regenerate embedding if content changed
        if regenerate_embedding and db_obj.content:
             new_embedding = self.generate_embedding(db_obj.content)
             if new_embedding is not None:
                 db_obj.embedding = new_embedding.tolist()
                 logger.debug(f"Regenerated embedding for updated note {db_obj.id}.")
             else:
                  logger.warning(f"Could not regenerate embedding for updated note {db_obj.id}.")
                  # db_obj.embedding = None # Optional: Nullify if regeneration fails

        db.add(db_obj) # Add updated object to session
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
    ) -> List[NoteDB]:
        """Gets multiple notes for a user, optionally filtered by creation date range."""
        query = db.query(self.model).filter(NoteDB.user_id == user_id)
        # Apply date filters based on timestamp (casting to date)
        if start_date:
            query = query.filter(cast(NoteDB.timestamp, SQLDate) >= start_date)
        if end_date:
            query = query.filter(cast(NoteDB.timestamp, SQLDate) <= end_date)
        return (
            query.order_by(NoteDB.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_date(self, db: Session, *, user_id: int, date: datetime.date) -> List[NoteDB]:
        logger.debug(f"CRUD: Getting notes for user {user_id} relevant to date {date}")
        query = db.query(self.model).filter(NoteDB.user_id == user_id)
        query = query.filter(
            or_(
                NoteDB.date_associated == date,
                and_(
                    NoteDB.is_global == True,
                    cast(NoteDB.timestamp, SQLDate) == date
                )
            )
        )
        return query.order_by(NoteDB.timestamp.desc()).all()

    def get_global(
        self,
        db: Session,
        *,
        user_id: int,
        start_date: Optional[datetime.date] = None,  # Added date filters
        end_date: Optional[datetime.date] = None,    # Added date filters
        skip: int = 0,
        limit: int = 100
    ) -> List[NoteDB]:
        """Gets global notes for a user, optionally filtered by creation date range."""
        query = db.query(self.model).filter(
            NoteDB.user_id == user_id,
            NoteDB.is_global == True
        )
        # Apply date filters based on timestamp (casting to date)
        if start_date:
            query = query.filter(cast(NoteDB.timestamp, SQLDate) >= start_date)
        if end_date:
            query = query.filter(cast(NoteDB.timestamp, SQLDate) <= end_date)
        return (
            query.order_by(NoteDB.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_logs_for_date(self, db: Session, *, user_id: int, date: datetime.date) -> List[Dict[str, Any]]:
        combined_logs = []
        notes = self.get_by_date(db=db, user_id=user_id, date=date)
        for note in notes:
            combined_logs.append({"type": "note", "content": note.content, "timestamp": note.timestamp})
        from backend import crud # Import here to avoid circular dependency issues at module level
        spending_logs = crud.spending_log.get_by_date(db=db, user_id=user_id, date=date)
        for log in spending_logs:
            combined_logs.append({"type": "spending", "content": f"{log.description}: ${log.amount:.2f}", "timestamp": log.timestamp})
        medical_logs = crud.medical_log.get_by_date(db=db, user_id=user_id, date=date)
        for log in medical_logs:
             combined_logs.append({"type": "medical", "content": f"{log.log_type}: {log.content}", "timestamp": log.timestamp})
        combined_logs.sort(key=lambda x: x.get("timestamp"), reverse=True)
        return combined_logs

    def get_notes_by_tags_keywords(self, db: Session, *, user_id: int, tags: Optional[List[str]] = None, keywords: Optional[List[str]] = None, skip: int = 0, limit: int = 100) -> List[NoteDB]:
        query = db.query(self.model).filter(NoteDB.user_id == user_id)
        if tags:
            # Assumes tags is List[str]. Requires GIN index on tags column in PostgreSQL for efficiency.
            query = query.filter(NoteDB.tags.contains(tags))
        if keywords:
            # Basic case-insensitive keyword search
            keyword_filters = [NoteDB.content.ilike(f"%{keyword}%") for keyword in keywords]
            query = query.filter(or_(*keyword_filters))
        return query.order_by(NoteDB.timestamp.desc()).offset(skip).limit(limit).all()

    # Placeholder for keyword/FTS search called by process endpoint
    def search_notes(self, db: Session, *, user_id: int, query: str, limit: int = 10) -> List[NoteDB]:
        """ Placeholder: Searches notes by keywords. Implement FTS for production. """
        logger.debug(f"CRUD: Keyword searching notes for user {user_id} with query: '{query}'")
        if not query: return []
        search_term = f"%{query}%"
        return (db.query(NoteDB).filter(NoteDB.user_id == user_id, NoteDB.content.ilike(search_term))
                .order_by(NoteDB.timestamp.desc()).limit(limit).all())

    def search_notes_by_similarity(self, db: Session, *, user_id: int, query_text: str, limit: int = 3) -> List[NoteDB]:
        logger.debug(f"CRUD: Searching notes for user {user_id} similar to: '{query_text}'")
        if embedding_model is None: logger.error("Embedding model not loaded."); return []
        if not query_text or not isinstance(query_text, str): return []
        try:
            query_vector = self.generate_embedding(query_text)
            if query_vector is None: return []
            query_vector_list = query_vector.tolist()
            results = (db.query(NoteDB).filter(NoteDB.user_id == user_id, NoteDB.embedding != None)
                       .order_by(NoteDB.embedding.cosine_distance(query_vector_list)).limit(limit).all())
            logger.info(f"Found {len(results)} notes via similarity search for query: '{query_text}'")
            return results
        except Exception as e: logger.error(f"Error during similarity search: {e}", exc_info=True); return []

note = CRUDNote(NoteDB)