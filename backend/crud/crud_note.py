# backend/crud/crud_note.py
from typing import List, Any, Dict, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, cast, Date as SQLDate
import datetime
import numpy as np

# Import SentenceTransformer
from sentence_transformers import SentenceTransformer

from backend.crud.base import CRUDBase
from backend.db.models.note import NoteDB # Import NoteDB model
from backend.schemas.note import NoteCreate, NoteUpdate
from backend.core.config import logger

# --- Initialize Embedding Model ---
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
# --- End Embedding Model Init ---


class CRUDNote(CRUDBase[NoteDB, NoteCreate, NoteUpdate]):

    def generate_embedding(self, text: str) -> Optional[np.ndarray]:
        """Generates embedding for given text, handles model loading errors."""
        if embedding_model is None: logger.error("Embedding model not loaded."); return None
        if not text or not isinstance(text, str): logger.warning("Invalid text for embedding."); return None
        try: return embedding_model.encode(text)
        except Exception as e: logger.error(f"Error generating embedding: {e}", exc_info=True); return None

    def create_with_owner(self, db: Session, *, obj_in: NoteCreate, user_id: int) -> NoteDB:
        """ Creates a note and generates/saves its embedding. """
        db_obj = NoteDB(content=obj_in.content, tags=obj_in.tags, is_global=obj_in.is_global, date_associated=obj_in.date_associated, user_id=user_id)
        if obj_in.content:
            embedding = self.generate_embedding(obj_in.content)
            if embedding is not None: db_obj.embedding = embedding.tolist(); logger.debug(f"Generated embedding for new note.")
            else: logger.warning(f"Could not generate embedding for new note.")
        db.add(db_obj); db.commit(); db.refresh(db_obj); return db_obj

    def update(self, db: Session, *, db_obj: NoteDB, obj_in: Union[NoteUpdate, Dict[str, Any]]) -> NoteDB:
        """ Updates a note and regenerates embedding if content changes. """
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.dict(exclude_unset=True)
        regenerate_embedding = 'content' in update_data and update_data['content'] != db_obj.content
        updated_db_obj = super().update(db=db, db_obj=db_obj, obj_in=update_data)
        if regenerate_embedding and updated_db_obj.content:
             new_embedding = self.generate_embedding(updated_db_obj.content)
             if new_embedding is not None:
                 updated_db_obj.embedding = new_embedding.tolist(); db.add(updated_db_obj); db.commit(); db.refresh(updated_db_obj)
                 logger.debug(f"Regenerated embedding for updated note {updated_db_obj.id}.")
             else: logger.warning(f"Could not regenerate embedding for updated note {updated_db_obj.id}.")
        return updated_db_obj

    def get_multi_by_owner(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[NoteDB]:
        return ( db.query(self.model).filter(NoteDB.user_id == user_id).order_by(NoteDB.timestamp.desc()).offset(skip).limit(limit).all() )

    def get_by_date(self, db: Session, *, user_id: int, date: datetime.date) -> List[NoteDB]:
        logger.debug(f"CRUD: Getting notes for user {user_id} relevant to date {date}")
        query = db.query(self.model).filter(NoteDB.user_id == user_id)
        query = query.filter( or_( NoteDB.date_associated == date, and_( NoteDB.is_global == True, cast(NoteDB.timestamp, SQLDate) == date ) ) )
        return query.order_by(NoteDB.timestamp.desc()).all()

    def get_global(self, db: Session, *, user_id: int) -> List[NoteDB]:
        return ( db.query(self.model).filter(NoteDB.user_id == user_id, NoteDB.is_global == True).order_by(NoteDB.timestamp.desc()).all() )

    def get_logs_for_date(self, db: Session, *, user_id: int, date: datetime.date) -> List[Dict[str, Any]]:
        combined_logs = []; notes = self.get_by_date(db=db, user_id=user_id, date=date)
        for note in notes: combined_logs.append({"type": "note", "content": note.content, "timestamp": note.timestamp})
        from backend import crud
        spending_logs = crud.spending_log.get_by_date(db=db, user_id=user_id, date=date)
        for log in spending_logs: combined_logs.append({"type": "spending", "content": f"{log.description}: ${log.amount:.2f}", "timestamp": log.timestamp})
        medical_logs = crud.medical_log.get_by_date(db=db, user_id=user_id, date=date)
        for log in medical_logs: combined_logs.append({"type": "medical", "content": f"{log.log_type}: {log.content}", "timestamp": log.timestamp})
        combined_logs.sort(key=lambda x: x.get("timestamp"), reverse=True); return combined_logs

    def get_notes_by_tags_keywords(self, db: Session, *, user_id: int, tags: Optional[List[str]] = None, keywords: Optional[List[str]] = None, skip: int = 0, limit: int = 100) -> List[NoteDB]:
        query = db.query(self.model).filter(NoteDB.user_id == user_id)
        if tags: query = query.filter(NoteDB.tags.contains(tags))
        if keywords: keyword_filters = [NoteDB.content.ilike(f"%{keyword}%") for keyword in keywords]; query = query.filter(or_(*keyword_filters))
        return query.order_by(NoteDB.timestamp.desc()).offset(skip).limit(limit).all()

    # --- Updated Vector Search Function ---
    def search_notes_by_similarity(
        self, db: Session, *, user_id: int, query_text: str, limit: int = 3 # Limit context notes
    ) -> List[NoteDB]:
        """
        Searches notes by semantic similarity using pgvector Cosine Distance.
        Requires the 'vector' extension enabled in PostgreSQL.
        """
        logger.debug(f"CRUD: Searching notes for user {user_id} similar to: '{query_text}'")
        if embedding_model is None: logger.error("Embedding model not loaded."); return []
        if not query_text or not isinstance(query_text, str): return []

        try:
            query_vector = self.generate_embedding(query_text)
            if query_vector is None: return []
            query_vector_list = query_vector.tolist()

            # --- Using Cosine Distance ---
            # Returns notes ordered by similarity (lower distance is more similar)
            # Ensure embedding column is not null before calculating distance
            results = (
                db.query(NoteDB)
                .filter(NoteDB.user_id == user_id)
                .filter(NoteDB.embedding != None)
                .order_by(NoteDB.embedding.cosine_distance(query_vector_list))
                .limit(limit)
                .all()
            )
            # --- End Query ---

            logger.info(f"Found {len(results)} notes via similarity search for query: '{query_text}'")
            return results

        except Exception as e:
            logger.error(f"Error during similarity search: {e}", exc_info=True)
            # Could be due to vector extension not enabled or other DB issues
            return []
    # --- End Updated Function ---

note = CRUDNote(NoteDB)