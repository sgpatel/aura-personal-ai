# backend/api/v1/endpoints/summary.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import datetime

from backend.db.session import get_db
from backend.schemas.api_models import SummaryOutput
from backend.schemas.user import User
from backend.api import deps
from backend import crud
from backend.services.summary_service import generate_daily_summary  # Import summary service
from backend.core.config import logger

router = APIRouter()

@router.get("/{date_str}", response_model=SummaryOutput)
async def get_daily_summary( # Make endpoint async
    date_str: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """ Get a summary of logs for a specific date. """
    try: target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format. Use YYYY-MM-DD.")

    logger.info(f"Request for daily summary for user {current_user.id} on {target_date}")
    relevant_data = crud.note.get_logs_for_date(db=db, user_id=current_user.id, date=target_date)

    try:
        # Await the async service function
        summary_text = await generate_daily_summary(relevant_data, {})
    except Exception as e:
        logger.error(f"Daily Summary Service error for user {current_user.id} on {target_date}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error generating daily summary.")

    return SummaryOutput(summary=summary_text, date=target_date)
