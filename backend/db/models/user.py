# backend/db/models/user.py
# (No changes needed from previous version)
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from backend.db.base_class import Base # Import the Base

class UserDB(Base):
    __tablename__ = "users" # Explicit table name

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, index=True, nullable=True) # Allow null
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationships (ensure corresponding model files import UserDB for back_populates)
    notes = relationship("NoteDB", back_populates="owner", cascade="all, delete-orphan")
    reminders = relationship("ReminderDB", back_populates="owner", cascade="all, delete-orphan")
    spending_logs = relationship("SpendingLogDB", back_populates="owner", cascade="all, delete-orphan")
    investment_notes = relationship("InvestmentNoteDB", back_populates="owner", cascade="all, delete-orphan")
    medical_logs = relationship("MedicalLogDB", back_populates="owner", cascade="all, delete-orphan")
