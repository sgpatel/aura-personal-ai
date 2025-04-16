# backend/services/nlu_service.py
# Enhanced Hybrid NLU with Advanced Intent Recognition
import logging
from typing import Dict, Any, List
import json
import re
import datetime
from datetime import timezone, date 
from collections import defaultdict

try:
    import dateutil.parser
    from dateutil.relativedelta import relativedelta
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False
    logging.warning("python-dateutil not installed. Date parsing disabled.")


from backend.services.llm import get_llm_service
from backend.core.config import logger

logger = logging.getLogger("aura_backend.nlu")
logger.setLevel(logging.DEBUG) # Ensure debug level is set

# === Intent Taxonomy ===
VALID_INTENTS = [
    "save_note", "log_spending", "log_investment", "log_medical",
    "set_reminder", "schedule_meeting", "modify_event",
    "get_summary", "get_note_summary", "get_reminders", "query_spending",
    "ask_question", "search_information",
    "unknown", "command", "feedback"
]

# === Entity Ontology ===
COMMON_ENTITIES = [
    "content", "amount", "currency", "description", "date", "time",
    "datetime", "timezone", "duration", "category", "tags", "keywords",
    "log_type", "priority", "filter", "time_range", "limit", "sort_by",
    "person", "location", "organization", "confidence", "raw_text",
    "llm_fallback", "question", "context", "note_id", "query", "filters",
    "feedback", "command", "parameters", "subject" # Added subject
]

# === Intent Patterns (expanded from previous) ===
# Note: Currency symbols need to be handled carefully in regex or extraction
CURRENCY_REGEX = r"[$£€₹¥]" # Example, adjust as needed
AMOUNT_REGEX = r"\d+(?:[.,]\d{1,2})?"
SPENDING_PATTERN_1 = re.compile(rf'(spent|spend|expensed?|paid)\s+({CURRENCY_REGEX}?\s*{AMOUNT_REGEX})\b(?:\s+?(?:on|for)\s+(.+))?', re.I)
SPENDING_PATTERN_2 = re.compile(rf'(bought|purchased)\s+(.+?)\s+for\s+({CURRENCY_REGEX}?\s*{AMOUNT_REGEX})', re.I)
MEETING_PATTERN_1 = re.compile(r'(meet|meeting|call)\s+(?:with\s+)?(.+?)\s+(?:at|on)\s+(.+?)(?:\s+to\s+discuss\s+(.+))?', re.I)
MEETING_PATTERN_2 = re.compile(r'(schedule|arrange)\s+(?:a\s+)?(appointment|demo)\s+(?:for|on)\s+(.+)', re.I)
REMINDER_PATTERN_1 = re.compile(r'(remind me|set reminder|alert me)\s+(?:to|about)\s+(.+?)\s+(?:at|on)\s+(.+)', re.I)
REMINDER_PATTERN_2 = re.compile(r'(?:⏰|❗)\s*(.+?)\s+-\s+(.+)', re.I)

INTENT_PATTERNS = {
    "log_spending": [SPENDING_PATTERN_1, SPENDING_PATTERN_2],
    "schedule_meeting": [MEETING_PATTERN_1, MEETING_PATTERN_2],
    "set_reminder": [REMINDER_PATTERN_1, REMINDER_PATTERN_2]
    # Add more patterns for other intents if desired
}

TIME_RELATED = re.compile(
    r'\b(\d{1,2}(?:[:.]\d{2})?\s*(?:am|pm)?)|'
    r'(next\s+(week|month|year|monday|tuesday|wednesday|thursday|friday|saturday|sunday))|'
    r'(in\s+\d+\s+(hours?|days?|weeks?))|'
    r'(tomorrow|tonight|today|noon|midnight)\b', re.I
)

QUESTION_PATTERN = re.compile(
    r'^(can you|could you|would you|please|how to|what\'?s?|who\'?s?|where|when|why|how)\b', re.I
)

