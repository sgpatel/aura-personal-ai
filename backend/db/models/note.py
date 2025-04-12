# backend/db/models/note.py
import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func # For default timestamps

from backend.db.base_class import Base

class NoteDB(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # Correct foreign key syntax
    content = Column(Text, nullable=False)
    tags = Column(ARRAY(String), nullable=True) # Allow null tags array
    # Use func.now() for database-level default timestamp with timezone
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_global = Column(Boolean, default=False)
    date_associated = Column(Date, nullable=True) # Allow null date

    # Relationship
    owner = relationship("UserDB", back_populates="notes") # Ensure UserDB is imported if needed, handl