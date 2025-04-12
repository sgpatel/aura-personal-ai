# backend/db/models/investment_note.py
import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.db.base_class import Base

class InvestmentNoteDB(Base):
    __tablename__ = "investment_notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=True) # Title optional
    content = Column(Text, nullable=False)
    tags = Column(ARRAY(String), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("UserDB", back_populates="investment_notes")