# === Entity Validation Rules ===
# (Using user's provided version)
# === Entity Validation Rules (Corrected log_medical) ===
ENTITY_VALIDATION = {
    "log_spending": {
        "required": ["amount"],
        "optional": ["currency", "description", "category", "date"], # Added date
        "types": {"amount": (float, int), "currency": str, "category": str, "date": (str, date)} # Added date type
    },
    "schedule_meeting": {
        "required": ["datetime"],
        "optional": ["person", "location", "subject"], # Changed from participants/agenda
        "types": {"datetime": (str, datetime.datetime), "person": str, "location": str, "subject": str} # Adjusted types
    },
    "set_reminder": {
        "required": ["datetime", "content"],
        "optional": ["priority"],
        "types": {"datetime": (str, datetime.datetime), "content": str, "priority": int}
    },
    "get_reminders": {
        "optional": ["filter", "time_range"],
        "types": {"filter": str, "time_range": str}
    },
    # --- Corrected log_medical rules ---
    "log_medical": {
        "required": ["log_type", "content"], # Requires type and content
        "optional": ["date"],
        "types": {
            "log_type": str,
            "content": str,
            "date": (str, date) # Allow string from LLM or parsed date
        }
    },
    # --- End Correction ---
    "log_investment": { # Assuming investment notes don't require amount/currency? Adjust if needed.
        "required": ["content"],
        "optional": ["title", "tags"],
        "types": {"content": str, "title": str, "tags": list}
    },
    "ask_question": {
        "required": ["question_text"], # Changed from 'question' to match NLU output
        "optional": ["context"],
        "types": {"question_text": str, "context": str}
    },
    "search_information": {
        "required": ["query"], # Changed from 'keywords' for clarity
        "optional": ["filters"],
        "types": {"query": str, "filters": dict}
    },
    "get_summary": { # For daily summary
        "optional": ["date", "period"], # Usually determined by context or defaults
        "types": {"date": (str, date), "period": str}
    },
    "get_note_summary": {
        "optional": ["tags", "keywords", "note_id"], # Allow multiple ways to specify notes
        "types": {"tags": list, "keywords": list, "note_id": (str, int)}
    },
    "query_spending": {
        "optional": ["time_range", "category", "limit", "start_date", "end_date"], # Allow various filters
        "types": {"time_range": str, "category": str, "limit": int, "start_date": (str, date), "end_date": (str, date)}
    },
    "feedback": {"required": ["content"], "optional": ["context"], "types": {"content": str, "context": str}}, # Use content for feedback
    "command": {"required": ["command"], "optional": ["parameters"], "types": {"command": str, "parameters": dict}},
    "unknown": {"required": [], "optional": ["raw_text"], "types": {"raw_text": str}}
 }

REMINDER_QUERY_WORDS = (
    "upcoming meetings", "my reminders", "scheduled meetings", "check reminders",
    "what reminders", "what meetings", "list reminders", "show reminders", "reminders list",
    "schedule", "appointments"
)

# === Enhanced LLM Prompt Engineering ===
# === LLM Prompt Engineering ===
LLM_EXAMPLES = """
Examples:
1. Input: "Remind me to call John at 3pm tomorrow"
   Output: {"intent": "set_reminder", "entities": {"content": "call John", "datetime": "YYYY-MM-DDTHH:MM:SSZ"}}
2. Input: "I spent $45.50 on office supplies today"
   Output: {"intent": "log_spending", "entities": {"amount": 45.50, "description": "office supplies", "currency": "USD", "date": "YYYY-MM-DD"}}
3. Input: "What's my schedule for next week?"
   Output: {"intent": "get_reminders", "entities": {"filter": "next week"}}
4. Input: "Log symptom: headache started this morning"
   Output: {"intent": "log_medical", "entities": {"log_type": "symptom", "content": "headache started this morning", "date": "YYYY-MM-DD"}}
"""
def build_llm_nlu_prompt(text: str) -> str:
    return f"""Analyze input: "{text}"
Intents: {", ".join(VALID_INTENTS)}
Entities: {", ".join(COMMON_ENTITIES)}
Respond ONLY with JSON object: {{"intent": "...", "entities": {{...}}}}
{LLM_EXAMPLES}
JSON Response:"""

