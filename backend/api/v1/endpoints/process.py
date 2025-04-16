# backend/api/v1/endpoints/process.py
# Handles main user text input, NLU, intent dispatching, and context management.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import datetime
from typing import Dict, Any, Optional

# Attempt to import dateutil safely
try:
    import dateutil.parser
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False

# Standard library imports first
import json
import re

# Project-specific imports
from backend.db.session import get_db
from backend.schemas.api_models import ProcessInput, ProcessOutput
from backend.schemas.user import User
from backend.schemas.note import NoteCreate
from backend.schemas.spending_log import SpendingLogCreate, SpendingLog
from backend.schemas.investment_note import InvestmentNoteCreate
from backend.schemas.medical_log import MedicalLogCreate
from backend.api import deps # For authentication dependency
from backend.services.llm import get_llm_service # For LLM calls
from backend.services.nlu_service import get_nlu_results_hybrid # Using hybrid NLU
from backend.services import summary_service, reminder_service # Specific services
from backend import crud # Access to all CRUD operations
from backend.core.config import logger # Central logger

# --- Context Management (Simple In-Memory) ---
# TODO: Replace with a persistent solution like Redis or Database integration
user_contexts: Dict[int, Dict[str, Any]] = {}

def get_user_context(user_id: int) -> Dict:
    """Retrieves or initializes context for a user."""
    return user_contexts.setdefault(user_id, {
        "conversation_history": [],
        "preferences": {}, # Placeholder for user preferences
        "last_intent": None # Placeholder for tracking last intent
    })

def update_user_context(user_id: int, new_interaction: Dict):
    """Adds interaction to context, keeping a limited history."""
    context = get_user_context(user_id)
    context["conversation_history"].append(new_interaction)
    # Keep only the last N interactions (e.g., 5 user + 5 assistant = 10 turns)
    max_history_len = 10
    context["conversation_history"] = context["conversation_history"][-max_history_len:]
    # Update last intent if provided in interaction data
    if "intent" in new_interaction:
         context["last_intent"] = new_interaction["intent"]
    user_contexts[user_id] = context
# --- End Context Management ---

# --- API Router ---
router = APIRouter()

# --- Helper Function to Parse Date Entities ---
def parse_date_entity(raw_date_entity: Any) -> Optional[datetime.date]:
    """ Parses various date inputs into a date object. """
    if isinstance(raw_date_entity, datetime.date):
        return raw_date_entity
    if isinstance(raw_date_entity, datetime.datetime):
        return raw_date_entity.date()
    if isinstance(raw_date_entity, str):
        raw_date_entity_lower = raw_date_entity.lower()
        if raw_date_entity_lower == 'today':
            return datetime.date.today()
        elif raw_date_entity_lower == 'yesterday':
            return datetime.date.today() - datetime.timedelta(days=1)
        elif raw_date_entity_lower == 'tomorrow':
             return datetime.date.today() + datetime.timedelta(days=1)
        else:
            try:
                # Attempt ISO format first
                return datetime.date.fromisoformat(raw_date_entity)
            except ValueError:
                # Fallback to dateutil if available
                if DATEUTIL_AVAILABLE:
                    try:
                        # Default to None if parsing fails completely
                        parsed_dt = dateutil.parser.parse(raw_date_entity, default=datetime.datetime.now(datetime.timezone.utc))
                        return parsed_dt.date()
                    except (ValueError, TypeError, OverflowError) as e:
                         logger.warning(f"dateutil could not parse date entity '{raw_date_entity}': {e}")
                         return None
                else:
                     logger.warning(f"Could not parse date entity '{raw_date_entity}' with basic methods.")
                     return None
    logger.debug(f"Could not parse '{raw_date_entity}' as date.")
    return None
# --- End Helper Function ---

