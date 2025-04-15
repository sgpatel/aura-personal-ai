# backend/api/v1/endpoints/process.py
# Updated to work with enhanced NLU service
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
from backend.services.nlu_service import get_nlu_results_hybrid, VALID_INTENTS, COMMON_ENTITIES
from backend.services import summary_service, reminder_service
from backend import crud
from backend.core.config import logger

# Context Management
user_contexts: Dict[int, Dict[str, Any]] = {}
def get_user_context(user_id: int) -> Dict:
    return user_contexts.setdefault(user_id, {
        "conversation_history": [],
        "preferences": {},
        "last_intent": None
    })

def update_user_context(user_id: int, new_interaction: Dict):
    context = get_user_context(user_id)
    context["conversation_history"].append(new_interaction)
    # Keep last 5 interactions
    context["conversation_history"] = context["conversation_history"][-5:]
    user_contexts[user_id] = context

router = APIRouter()

def handle_datetime_entity(entity: Any) -> datetime.datetime:
    """Robust datetime handling with fallbacks"""
    if isinstance(entity, datetime.datetime):
        return entity
    
    try:
        if isinstance(entity, str):
            return datetime.datetime.fromisoformat(entity)
        elif isinstance(entity, (int, float)):
            return datetime.datetime.fromtimestamp(entity, tz=datetime.timezone.utc)
    except (ValueError, TypeError):
        pass
    
    logger.warning("Could not parse datetime, using fallback")
    return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)

@router.post("/", response_model=ProcessOutput)
async def process_input_endpoint(
    input_data: ProcessInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    text_input = (input_data.text or "").strip()
    if not text_input:
        return ProcessOutput(reply="Please provide some input to process")
    user_id = current_user.id
    text_input = input_data.text.strip()
    context = get_user_context(user_id)
    update_user_context(user_id, {"role": "user", "content": text_input})
    reply_text = "Let me check on that..."

    try:
        # Get NLU results with conversation context
        nlu_result = await get_nlu_results_hybrid(text_input, context)
        intent = nlu_result.get("intent", "unknown")
        entities = nlu_result.get("entities", {})
        logger.info(f"Processed intent: {intent} | Entities: {entities}")
    except Exception as e:
        logger.error(f"NLU Service error: {e}", exc_info=True)
        return ProcessOutput(reply="I'm having trouble understanding that right now.")

    try:
        # Enhanced Intent Handling
        if intent == "save_note":
            note_data = NoteCreate(
                content=entities.get('content', text_input),
                is_global=entities.get('is_global', False),
                date_associated=entities.get('date'),
                tags=entities.get('tags', [])
            )
            crud.note.create_with_owner(db=db, obj_in=note_data, user_id=user_id)
            reply_text = "Note saved successfully."

        elif intent == "log_spending":
            if 'amount' not in entities:
                reply_text = "Please specify an amount to log."
            else:
                spending_data = SpendingLogCreate(
                    amount=float(entities['amount']),
                    currency=entities.get('currency', 'USD'),
                    description=entities.get('description', 'Miscellaneous'),
                    category=entities.get('category', 'Other'),
                    date=entities.get('date')
                )
                crud.spending_log.create_with_owner(db=db, obj_in=spending_data, user_id=user_id)
                reply_text = f"Logged {spending_data.currency}{spending_data.amount:.2f} for {spending_data.description}"

        elif intent == "schedule_meeting":
            if 'datetime' not in entities:
                reply_text = "When would you like to schedule this meeting?"
            else:
                meeting_time = handle_datetime_entity(entities['datetime'])
                reminder_service.schedule_new_reminder(
                    db=db,
                    reminder_data={
                        "content": entities.get('subject', 'Meeting'),
                        "remind_at": meeting_time
                    },
                    user_id=user_id
                )
                reply_text = f"Meeting scheduled for {meeting_time.strftime('%A, %B %d at %I:%M %p')}"

        elif intent == "query_spending":
            time_range = entities.get('time_range', 'month')
            category_filter = entities.get('category')
            spending_data = crud.spending_log.get_by_time_range(
                db=db, 
                user_id=user_id,
                time_range=time_range,
                category=category_filter
            )
            reply_text = summary_service.generate_spending_summary(spending_data)

        elif intent == "get_reminders":
            time_filter = entities.get('filter', 'week')
            reminders = crud.reminder.get_filtered_reminders(
                db=db,
                user_id=user_id,
                time_filter=time_filter
            )
            if not reminders:
                reply_text = "No upcoming reminders found."
            else:
                reminder_list = "\n".join(
                    f"- {r.content} ({r.remind_at.strftime('%m/%d %I:%M %p')})"
                    for r in reminders
                )
                reply_text = f"Upcoming reminders:\n{reminder_list}"

        elif intent == "search_information":
            search_query = entities.get('keywords', text_input)
            results = crud.note.search_notes(
                db=db,
                user_id=user_id,
                query=search_query,
                limit=3
            )
            reply_text = summary_service.generate_search_summary(results, search_query)

        # Handle other intents
        elif intent == "ask_question":
            # ... (existing question handling with context notes)
            question = entities.get('question_text', text_input)
            logger.info(f"Handling ask_question intent. Question: '{question}'")
            context_notes = []; context_str = ""
            try: context_notes = crud.note.search_notes_by_similarity(db=db, user_id=user_id, query_text=question, limit=3)
            except Exception as e: logger.error(f"Vector search failed: {e}", exc_info=True)
            if context_notes:
                logger.info(f"Found {len(context_notes)} relevant notes for context.")
                context_str += "Based on context from your past notes:\n";
                for i, note in enumerate(context_notes): context_str += f"Context {i+1}: {note.content}\n"
                context_str += "---\n"
            final_prompt = f"{context_str}Please answer the following question:\n\nQuestion: {question}\n\nAnswer:"
            logger.debug(f"Augmented prompt for LLM:\n{final_prompt}")
            try: llm_service = get_llm_service(); answer = await llm_service.generate_text(prompt=final_prompt); reply_text = answer
            except Exception as e: logger.error(f"LLM answer error: {e}", exc_info=True); reply_text = "Sorry, error getting answer."
        
        else:
            # Fallback to LLM for unhandled intents
            llm_service = get_llm_service()
            llm_response = await llm_service.generate_text(
                prompt=f"User: {text_input}\nAssistant:",
                max_tokens=150
            )
            reply_text = llm_response.strip()

    except Exception as e:
        logger.error(f"Error handling intent '{intent}': {e}", exc_info=True)
        reply_text = "Something went wrong while processing your request."

    # Update context with system response
    update_user_context(user_id, {
        "role": "assistant",
        "content": reply_text,
        "intent": intent,
        "success": True
    })

    return ProcessOutput(reply=reply_text)