# === Advanced Time Parsing ===
def parse_time_expression(text: str) -> Dict[str, Any]:
    """Enhanced time parsing with relative expressions and fallbacks"""
    parsed = {"date": None, "time": None, "datetime": None}
    if not text: return parsed
    now = datetime.datetime.now(timezone.utc)

    if DATEUTIL_AVAILABLE:
        try:
            # Use fuzzy parsing which is good at finding dates/times within text
            dt = dateutil.parser.parse(text, fuzzy=True, default=now)
            # Ensure timezone aware (UTC)
            if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
            else: dt = dt.astimezone(timezone.utc)
            parsed.update({
                "date": dt.date().isoformat(),
                "time": dt.time().isoformat(timespec='seconds'), # Include seconds
                "datetime": dt.isoformat(timespec='seconds') # ISO format with seconds
            })
            logger.debug(f"dateutil parsed '{text}' into: {parsed}")
            return parsed
        except (ValueError, OverflowError, TypeError) as e:
             logger.warning(f"dateutil failed for '{text}': {e}")
             # Don't return here, let regex try below if dateutil fails

    # Fallback relative time parsing (if dateutil failed or not available)
    relative_match = re.search(r'in\s+(\d+)\s+(hour|day|week)s?', text, re.I)
    if relative_match:
        num, unit = relative_match.groups()
        delta = relativedelta(**{f"{unit}s": int(num)})
        future = now + delta
        parsed["datetime"] = future.isoformat(timespec='seconds')
        parsed["date"] = future.date().isoformat()
        parsed["time"] = future.time().isoformat(timespec='seconds')
        logger.debug(f"Relative time parsed '{text}' into: {parsed}")

    # Add more specific regex or keyword checks if needed (e.g., for 'tomorrow')
    elif 'tomorrow' in text.lower():
        tomorrow_date = (now + relativedelta(days=1)).date()
        parsed["date"] = tomorrow_date.isoformat()
        # Try to find time mentioned alongside tomorrow
        time_match = TIME_RELATED.search(text)
        if time_match and DATEUTIL_AVAILABLE:
             try:
                 # Parse just the time part with today's date as default, then add a day
                 time_only_dt = dateutil.parser.parse(time_match.group(0), default=now)
                 final_dt = datetime.datetime.combine(tomorrow_date, time_only_dt.time(), tzinfo=timezone.utc)
                 parsed["datetime"] = final_dt.isoformat(timespec='seconds')
                 parsed["time"] = final_dt.time().isoformat(timespec='seconds')
             except Exception as e:
                 logger.warning(f"Could not parse time with 'tomorrow': {e}")
        logger.debug(f"Parsed 'tomorrow' in '{text}' into: {parsed}")


    return parsed

# === Enhanced Rule-Based Processing ===
def rule_based_processing(text: str) -> Dict[str, Any]:
    """Advanced pattern matching with context awareness"""
    result = {"intent": "unknown", "entities": {}}
    if not text: return result
    text = text.strip(); text_lower = text.lower()
    
    #     # Check for reminder-related queries
    # if any(phrase in text_lower for phrase in REMINDER_QUERY_WORDS):
    #     result["intent"] = "get_reminders"
    #     result["entities"] = {}  # Add any additional entities if needed
    #     logger.debug(f"Matched 'get_reminders' intent using REMINDER_QUERY_WORDS.")
    #     return result

    # Check all intent patterns
    for intent_key, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            # --- FIX: Use the compiled pattern directly ---
            # Remove the incorrect .format() call
            compiled_pattern = pattern
            # --- End Fix ---
            match = compiled_pattern.search(text)
            if match:
                logger.debug(f"Regex pattern matched for intent '{intent_key}'")
                result["intent"] = intent_key
                result["entities"] = extract_entities(intent_key, match.groups(), text)
                if validate_entities(intent_key, result["entities"]):
                    logger.debug(f"--> RULE Matched & Validated: {result['intent']}")
                    return result # Return first valid match
                else:
                    logger.warning(f"Rule matched '{intent_key}' but entities failed validation: {result['entities']}")
                    result["intent"] = "unknown" # Reset if invalid entities


    # Specialized checks if no pattern matched above
    if result["intent"] == "unknown":
        if any(q_word in text_lower for q_word in ("schedule", "plan", "arrange")) and TIME_RELATED.search(text):
            result["intent"] = "schedule_meeting"
            result["entities"] = parse_time_expression(text)
            result["entities"]["subject"] = text # Default subject
            if validate_entities(result["intent"], result["entities"]):
                 logger.debug(f"--> RULE Matched intent (specialized): {result['intent']}")
                 return result
            else: result["intent"] = "unknown"

    # Add more specialized rule checks here...
    return result # Return unknown if no rules matched

