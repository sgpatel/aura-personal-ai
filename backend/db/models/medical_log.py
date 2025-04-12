# backend/db/models/medical_log.py
import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.db.base_class import Base

class MedicalLogDB(Base):
    __tablename__ = "medical_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    log_type = Column(String, nullable=False, index=True) # e.g., 'symptom', 'medication', 'appointment'
    content = Column(Text, nullable=False)
    date = Column(Date, default=datetime.date.today, index=True) # Index date
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("UserDB", back_populates="medical_logs")