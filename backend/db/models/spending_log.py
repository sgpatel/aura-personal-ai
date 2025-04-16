# backend/db/models/spending_log.py
import datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.db.base_class import Base

class SpendingLogDB(Base):
    __tablename__ = "spending_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, index=True, nullable=True)
    currency = Column(String(3), nullable=True, default='USD') # 3-letter code
    date = Column(Date, default=datetime.date.today, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("UserDB", back_populates="spending_logs")