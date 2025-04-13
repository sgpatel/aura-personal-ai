# backend/api/v1/endpoints/summary.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import datetime

from backend.db.session import get_db
from backend.schemas.api_models import SummaryOutput # Use existing schema
from backend.schemas.user import User
from backend.api import deps
from backend import crud
from backend.services import summary_service # Import summary service
from backend.core.config import logger

router = APIRouter()

@router.get("/{date_str}", response_model=SummaryOutput)
async def get_daily_summary(
    date_str: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get a summary of logs (notes, spending, medical) for a specific date.
    """
    try:
        target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format. Use YYYY-MM-DD.")

    logger.info(f"Request for daily summary for user {current_user.id} on {target_date}")

    # Fetch relevant data using the combined log fetcher in crud_note
    # (Consider moving get_logs_for_date to a more general location if preferred)
    relevant_data = crud.note.get_logs_for_date(db=db, user_id=current_user.id, date=target_date)

    # Call the daily summary service
    try:
        summary_text = summary_service.generate_daily_summary(relevant_data, {})
    except Exception as e:
        logger.error(f"Daily Summary Service error for user {current_user.id} on {target_date}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error generating daily summary.")

    return SummaryOutput(summary=summary_text, date=target_date)
