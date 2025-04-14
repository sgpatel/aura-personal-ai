# backend/db/models/note.py
import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Import Vector type from pgvector.sqlalchemy
from pgvector.sqlalchemy import Vector

from backend.db.base_class import Base

# Define embedding dimensions (e.g., 384 for all-MiniLM-L6-v2)
# Choose based on the sentence-transformer model you use
EMBEDDING_DIM = 384

class NoteDB(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(ARRAY(String), nullable=True, index=True) # GIN index recommended
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_global = Column(Boolean, default=False)
    date_associated = Column(Date, nullable=True)

    # --- New Embedding Column ---
    embedding = Column(Vector(EMBEDDING_DIM), nullable=True)
    # Add index=True later if using specific index types like HNSW with Alembic
    # For HNSW index in PostgreSQL:
    # CREATE INDEX idx_notes_embedding ON notes USING hnsw (embedding vector_l2_ops);
    # --- End New Column ---

    owner = relationship("UserDB", back_populates="notes")
