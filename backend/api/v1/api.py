# backend/api/v1/api.py
# Updated to include new summary router
from fastapi import APIRouter

from backend.api.v1.endpoints import (
    auth, users, process, notes, reminders,
    spending, investments, medical, summary # Added summary router import
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(process.router, prefix="/process", tags=["Processing"])
api_router.include_router(notes.router, prefix="/notes", tags=["Notes"])
api_router.include_router(reminders.router, prefix="/reminders", tags=["Reminders"])
api_router.include_router(spending.router, prefix="/spending", tags=["Spending"])
api_router.include_router(investments.router, prefix="/investments", tags=["Investments"])
api_router.include_router(medical.router, prefix="/medical", tags=["Medical"])
api_router.include_router(summary.router, prefix="/summary", tags=["Summary"]) # Include summary router
