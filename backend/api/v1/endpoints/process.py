# backend/api/v1/endpoints/process.py
# Updated to use CRUD instances and new reminder service placeholder
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import datetime
from typing import Dict, Any # Import Any

from backend.db.session import get_db
from backend.schemas.api_models import ProcessInput, ProcessOutput
from backend.schemas.user import User
from backend.schemas.note import NoteCreate
from backend.schemas.spending_log import SpendingLogCreate
from backend.api import deps
from backend.services import nlu_service, summary_service, reminder_service # Import reminder_service
from backend import crud # Import crud package
from backend.core.config import logger

# --- Context Management (Keep simple in-memory version for now) ---
user_contexts: Dict[int, Dict[str, Any]] = {}
def get_user_context(user_id: int) -> Dict:
    if user_id not in user_contexts: user_contexts[user_id] = {"conversation_history": []}
    return user_contexts[user_id]
def update_user_context(user_id: int, new_interaction: Dict):
    context = get_user_context(user_id)
    context["conversation_history"].append(new_interaction)
    max_history = 10
    if len(context["conversation_history"]) > max_history:
        context["conversation_history"] = context["conversation_history"][-max_history:]
    user_contexts[user_id] = context
# --- End Context Management ---

router = APIRouter()

@router.post("/", response_model=ProcessOutput)
async def process_input_endpoint(
    input_data: ProcessInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    user_id = current_user.id
    text_input = input_data.text
    reply_text = "Sorry, I didn't understand that."

    context = get_user_context(user_id)
    update_user_context(user_id, {"role": "user", "content": text_input})

    try:
        nlu_result = nlu_service.get_nlu_results(text_input, context)
        intent = nlu_result.get("intent", "unknown")
        entities = nlu_result.get("entities", {})
    except Exception as e:
        logger.error(f"NLU Service error for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing language.")

    try:
        if intent == "save_note":
            content = entities.get('content', text_input)
            note_data = NoteCreate(
                content=content,
                is_global=entities.get('is_global', True),
                date_associated=entities.get('date_associated'), # Pass if extracted
                tags=entities.get('tags') # Pass if extracted
            )
            saved_note = crud.note.create_with_owner(db=db, obj_in=note_data, user_id=user_id) # Use crud instance
            logger.info(f"Note {saved_note.id} saved for user {user_id}.")
            reply_text = f"Note saved."

        elif intent == "log_spending":
            amount = entities.get('amount')
            desc = entities.get('description', 'Unknown expense')
            if amount:
                 spending_data = SpendingLogCreate(
                     description=desc,
                     amount=amount,
                     category=entities.get('category'), # Pass if extracted
                     date=entities.get('date') # Pass if extracted
                 )
                 saved_spending = crud.spending_log.create_with_owner(db=db, obj_in=spending_data, user_id=user_id) # Use crud instance
                 logger.info(f"Spending {saved_spending.id} logged for user {user_id}.")
                 reply_text = f"Logged spending: {desc} for ${amount:.2f}."
            else:
                 reply_text = "Sorry, I couldn't identify the amount for the expense."

        elif intent == "set_reminder":
             remind_at = entities.get('remind_at') # Get extracted time (placeholder)
             content = entities.get('raw_reminder_text', 'Reminder') # Use raw text or default
             if remind_at:
                 reminder_data = {
                     "content": content,
                     "remind_at": remind_at,
                     # Add other fields like recurrence if extracted
                 }
                 success = reminder_service.schedule_new_reminder(db=db, reminder_data=reminder_data, user_id=user_id)
                 if success:
                     reply_text = f"Okay, I'll remind you about: '{content[:50]}...'."
                 else:
                     reply_text = "Sorry, I couldn't schedule the reminder."
             else:
                 reply_text = "Sorry, I couldn't figure out when to remind you."

        elif intent == "get_summary":
             period = entities.get('period', 'day')
             date = entities.get('date', datetime.date.today())
             relevant_data = crud.note.get_logs_for_date(db=db, user_id=user_id, date=date) # Use crud instance
             summary = summary_service.generate_summary(relevant_data, {})
             reply_text = summary

        # Add handlers for other intents (medical, investment) using their CRUD instances...

        else:
             logger.info(f"Unknown intent '{intent}' for user {user_id}. Input: '{text_input}'")
             reply_text = f"I received: '{text_input[:50]}...'. How can I help?"

    except Exception as e:
        logger.error(f"Error handling intent '{intent}' for user {user_id}: {e}", exc_info=True)
        reply_text = "Sorry, an internal error occurred."

    update_user_context(user_id, {"role": "assistant", "content": reply_text})
    return ProcessOutput(reply=reply_text)
