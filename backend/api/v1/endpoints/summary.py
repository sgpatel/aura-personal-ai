from fastapi import APIRouter, Depends
from backend.api.deps import get_current_user  # Import the missing function
from typing import List
from backend.schemas.note import NoteSummary
from backend.services.summary_service import generate_summary

router = APIRouter()

@router.post("/summary/", response_model=List[NoteSummary])
async def create_summary(notes: List[str], user_id: int = Depends(get_current_user)):
    """
    Generate a summary for the provided notes.
    """
    summary = await generate_summary(notes, user_id)
    return summary