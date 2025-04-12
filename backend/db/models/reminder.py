# backend/db/models/reminder.py
import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.db.base_class import Base

class ReminderDB(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(String, nullable=False)
    remind_at = Column(DateTime(timezone=True), nullable=False, index=True) # Index for querying
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True, index=True) # Index for querying active ones
    # Optional: Add fields for recurrence rule (e.g., RRULE string)
    # recurrence_rule = Column(String, nullable=True)
    # Optional: Track if triggered/dismissed
    # triggered_at = Column(DateTime(timezone=True), nullable=True)

    owner = relationship("UserDB", back_populates="reminders")