# backend/db/models/__init__.py
# Ensures Base knows about all models for metadata operations
from .user import UserDB
from .note import NoteDB
from .reminder import ReminderDB
from .spending_log import SpendingLogDB
from .investment_note import InvestmentNoteDB
from .medical_log import MedicalLogDB

# You might not need to import all here if Base is imported correctly in each model file
# and Base.metadata is used elsewhere (e.g., in Alembic env.py or main.py startup)