# --- Helper Function to Parse Datetime Entities ---
def parse_datetime_entity(raw_datetime_entity: Any) -> Optional[datetime.datetime]:
     """ Parses various datetime inputs into a timezone-aware datetime object (UTC). """
     if isinstance(raw_datetime_entity, datetime.datetime):
         if raw_datetime_entity.tzinfo is None:
             return raw_datetime_entity.replace(tzinfo=datetime.timezone.utc)
         else:
             return raw_datetime_entity.astimezone(datetime.timezone.utc)
     if isinstance(raw_datetime_entity, str):
         try:
             # Try ISO format first (dateutil handles this well)
             if DATEUTIL_AVAILABLE:
                 dt = dateutil.parser.isoparse(raw_datetime_entity)
                 if dt.tzinfo is None: return dt.replace(tzinfo=datetime.timezone.utc)
                 else: return dt.astimezone(datetime.timezone.utc)
             else: # Basic ISO parse if dateutil not available
                  dt = datetime.datetime.fromisoformat(raw_datetime_entity)
                  if dt.tzinfo is None: return dt.replace(tzinfo=datetime.timezone.utc)
                  else: return dt.astimezone(datetime.timezone.utc)
         except (ValueError, TypeError):
             # Fallback to general parsing if ISO fails and dateutil is available
             if DATEUTIL_AVAILABLE:
                 try:
                     now = datetime.datetime.now(datetime.timezone.utc)
                     # Use fuzzy=False for potentially more predictable parsing
                     dt = dateutil.parser.parse(raw_datetime_entity, default=now, fuzzy=False)
                     if dt.tzinfo is None: return dt.replace(tzinfo=datetime.timezone.utc)
                     else: return dt.astimezone(datetime.timezone.utc)
                 except (ValueError, TypeError, OverflowError) as e:
                     logger.warning(f"dateutil could not parse datetime entity '{raw_datetime_entity}': {e}")
                     return None
             else:
                  logger.warning(f"Could not parse datetime entity '{raw_datetime_entity}' with basic methods.")
                  return None
     logger.debug(f"Could not parse '{raw_datetime_entity}' as datetime.")
     return None
# --- End Helper Function ---


