# backend/services/nlu_service.py
# (No significant changes from previous version - still placeholder)
import logging
from typing import Dict, Any
import re
import datetime # Import datetime

logger = logging.getLogger(__name__)

def get_nlu_results(text: str, user_context: Dict) -> Dict[str, Any]:
    """
    Placeholder NLU - Replace with real NLU model/API.
    """
    logger.info(f"NLU Service Processing: '{text}'")
    intent = "unknown"
    entities = {}
    text_lower = text.lower()

    # --- Placeholder Intent/Entity Logic ---
    if "remind me" in text_lower:
        intent = "set_reminder"
        entities['raw_reminder_text'] = text # Pass raw text for now
        # TODO: Extract actual time/date using libraries like 'dateparser' or NLU model
        entities['remind_at'] = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1) # Placeholder: 1 hour from now
    elif "log spending" in text_lower or "expense" in text_lower:
        intent = "log_spending"
        match_amount = re.search(r'\$?(\d+(\.\d{1,2})?)', text)
        if match_amount: entities['amount'] = float(match_amount.group(1))
        match_desc = re.search(r'(?:for|of) (.*)', text, re.IGNORECASE)
        if match_desc: entities['description'] = match_desc.group(1).strip()
        else: entities['description'] = "Unspecified Expense"
        # TODO: Extract category, date if mentioned
    elif "summarize" in text_lower:
        intent = "get_summary"
        entities['period'] = 'day' # Default
        entities['date'] = datetime.date.today() # Default
        # TODO: Extract actual period/date
    elif "note:" in text_lower or "save note" in text_lower:
        intent = "save_note"
        entities['content'] = text.split(":", 1)[1].strip() if ":" in text else text.replace("save note", "").strip()
        entities['is_global'] = True # Default assumption
        # TODO: Extract tags, date association, global flag
    elif "what did i do on" in text_lower or "what happened on" in text_lower:
        intent = "get_summary" # Treat as summary request for that day
        # TODO: Extract date more reliably
        try:
            # Very basic date extraction attempt
            date_str = text_lower.split(" on ")[-1].strip().replace("?","")
            # This needs a robust date parsing library!
            parsed_date = datetime.datetime.strptime(date_str, "%B %d %Y").date() # Example format
            entities['date'] = parsed_date
            entities['period'] = 'day'
        except ValueError:
            logger.warning(f"Could not parse date from summary request: {text}")
            entities['date'] = datetime.date.today() # Fallback
            entities['period'] = 'day'
    # Add more intent patterns...

    logger.info(f"NLU Result: Intent={intent}, Entities={entities}")
    return {"intent": intent, "entities": entities}