def extract_entities(intent: str, match_groups: tuple, original_text: str) -> Dict:
    """Entity extraction based on intent patterns, includes time parsing"""
    entities = {}
    if not match_groups: return entities
    logger.debug(f"Extracting entities for intent '{intent}' from groups: {match_groups}")
    try:
        if intent == "log_spending":
            # Determine pattern match based on group content
            if '$' in match_groups[1] or '£' in match_groups[1] or '€' in match_groups[1] or '₹' in match_groups[1] or '¥' in match_groups[1]: # Pattern 1 likely
                amount_str = match_groups[1]; entities["description"] = match_groups[2].strip() if len(match_groups) > 2 and match_groups[2] else "Miscellaneous"
            else: # Pattern 2 likely
                amount_str = match_groups[2]; entities["description"] = match_groups[1].strip() if len(match_groups) > 1 and match_groups[1] else "Miscellaneous"
            entities["amount"] = float(re.sub(r'[^\d.,]', '', amount_str).replace(',', '.'))
            currency_match = re.search(CURRENCY_REGEX, amount_str); entities["currency"] = currency_match.group(0) if currency_match else "USD"

        elif intent == "schedule_meeting":
            # Pattern 1: (verb) (with person) (at/on time/date) (to discuss subject)
            # Pattern 2: (verb) (appointment/demo) (for/on time/date)
            if len(match_groups) >= 3 and ('appointment' in match_groups[1] or 'demo' in match_groups[1]): # Pattern 2
                 time_text = match_groups[2]; entities["subject"] = match_groups[1].strip().capitalize()
            else: # Pattern 1
                 time_text = match_groups[2] if len(match_groups) > 2 else ""
                 entities["person"] = match_groups[1].strip() if len(match_groups) > 1 else None
                 # Use specific subject if provided, otherwise construct from person
                 entities["subject"] = match_groups[3].strip() if len(match_groups) > 3 and match_groups[3] else f"Meeting with {entities.get('person', '...')}"
            entities.update(parse_time_expression(time_text)) # Parse time/date from the relevant group

        elif intent == "set_reminder":
            # Pattern 1: (verb) (to/about content) (at/on time/date)
            # Pattern 2: (emoji) (content) - (time/date)
            if len(match_groups) >= 3: # Pattern 1 likely
                 time_text = match_groups[2]; entities["content"] = match_groups[1].strip() # Extract content after "to/about"
            else: # Pattern 2 likely
                 time_text = match_groups[1]; entities["content"] = match_groups[0].strip()
            entities.update(parse_time_expression(time_text)) # Parse time/date

    except IndexError: logger.warning(f"Index error during entity extraction for intent {intent}")
    except ValueError: logger.warning(f"Value error during entity extraction for intent {intent}")
    except Exception as e: logger.error(f"Unexpected error during entity extraction: {e}", exc_info=True)

    entities["raw_text"] = original_text # Always include raw text
    logger.debug(f"Extracted Entities: {entities}")
    return entities
# --- End Entity Extraction ---

def validate_entities(intent: str, entities: Dict) -> bool:
    """Validate entities against intent requirements"""
    rules = ENTITY_VALIDATION.get(intent, {})
    for field in rules.get("required", []):
        if field not in entities or entities.get(field) is None: # Check for None as well
            logger.debug(f"Validation failed for {intent}: Missing required entity '{field}'")
            return False
    for field, types in rules.get("types", {}).items():
        # Allow optional fields to be missing
        if field in entities and entities.get(field) is not None:
             # Handle Union types if specified in rules (e.g., (str, datetime.datetime))
             if isinstance(types, tuple):
                 if not isinstance(entities.get(field), types):
                     logger.debug(f"Validation failed for {intent}: Entity '{field}' type {type(entities.get(field))} not in {types}")
                     return False
             # Handle single type
             elif not isinstance(entities.get(field), types):
                 logger.debug(f"Validation failed for {intent}: Entity '{field}' type {type(entities.get(field))}, expected {types}")
                 return False
    logger.debug(f"Entity validation passed for intent '{intent}'")
    return True

