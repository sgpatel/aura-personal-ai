# backend/api/v1/endpoints/process.py
# Updated to handle ask_question and schedule_meeting intents
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import datetime
from typing import Dict, Any

from backend.db.session import get_db
from backend.schemas.api_models import ProcessInput, ProcessOutput
from backend.schemas.user import User
from backend.schemas.note import NoteCreate
from backend.schemas.spending_log import SpendingLogCreate
from backend.schemas.investment_note import InvestmentNoteCreate
from backend.schemas.medical_log import MedicalLogCreate
from backend.api import deps
# Import LLM service factory
from backend.services.llm import get_llm_service
from backend.services import nlu_service, summary_service, reminder_service
from backend import crud
from backend.core.config import logger

# --- Context Management (Keep simple in-memory version for now) ---
user_contexts: Dict[int, Dict[str, Any]] = {}
def get_user_context(user_id: int) -> Dict:
    if user_id not in user_contexts: user_contexts[user_id] = {"conversation_history": []}
    return user_contexts[user_id]
def update_user_context(user_id: int, new_interaction: Dict):
    context = get_user_context(user_id); context["conversation_history"].append(new_interaction)
    max_history = 10
    if len(context["conversation_history"]) > max_history: context["conversation_history"] = context["conversation_history"][-max_history:]
    user_contexts[user_id] = context
# --- End Context Management ---

router = APIRouter()

@router.post("/", response_model=ProcessOutput)
async def process_input_endpoint( # Make endpoint async
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
        # --- Handle Intents ---
        if intent == "save_note":
            note_data = NoteCreate(content=entities.get('content', text_input), is_global=entities.get('is_global', True), date_associated=entities.get('date_associated'), tags=entities.get('tags'))
            saved_note = crud.note.create_with_owner(db=db, obj_in=note_data, user_id=user_id)
            reply_text = f"Note saved."
        elif intent == "log_spending":
            amount = entities.get('amount'); desc = entities.get('description', 'Unknown expense')
            if amount: spending_data = SpendingLogCreate(description=desc, amount=amount, category=entities.get('category'), date=entities.get('date')); saved_log = crud.spending_log.create_with_owner(db=db, obj_in=spending_data, user_id=user_id); reply_text = f"Logged spending: {desc} for ${amount:.2f}."
            else: reply_text = "Sorry, I couldn't identify the amount."
        elif intent == "log_investment":
            inv_data = InvestmentNoteCreate(content=entities.get('content', text_input), title=entities.get('title'), tags=entities.get('tags')); saved_inv = crud.investment_note.create_with_owner(db=db, obj_in=inv_data, user_id=user_id); reply_text = "Investment note saved."
        elif intent == "log_medical":
            med_data = MedicalLogCreate(content=entities.get('content', text_input), log_type=entities.get('log_type', 'general'), date=entities.get('date')); saved_med = crud.medical_log.create_with_owner(db=db, obj_in=med_data, user_id=user_id); reply_text = "Medical log saved."
        elif intent == "set_reminder":
             remind_at = entities.get('remind_at'); content = entities.get('raw_reminder_text', 'Reminder')
             if remind_at: reminder_data = {"content": content, "remind_at": remind_at}; success = reminder_service.schedule_new_reminder(db=db, reminder_data=reminder_data, user_id=user_id); reply_text = f"Okay, I'll remind you about: '{content[:50]}...'." if success else "Sorry, couldn't schedule reminder."
             else: reply_text = "Sorry, I couldn't figure out when to remind you."
        elif intent == "schedule_meeting": # New intent handler
             remind_at = entities.get('extracted_datetime') # Use extracted datetime placeholder
             content = entities.get('extracted_content', f"Meeting: {entities.get('raw_meeting_text', 'details unclear')}")
             if remind_at:
                 reminder_data = {"content": content, "remind_at": remind_at}
                 success = reminder_service.schedule_new_reminder(db=db, reminder_data=reminder_data, user_id=user_id)
                 reply_text = f"Okay, I've scheduled: '{content[:60]}...'." if success else "Sorry, couldn't schedule the meeting/appointment."
             else:
                 reply_text = "Sorry, I couldn't figure out the time for the meeting/appointment."
        elif intent == "get_summary": # Daily Summary
             date = entities.get('date', datetime.date.today())
             relevant_data = crud.note.get_logs_for_date(db=db, user_id=user_id, date=date)
             summary = await summary_service.generate_daily_summary(relevant_data, {}) # Await async call
             reply_text = summary
        elif intent == "get_note_summary": # Note Summary by Tag/Keyword
            tags = entities.get('tags'); keywords = entities.get('keywords')
            if not tags and not keywords: reply_text = "Please specify tags or keywords to summarize notes."
            else:
                notes_to_summarize = crud.note.get_notes_by_tags_keywords(db=db, user_id=user_id, tags=tags, keywords=keywords, limit=50)
                if not notes_to_summarize: reply_text = "No notes found matching the criteria."
                else:
                    notes_content = [note.content for note in notes_to_summarize]
                    summary = await summary_service.generate_note_summary(notes_content=notes_content, criteria_tags=tags, criteria_keywords=keywords) # Await async call
                    reply_text = summary
        elif intent == "ask_question": # New intent handler
            question = entities.get('question_text', text_input)
            logger.info(f"Handling ask_question intent for user {user_id}. Question: '{question}'")
            try:
                llm_service = get_llm_service()
                # Use generate_text for general questions
                if llm_service.provider == "ollama":
                    answer = await llm_service.generate_text(prompt=question)
                else:
                    # This might block if generate_text is sync - consider run_in_threadpool
                    answer = llm_service.generate_text(prompt=question)
                reply_text = answer
            except Exception as e:
                logger.error(f"Error getting answer from LLM for user {user_id}: {e}", exc_info=True)
                reply_text = "Sorry, I encountered an error trying to answer your question."
        else: # Unknown intent fallback
             logger.info(f"Unknown intent '{intent}' for user {user_id}. Input: '{text_input}'")
             reply_text = f"I received: '{text_input[:50]}...'. I'm still learning how to handle that."

    except Exception as e:
        logger.error(f"Error handling intent '{intent}' for user {user_id}: {e}", exc_info=True)
        reply_text = "Sorry, an internal error occurred."

    update_user_context(user_id, {"role": "assistant", "content": reply_text})
    return ProcessOutput(reply=reply_text)
