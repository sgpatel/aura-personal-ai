# backend/api/v1/api.py
# Updated to include new routers
from fastapi import APIRouter

# Import endpoint routers
from backend.api.v1.endpoints import (
    auth, users, process, notes, reminders,spending, investments, medical, summary
)

api_router = APIRouter()

# Include routers from endpoint modules
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(process.router, prefix="/process", tags=["Processing"])
api_router.include_router(notes.router, prefix="/notes", tags=["Notes"])
api_router.include_router(reminders.router, prefix="/reminders", tags=["Reminders"])
api_router.include_router(spending.router, prefix="/spending", tags=["Spending"])
api_router.include_router(investments.router, prefix="/investments", tags=["Investments"])
api_router.include_router(medical.router, prefix="/medical", tags=["Medical"])
api_router.include_router(summary.router, prefix="/summary", tags=["Summary"])
# ... include other routers ...