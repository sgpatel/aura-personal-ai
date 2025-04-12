# backend/crud/__init__.py
from .crud_user import user # Use an instance or import functions directly
from .crud_note import note
from .crud_reminder import reminder
from .crud_spending_log import spending_log
from .crud_investment_note import investment_note
from .crud_medical_log import medical_log

# This pattern uses instances of CRUD classes (see below)
# Alternatively, import functions directly:
# from .crud_user import get_user_by_email, create_user
# from .crud_note import create_note, get_notes_by_date, get_global_notes
# ... etc ...