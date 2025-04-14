# backend/api/v1/endpoints/process.py
# Implemented RAG for ask_question intent
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
from backend.services.llm import get_llm_service
from backend.services import nlu_service, summary_service, reminder_service
from backend import crud
from backend.core.config import logger

# Context Management
user_contexts: Dict[int, Dict[str, Any]] = {}
def get_user_context(user_id: int) -> Dict:
    if user_id not in user_contexts: user_contexts[user_id] = {"conversation_history": []}
    return user_contexts[user_id]
def update_user_context(user_id: int, new_interaction: Dict):
    context = get_user_context(user_id); context["conversation_history"].append(new_interaction)
    max_history = 10 # Limit history size
    if len(context["conversation_history"]) > max_history: context["conversation_history"] = context["conversation_history"][-max_history:]
    user_contexts[user_id] = context

router = APIRouter()

@router.post("/", response_model=ProcessOutput)
async def process_input_endpoint(
    input_data: ProcessInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    user_id = current_user.id; text_input = input_data.text; reply_text = "Sorry, I didn't understand that."
    context = get_user_context(user_id); update_user_context(user_id, {"role": "user", "content": text_input})
    try:
        nlu_result = nlu_service.get_nlu_results(text_input, context)
        intent = nlu_result.get("intent", "unknown"); entities = nlu_result.get("entities", {})
    except Exception as e: logger.error(f"NLU Service error: {e}", exc_info=True); raise HTTPException(status_code=500, detail="Error processing language.")

    try:
        # --- Handle Intents ---
        if intent == "save_note":
            # ... (no change) ...
            note_data = NoteCreate(content=entities.get('content', text_input), is_global=entities.get('is_global', True), date_associated=entities.get('date_associated'), tags=entities.get('tags'))
            saved_note = crud.note.create_with_owner(db=db, obj_in=note_data, user_id=user_id); reply_text = f"Note saved."
        elif intent == "log_spending":
            # ... (no change) ...
            amount = entities.get('amount'); desc = entities.get('description', 'Unknown expense')
            if amount: spending_data = SpendingLogCreate(description=desc, amount=amount, category=entities.get('category'), date=entities.get('date')); saved_log = crud.spending_log.create_with_owner(db=db, obj_in=spending_data, user_id=user_id); reply_text = f"Logged spending: {desc} for ${amount:.2f}."
            else: reply_text = "Sorry, I couldn't identify the amount."
        elif intent == "log_investment":
            # ... (no change) ...
             inv_data = InvestmentNoteCreate(content=entities.get('content', text_input), title=entities.get('title'), tags=entities.get('tags')); saved_inv = crud.investment_note.create_with_owner(db=db, obj_in=inv_data, user_id=user_id); reply_text = "Investment note saved."
        elif intent == "log_medical":
            # ... (no change) ...
            med_data = MedicalLogCreate(content=entities.get('content', text_input), log_type=entities.get('log_type', 'general'), date=entities.get('date')); saved_med = crud.medical_log.create_with_owner(db=db, obj_in=med_data, user_id=user_id); reply_text = "Medical log saved."
        elif intent == "set_reminder":
             # ... (no change) ...
             remind_at = entities.get('remind_at'); content = entities.get('raw_reminder_text', 'Reminder')
             if remind_at: reminder_data = {"content": content, "remind_at": remind_at}; success = reminder_service.schedule_new_reminder(db=db, reminder_data=reminder_data, user_id=user_id); reply_text = f"Okay, I'll remind you about: '{content[:50]}...'." if success else "Sorry, couldn't schedule reminder."
             else: reply_text = "Sorry, I couldn't figure out when to remind you."
        elif intent == "schedule_meeting":
             # ... (no change) ...
             remind_at = entities.get('extracted_datetime'); content = entities.get('extracted_content', f"Meeting: {entities.get('raw_meeting_text', 'details unclear')}")
             if remind_at: reminder_data = {"content": content, "remind_at": remind_at}; success = reminder_service.schedule_new_reminder(db=db, reminder_data=reminder_data, user_id=user_id); reply_text = f"Okay, I've scheduled: '{content[:60]}...'." if success else "Sorry, couldn't schedule the meeting/appointment."
             else: reply_text = "Sorry, I couldn't figure out the time for the meeting/appointment."
        elif intent == "get_summary": # Daily Summary
             # ... (no change) ...
             date = entities.get('date', datetime.date.today()); relevant_data = crud.note.get_logs_for_date(db=db, user_id=user_id, date=date)
             summary = await summary_service.generate_daily_summary(relevant_data, {}); reply_text = summary
        elif intent == "get_note_summary": # Note Summary by Tag/Keyword
            # ... (no change) ...
            tags = entities.get('tags'); keywords = entities.get('keywords')
            if not tags and not keywords: reply_text = "Please specify tags or keywords."
            else:
                notes_to_summarize = crud.note.get_notes_by_tags_keywords(db=db, user_id=user_id, tags=tags, keywords=keywords, limit=50)
                if not notes_to_summarize: reply_text = "No notes found matching criteria."
                else: notes_content = [note.content for note in notes_to_summarize]; summary = await summary_service.generate_note_summary(notes_content=notes_content, criteria_tags=tags, criteria_keywords=keywords); reply_text = summary

# --- New Handler for get_reminders ---
        elif intent == "get_reminders":
            logger.info(f"Handling get_reminders intent for user {user_id}")
            try:
                # Fetch upcoming reminders using CRUD (adjust parameters/logic as needed)
                # Example: Get active reminders due in the next 7 days
                upcoming_reminders = crud.reminder.get_upcoming_reminders(db=db, user_id=user_id, within_minutes=60*24*7)
                # Alternatively, get all active reminders:
                # upcoming_reminders = crud.reminder.get_multi_by_owner(db=db, user_id=user_id, only_active=True, limit=20)

                if not upcoming_reminders:
                    reply_text = "You have no upcoming reminders found."
                else:
                    reply_text = "Okay, here are your upcoming reminders:\n"
                    for rem in upcoming_reminders:
                        try:
                            # Format time in user's local timezone if possible, else UTC
                            rem_time_local = rem.remind_at.astimezone()
                            time_str = rem_time_local.strftime('%a, %b %d %I:%M %p')
                        except Exception: # Fallback if timezone conversion fails
                            time_str = rem.remind_at.strftime('%Y-%m-%d %H:%M UTC')
                        reply_text += f"- {rem.content} (at {time_str})\n"
            except Exception as e:
                logger.error(f"Error fetching reminders for user {user_id}: {e}", exc_info=True)
                reply_text = "Sorry, I couldn't fetch your reminders right now."
        # --- End New Handler ---
        
        # --- Updated ask_question Intent Handler ---
        elif intent == "ask_question":
            question = entities.get('question_text', text_input)
            logger.info(f"Handling ask_question intent. Question: '{question}'")

            # 1. Search for relevant notes using vector similarity
            context_notes = []
            try:
                context_notes = crud.note.search_notes_by_similarity(
                    db=db, user_id=user_id, query_text=question, limit=3 # Get top 3 relevant notes
                )
            except Exception as e:
                logger.error(f"Vector search failed during RAG: {e}", exc_info=True)
                # Proceed without context if search fails

            # 2. Construct prompt with context (if found)
            context_str = ""
            if context_notes:
                logger.info(f"Found {len(context_notes)} relevant notes for context.")
                context_str += "Based on the following potentially relevant context from your past notes:\n"
                for i, note in enumerate(context_notes):
                    context_str += f"Context {i+1}: {note.content}\n"
                context_str += "---\n"

            final_prompt = f"{context_str}Please answer the following question:\n\nQuestion: {question}\n\nAnswer:"
            logger.debug(f"Augmented prompt for LLM:\n{final_prompt}")

            # 3. Call LLM service
            try:
                llm_service = get_llm_service()
                answer = await llm_service.generate_text(prompt=final_prompt) # Ensure await
                reply_text = answer
            except Exception as e:
                logger.error(f"LLM answer error: {e}", exc_info=True)
                reply_text = "Sorry, I encountered an error trying to answer your question."
        # --- End Updated ask_question Handler ---

        else: # Unknown intent fallback
             logger.info(f"Unknown intent '{intent}'. Input: '{text_input}'"); reply_text = f"Received: '{text_input[:50]}...'. How can I assist?"
    except Exception as e: logger.error(f"Error handling intent '{intent}': {e}", exc_info=True); reply_text = "Sorry, an internal error occurred."
    update_user_context(user_id, {"role": "assistant", "content": reply_text}); return ProcessOutput(reply=reply_text)