@router.post("/", response_model=ProcessOutput)
async def process_input_endpoint(
    input_data: ProcessInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Main endpoint to process user text input:
    1. Gets intent/entities via Hybrid NLU (Rules + LLM Fallback).
    2. Executes actions based on intent (CRUD, Summaries, QA).
    3. Handles fallbacks and errors.
    4. Updates basic conversation context.
    """
    text_input = (input_data.text or "").strip()
    if not text_input:
        return ProcessOutput(reply="Please provide some input.")

    user_id = current_user.id
    context = get_user_context(user_id)
    update_user_context(user_id, {"role": "user", "content": text_input})
    reply_text = "Sorry, I'm not sure how to respond to that yet." # Default reply

    # 1. Get NLU results
    try:
        nlu_result = await get_nlu_results_hybrid(text_input, context)
        intent = nlu_result.get("intent", "unknown")
        entities = nlu_result.get("entities", {})
        logger.info(f"Intent: {intent} | Entities: {entities}")
    except Exception as e:
        logger.error(f"NLU Service error: {e}", exc_info=True)
        # Update context with failure? For now, just return generic error
        # update_user_context(user_id, {"role": "assistant", "content": "Error understanding.", "intent": "error", "success": False})
        return ProcessOutput(reply="I'm having trouble understanding your request right now.")

    # 2. Handle Intent based on NLU result
    try:
        if intent == "save_note":
            parsed_date = parse_date_entity(entities.get('date'))
            note_data = NoteCreate(
                content=entities.get('content', text_input),
                is_global=entities.get('is_global', False if parsed_date else True), # Default non-global if date found
                date_associated=parsed_date,
                tags=entities.get('tags', []) # Use empty list if tags missing
            )
            saved_note = crud.note.create_with_owner(db=db, obj_in=note_data, user_id=user_id)
            logger.info(f"Note {saved_note.id} saved for user {user_id}")
            reply_text = "Note saved successfully."

        elif intent == "log_spending":
            amount = entities.get('amount')
            if amount is None:
                 reply_text = "It looks like you want to log spending, but please specify an amount."
            else:
                 try:
                     amount_float = float(amount)
                 except (ValueError, TypeError):
                     logger.error(f"Invalid amount entity received from NLU: {amount}")
                     reply_text = "Sorry, I couldn't understand the amount specified for the spending log."
                 else:
                     parsed_date = parse_date_entity(entities.get('date'))
                     spending_data = SpendingLogCreate(
                         amount=amount_float,
                         currency=entities.get('currency', 'USD'), # Default currency
                         description=entities.get('description', 'Miscellaneous'), # Default description
                         category=entities.get('category', 'Other'), # Default category
                         date=parsed_date # Use parsed date (defaults to today in CRUD if None)
                     )
                     saved_log = crud.spending_log.create_with_owner(db=db, obj_in=spending_data, user_id=user_id)
                     logger.info(f"Spending log {saved_log.id} saved for user {user_id}")
                     reply_text = f"Logged {saved_log.currency}{saved_log.amount:.2f} for {saved_log.description}."

        elif intent == "set_reminder" or intent == "schedule_meeting":
             remind_at_dt = parse_datetime_entity(entities.get('datetime'))
             content = entities.get('content') or entities.get('subject') or "Reminder/Meeting" # Prioritize specific content

             if remind_at_dt:
                 # Ensure reminder time is in the future (optional, prevents immediate past reminders)
                 if remind_at_dt <= datetime.datetime.now(datetime.timezone.utc):
                     logger.warning(f"Attempted to set reminder for past time: {remind_at_dt}")
                     # Option 1: Reject
                     # reply_text = "Sorry, I can only set reminders for the future."
                     # Option 2: Adjust slightly into future (e.g., 1 minute)
                     remind_at_dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=1)
                     logger.info(f"Adjusted past reminder time to {remind_at_dt}")

                 reminder_data = {"content": content, "remind_at": remind_at_dt}
                 success = reminder_service.schedule_new_reminder(db=db, reminder_data=reminder_data, user_id=user_id)
                 if success:
                     try: time_str_confirm = remind_at_dt.astimezone().strftime('%a, %b %d at %I:%M %p %Z') # Nicer format
                     except Exception: time_str_confirm = remind_at_dt.strftime('%Y-%m-%d %H:%M %Z')
                     reply_text = f"Okay, reminder set for: '{content[:50]}{'...' if len(content)>50 else ''}' on {time_str_confirm}."
                 else:
                     reply_text = "Sorry, I encountered an error trying to set the reminder."
             else:
                 reply_text = "Sorry, I couldn't figure out a valid time for the reminder/meeting."

        elif intent == "log_investment":
             inv_data = InvestmentNoteCreate(content=entities.get('content', text_input), title=entities.get('title'), tags=entities.get('tags', []))
             saved_inv = crud.investment_note.create_with_owner(db=db, obj_in=inv_data, user_id=user_id)
             logger.info(f"Investment note {saved_inv.id} saved for user {user_id}")
             reply_text = "Investment note saved."

        elif intent == "log_medical":
             parsed_date = parse_date_entity(entities.get('date'))
             med_data = MedicalLogCreate(content=entities.get('content', text_input), log_type=entities.get('log_type', 'general'), date=parsed_date)
             saved_med = crud.medical_log.create_with_owner(db=db, obj_in=med_data, user_id=user_id)
             logger.info(f"Medical log {saved_med.id} saved for user {user_id}")
             reply_text = "Medical log saved."

        elif intent == "query_spending":
            time_range = entities.get('time_range', 'month')
            category_filter = entities.get('category')
            logger.info(f"Handling query_spending intent for user {user_id}. Range: {time_range}, Category: {category_filter}")
            # Call CRUD function (placeholder logic inside)
            spending_data_db = crud.spending_log.get_by_time_range(db=db, user_id=user_id, time_range=time_range, category=category_filter)
            # Pass data to summary service (placeholder logic inside)
            # --- FIX: Convert DB objects to Pydantic models, then to dicts ---
            spending_data_pydantic = [SpendingLog.model_validate(log) for log in spending_data_db]  # Pydantic V2
            spending_data_dict = [log.dict() for log in spending_data_pydantic]
            # --- End Fix ---
            reply_text = await summary_service.generate_spending_summary(spending_data=spending_data_dict, time_range=time_range)

        elif intent == "get_reminders":
            time_filter = entities.get('filter', 'week') # Default to upcoming week
            logger.info(f"Handling get_reminders intent for user {user_id}. Filter: {time_filter}")
            try:
                reminders = crud.reminder.get_filtered_reminders(db=db, user_id=user_id, time_filter=time_filter)
                if not reminders: reply_text = f"You have no reminders scheduled for '{time_filter}'." if time_filter != "all" else "You have no active reminders."
                else:
                    reply_text = f"Okay, here are your reminders for '{time_filter}':\n"
                    for rem in reminders:
                        try: rem_time_local = rem.remind_at.astimezone(); time_str = rem_time_local.strftime('%a, %b %d %I:%M %p %Z')
                        except Exception: time_str = rem.remind_at.strftime('%Y-%m-%d %H:%M UTC')
                        reply_text += f"- {rem.content} (at {time_str})\n"
            except Exception as e: logger.error(f"Error fetching reminders: {e}", exc_info=True); reply_text = "Sorry, couldn't fetch reminders."

        elif intent == "search_information":
            search_query = entities.get('query') or entities.get('keywords') or text_input # Use extracted query or fallback
            logger.info(f"Handling search_information intent for user {user_id}. Query: '{search_query}'")
            # Call CRUD function (placeholder logic inside)
            results_db = crud.note.search_notes(db=db, user_id=user_id, query=search_query, limit=5)
            # Pass data to summary service (placeholder logic inside)
            results_dict = [note.dict() for note in results_db] # Convert for service
            reply_text = await summary_service.generate_search_summary(results=results_dict, query=search_query)

        elif intent == "get_summary": # Daily Summary
             parsed_date = parse_date_entity(entities.get('date')) or datetime.date.today()
             logger.info(f"Handling get_summary intent for user {user_id}. Date: {parsed_date}")
             relevant_data = crud.note.get_logs_for_date(db=db, user_id=user_id, date=parsed_date)
             summary = await summary_service.generate_daily_summary(relevant_data, {}); reply_text = summary

        elif intent == "get_note_summary": # Note Summary by Tag/Keyword
            tags = entities.get('tags'); keywords = entities.get('keywords')
            logger.info(f"Handling get_note_summary for user {user_id}. Tags: {tags}, Keywords: {keywords}")
            if not tags and not keywords: reply_text = "Please specify tags or keywords to summarize notes."
            else:
                notes_to_summarize = crud.note.get_notes_by_tags_keywords(db=db, user_id=user_id, tags=tags, keywords=keywords, limit=50)
                if not notes_to_summarize: reply_text = "No notes found matching the criteria."
                else: notes_content = [note.content for note in notes_to_summarize]; summary = await summary_service.generate_note_summary(notes_content=notes_content, criteria_tags=tags, criteria_keywords=keywords); reply_text = summary

        elif intent == "ask_question": # General Question Answering (RAG)
            question = entities.get('question_text', text_input); logger.info(f"Handling ask_question intent. Question: '{question}'"); context_notes = []; context_str = ""
            try: context_notes = crud.note.search_notes_by_similarity(db=db, user_id=user_id, query_text=question, limit=3)
            except Exception as e: logger.error(f"Vector search failed: {e}", exc_info=True)
            if context_notes: logger.info(f"Found {len(context_notes)} notes."); context_str += "Based on context from your past notes:\n";
            for i, note in enumerate(context_notes): context_str += f"{i+1}: {note.content}\n"; context_str += "---\n"
            final_prompt = f"{context_str}Please answer the following question:\n\nQuestion: {question}\n\nAnswer:"; logger.debug(f"LLM prompt:\n{final_prompt}")
            try: llm_service = get_llm_service(); answer = await llm_service.generate_text(prompt=final_prompt); reply_text = answer
            except Exception as e: logger.error(f"LLM answer error: {e}", exc_info=True); reply_text = "Sorry, error getting answer."

        else: # Unknown intent from NLU, fallback to LLM chat
             logger.info(f"Unhandled intent '{intent}', fallback to LLM chat.")
             try:
                 llm_service = get_llm_service()
                 # Construct a simple chat prompt
                 # TODO: Add conversation history from context for better chat
                 chat_prompt = f"User: {text_input}\nAssistant:"
                 llm_response = await llm_service.generate_text(prompt=chat_prompt, max_tokens=150)
                 reply_text = llm_response.strip()
             except Exception as e:
                 logger.error(f"LLM fallback error: {e}", exc_info=True)
                 reply_text = "Sorry, I couldn't process that request." # Generic error for final fallback

    except Exception as e:
        # Catchall for errors during intent handling
        logger.error(f"Error handling intent '{intent}': {e}", exc_info=True)
        reply_text = "Sorry, something went wrong while processing your request."

    # Update context with the final reply
    update_user_context(user_id, {"role": "assistant", "content": reply_text, "intent": intent}) # Removed success flag for now
    return ProcessOutput(reply=reply_text)