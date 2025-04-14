# backend/services/nlu_service.py
# Placeholder - Replace with real NLU
import logging
from typing import Dict, Any
import re
import datetime

logger = logging.getLogger("aura_backend.nlu")
logger.setLevel(logging.DEBUG)

QUESTION_WORDS = ("who", "what", "where", "when", "why", "how", "is", "are", "do", "does", "can", "could", "tell me")
MEETING_WORDS = ("meeting", "appointment", "schedule", "meet with", "appt")
# --- New Keywords for Getting Reminders ---
REMINDER_QUERY_WORDS = (
    "upcoming meetings", "my reminders", "scheduled meetings",
    "check reminders", "what reminders", "what meetings",
    "list reminders", "show reminders", "reminders list"
)
# --- End New Keywords ---
TIME_PATTERN = re.compile(r'\b(\d{1,2}(:\d{2})?)\s*(am|pm)?\b', re.IGNORECASE)
SPENDING_PATTERN = re.compile(r'\b(?:spend|spent)\s+([$£€₹]?\s*\d+(?:[.,]\d{1,2})?)\b(?:.*?(?:for|on)\s+(.+))?', re.IGNORECASE)


def get_nlu_results(text: str, user_context: Dict) -> Dict[str, Any]:
    """
    Placeholder NLU - Includes get_reminders intent.
    Replace with real NLU model/API.
    """
    logger.debug(f"NLU Service Processing input: '{text}'")
    intent = "unknown"
    entities = {}
    text_lower = text.lower()

    # --- Intent Checks (Order matters: More specific first) ---

    # 1. Specific Commands/Logs
    spending_match = SPENDING_PATTERN.search(text)
    logger.debug(f"Checking log_spending (pattern): match={bool(spending_match)}")
    if spending_match:
        intent = "log_spending"; entities['amount'] = None; entities['description'] = "Unspecified Expense"
        try: amount_str = re.sub(r'[^\d.,]', '', spending_match.group(1)).replace(',', '.'); entities['amount'] = float(amount_str)
        except (ValueError, TypeError): logger.warning(f"Could not parse amount: {spending_match.group(1)}")
        if spending_match.group(2): entities['description'] = spending_match.group(2).strip()
        logger.debug(f"--> Matched intent: {intent}")
    elif intent == "unknown" and ("log spending" in text_lower or "expense" in text_lower):
         intent = "log_spending"; match_amount = re.search(r'\$?(\d+(\.\d{1,2})?)', text)
         if match_amount: entities['amount'] = float(match_amount.group(1))
         match_desc = re.search(r'(?:for|of) (.*)', text, re.IGNORECASE)
         if match_desc: entities['description'] = match_desc.group(1).strip()
         else: entities['description'] = "Unspecified Expense"
         logger.debug(f"--> Matched intent (keyword fallback): {intent}")

    logger.debug(f"Checking log_investment: 'log investment' in text={ 'log investment' in text_lower }")
    if intent == "unknown" and "log investment" in text_lower:
        intent = "log_investment"; entities['content'] = text.replace("log investment", "").strip(); logger.debug(f"--> Matched intent: {intent}")

    debug_log_medical_keywords = "log medical" in text_lower or "log symptom" in text_lower or "log medication" in text_lower
    logger.debug(f"Checking log_medical: has_keywords={debug_log_medical_keywords}")
    if intent == "unknown" and debug_log_medical_keywords:
        intent = "log_medical"; entities['content'] = text.split(":", 1)[-1].strip()
        if "symptom" in text_lower: entities['log_type'] = "symptom"
        elif "medication" in text_lower: entities['log_type'] = "medication"
        else: entities['log_type'] = "general"
        logger.debug(f"--> Matched intent: {intent}")

    # 2. Actions (Scheduling/Reminders)
    debug_has_meet_word = any(word in text_lower for word in MEETING_WORDS)
    debug_time_match = TIME_PATTERN.search(text); debug_has_time = bool(debug_time_match)
    logger.debug(f"Checking schedule_meeting: has_meet_word={debug_has_meet_word}, has_time={debug_has_time}")
    if intent == "unknown" and debug_has_meet_word and debug_has_time:
        intent = "schedule_meeting"; entities['raw_meeting_text'] = text; entities['time_mention'] = debug_time_match.group(0) if debug_time_match else None
        entities['extracted_datetime'] = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2); entities['extracted_content'] = f"Meeting: {text}"
        logger.debug(f"--> Matched intent: {intent}")

    logger.debug(f"Checking set_reminder: 'remind me' in text={ 'remind me' in text_lower }")
    if intent == "unknown" and "remind me" in text_lower:
        intent = "set_reminder"; entities['raw_reminder_text'] = text; entities['remind_at'] = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
        logger.debug(f"--> Matched intent: {intent}")

    # 3. Specific Note Saving Command
    logger.debug(f"Checking save_note (keywords): 'note:' in text={ 'note:' in text_lower }, 'save note' in text={ 'save note' in text_lower }")
    if intent == "unknown" and ("note:" in text_lower or "save note" in text_lower):
        intent = "save_note"; entities['content'] = text.split(":", 1)[-1].strip() if ":" in text else text.replace("save note", "").strip(); entities['is_global'] = True
        logger.debug(f"--> Matched intent: {intent}")

    # 4. Querying Information (BEFORE general question check)
    debug_get_reminders = any(phrase in text_lower for phrase in REMINDER_QUERY_WORDS)
    logger.debug(f"Checking get_reminders: has_keywords={debug_get_reminders}")
    if intent == "unknown" and debug_get_reminders:
        intent = "get_reminders"
        entities['filter'] = 'upcoming' # Default filter, could parse "today", "next week" etc.
        logger.debug(f"--> Matched intent: {intent}")

    debug_note_summary_keywords = "summarize notes tagged" in text_lower or "summarize notes about" in text_lower
    logger.debug(f"Checking get_note_summary: has_keywords={debug_note_summary_keywords}")
    if intent == "unknown" and debug_note_summary_keywords:
        intent = "get_note_summary"
        if "tagged" in text_lower: entities['tags'] = [tag.strip() for tag in text_lower.split("tagged")[-1].split(',')]
        if "about" in text_lower: entities['keywords'] = [kw.strip() for kw in text_lower.split("about")[-1].split(',')]
        logger.debug(f"--> Matched intent: {intent}")

    logger.debug(f"Checking get_summary (keyword 'summarize'): 'summarize' in text={ 'summarize' in text_lower }")
    if intent == "unknown" and "summarize" in text_lower: # General summarize check
        intent = "get_summary"; entities['period'] = 'day'; entities['date'] = datetime.date.today()
        if " on " in text_lower:
            try: date_str = text_lower.split(" on ")[-1].strip().replace("?",""); parsed_date = datetime.datetime.strptime(date_str, "%B %d %Y").date(); entities['date'] = parsed_date
            except ValueError: pass
        logger.debug(f"--> Matched intent: {intent}")

    debug_get_summary_what = "what did i do on" in text_lower or "what happened on" in text_lower
    logger.debug(f"Checking get_summary (keywords 'what did/happened'): has_keywords={debug_get_summary_what}")
    if intent == "unknown" and debug_get_summary_what:
        intent = "get_summary"; entities['period'] = 'day'
        try: date_str = text_lower.split(" on ")[-1].strip().replace("?",""); parsed_date = datetime.datetime.strptime(date_str, "%B %d %Y").date(); entities['date'] = parsed_date
        except ValueError: logger.warning(f"Could not parse date: {text}"); entities['date'] = datetime.date.today()
        logger.debug(f"--> Matched intent: {intent}")

    # 5. General Question Check
    debug_ask_q_starts = text_lower.startswith(QUESTION_WORDS)
    debug_ask_q_mark = "?" in text
    logger.debug(f"Checking ask_question: starts_with_qword={debug_ask_q_starts}, contains_qmark={debug_ask_q_mark}")
    if intent == "unknown" and (debug_ask_q_starts or debug_ask_q_mark):
        intent = "ask_question"; entities['question_text'] = text
        logger.debug(f"--> Matched intent: {intent}")

    # --- Fallback to Save Note ---
    if intent == "unknown":
        intent = "save_note"; entities['content'] = text; entities['is_global'] = True
        logger.debug(f"--> No specific intent matched, falling back to: {intent}")

    logger.info(f"NLU Final Result: Intent={intent}, Entities={entities}")
    return {"intent": intent, "entities": entities}