async def get_nlu_results_hybrid(text: str, user_context: Dict = None) -> Dict[str, Any]:
    """Advanced hybrid processing with validation and context awareness"""
    logger.debug(f"Processing: '{text}'")
    rule_result = rule_based_processing(text) # Try rules first

    if rule_result["intent"] != "unknown":
        logger.info(f"Rule-based match successful: {rule_result}")
        return rule_result # Return if rule matched and validated

    # If rules failed or didn't match, fall back to LLM
    logger.info(f"No valid rule match. Falling back to LLM NLU: '{text}'")
    llm_result = await get_intent_and_entities_from_llm(text)

    # Validate LLM result before returning
    if llm_result["intent"] != "unknown":
         if validate_entities(llm_result["intent"], llm_result["entities"]):
             logger.info(f"LLM NLU valid result: {llm_result}")
             llm_result["entities"]["llm_fallback"] = True # Mark as LLM result
             return llm_result
         else:
             logger.warning(f"LLM NLU result failed entity validation: {llm_result}")
             # Optionally keep entities even if validation fails? Or discard? Discarding for now.
             llm_result["intent"] = "unknown" # Treat as unknown if validation fails

    # Final Fallback if both rules and LLM NLU fail or return unknown/invalid
    logger.info("Rules and LLM NLU failed or returned unknown. Using final fallback.")
    final_intent = "save_note" if len(text) > 10 else "unknown" # Basic heuristic
    final_entities = {"content": text} if final_intent == "save_note" else {"raw_text": text}
    if "llm_error" in llm_result.get("entities", {}): # Preserve LLM error if it occurred
        final_entities["llm_error"] = llm_result["entities"]["llm_error"]
    if "parsing_error" in llm_result.get("entities", {}):
         final_entities["parsing_error"] = llm_result["entities"]["parsing_error"]

    return {"intent": final_intent, "entities": final_entities}


def extract_json(text: str) -> str:
    """Robust JSON extraction using multiple methods"""
    if not text or not isinstance(text, str): return ""
    # Method 1: Look for JSON blocks ```json ... ```
    json_match = re.search(r'```json\s*({.*?})\s*```', text, re.DOTALL)
    if json_match: return json_match.group(1)
    # Method 2: Find first '{' and last '}'
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        potential_json = text[start:end+1]
        try: json.loads(potential_json); return potential_json # Check if valid JSON
        except json.JSONDecodeError: pass
    return "" # Return empty if no valid JSON found

def filter_entities(entities: Dict) -> Dict:
    """Filter entities to only include valid fields"""
    if not isinstance(entities, dict): return {}
    return {k: v for k, v in entities.items() if k in COMMON_ENTITIES}

def validate_llm_response(response: Dict) -> bool:
    """Comprehensive response validation"""
    if not isinstance(response, dict): return False
    intent = response.get("intent")
    entities = response.get("entities", {})
    if intent not in VALID_INTENTS: return False
    if not isinstance(entities, dict): return False
    # Check if all keys in entities are allowed common entities
    if not all(k in COMMON_ENTITIES for k in entities.keys()): return False
    # Optionally add type checks for specific entities extracted by LLM if needed
    return True

async def get_intent_and_entities_from_llm(text: str) -> Dict[str, Any]:
    """Improved LLM response handling with validation"""
    result = {"intent": "unknown", "entities": {}}; logger.debug(f"--- Calling LLM for NLU: '{text}' ---")
    try:
        llm_service = get_llm_service(); prompt = build_llm_nlu_prompt(text)
        response = await llm_service.generate_text(prompt=prompt, max_tokens=300, temperature=0.1)
        logger.debug(f"Raw LLM NLU response: {response}")
        json_str = extract_json(response)
        if json_str:
            try:
                parsed = json.loads(json_str)
                if validate_llm_response(parsed):
                    result["intent"] = parsed["intent"]
                    result["entities"] = filter_entities(parsed.get("entities", {}))
                    logger.info(f"LLM NLU Parsed: {result}")
                else: logger.warning(f"LLM JSON invalid structure or intent: {parsed}")
            except json.JSONDecodeError as e: logger.error(f"LLM JSON Decode Error: {e} - Response: {json_str}")
        else: logger.warning(f"LLM response had no JSON: {response}")
    except Exception as e: logger.error(f"LLM NLU service error: {e}", exc_info=True); result["entities"]["llm_error"] = str(e)
    return result
