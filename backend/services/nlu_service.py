# backend/services/nlu_service.py
# Enhanced Hybrid NLU with Advanced Intent Recognition
import logging
from typing import Dict, Any, List
import json
import re
import datetime
from datetime import timezone
from collections import defaultdict

# Enhanced dateutil integration
try:
    import dateutil.parser
    from dateutil.relativedelta import relativedelta
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False

from backend.services.llm import get_llm_service
from backend.core.config import logger

logger = logging.getLogger("aura_backend.nlu")
logger.setLevel(logging.DEBUG)

# === Intent Taxonomy ===
VALID_INTENTS = [
    # Data Logging
    "save_note", "log_spending", "log_investment", "log_medical",
    # Scheduling
    "set_reminder", "schedule_meeting", "modify_event",
    # Queries
    "get_summary", "get_note_summary", "get_reminders", "query_spending",
    # Knowledge
    "ask_question", "search_information",
    # System
    "unknown", "command", "feedback"
]

# === Entity Ontology ===
COMMON_ENTITIES = [
    # Core
    "content", "amount", "currency", "description",
    # Temporal
    "date", "time", "datetime", "timezone", "duration",
    # Categorization
    "category", "tags", "keywords", "log_type", "priority",
    # Querying
    "filter", "time_range", "limit", "sort_by",
    # Relationships
    "person", "location", "organization",
    # System
    "confidence", "raw_text", "llm_fallback"
]

# === Intent Patterns (expanded from previous) ===
INTENT_PATTERNS = {
    "log_spending": [
        re.compile(r'(spent|spend|expensed?|paid)\s+((?:{currencies})?[0-9,.]+\b)(?:\s+?(?:on|for)\s+(.+))', re.I),
        re.compile(r'(bought|purchased)\s+(.+?)\s+for\s+((?:{currencies})?[0-9,.]+)', re.I)
    ],
    "schedule_meeting": [
        re.compile(r'(meet|meeting|call)\s+(?:with\s+)?(.+?)\s+(?:at|on)\s+(.+?)(?:\s+to\s+discuss\s+(.+))?', re.I),
        re.compile(r'(schedule|arrange)\s+(?:a\s+)?(appointment|demo)\s+(?:for|on)\s+(.+)', re.I)
    ],
    "set_reminder": [
        re.compile(r'(remind me|set reminder|alert me)\s+(?:to|about)\s+(.+?)\s+(at|on)\s+(.+)', re.I),
        re.compile(r'(?:⏰|❗)\s*(.+?)\s+-\s+(.+)', re.I)
    ]
}

TIME_RELATED = re.compile(
    r'\b(\d{1,2}(?:[:.]\d{2})?\s*(?:am|pm)?)|'
    r'(next\s+(week|month|year|monday|tuesday|wednesday|thursday|friday|saturday|sunday))|'
    r'(in\s+\d+\s+(hours?|days?|weeks?))|'
    r'(tomorrow|tonight|today|noon|midnight)\b', re.I
)

CURRENCY_SYMBOLS = {'$', '£', '€', '₹', '¥'}
QUESTION_PATTERN = re.compile(
    r'^(can you|could you|would you|please|how to|what\'?s?|who\'?s?|where|when|why|how)\b', re.I
)

# === Entity Validation Rules ===
ENTITY_VALIDATION = {
    "log_spending": {
        "required": ["amount"],
        "optional": ["currency", "description", "category"],
        "types": {
            "amount": (int, float),
            "currency": (str),
            "category": (str)
        }
    },
    "schedule_meeting": {
        "required": ["datetime"],
        "optional": ["participants", "location", "agenda"],
        "types": {
            "datetime": (str, datetime.datetime),
            "duration": (int, float)
        }
    },
    "set_reminder": {
        "required": ["datetime"],
        "optional": ["content", "priority"],
        "types": {
            "datetime": (str, datetime.datetime),
            "priority": (int)
        }
    },
    "get_reminders": {
        "optional": ["filter", "time_range"],
        "types": {
            "filter": (str),
            "time_range": (str)
        }
    },
    "log_investment": {
        "required": ["amount", "currency"],
        "optional": ["description", "category"],
        "types": {
            "amount": (int, float),
            "currency": (str),
            "category": (str)
        }
    },
    "log_medical": {
        "required": ["description", "amount"],
        "optional": ["category"],
        "types": {
            "description": (str),
            "amount": (int, float),
            "category": (str)
        }
    },
    "ask_question": {
        "required": ["question"],
        "optional": ["context"],
        "types": {
            "question": (str),
            "context": (str)
        }
    },
    "search_information": {
        "required": ["query"],
        "optional": ["filters"],
        "types": {
            "query": (str),
            "filters": (dict)
        }
    },
    "get_summary": {
        "required": ["content"],
        "optional": ["context"],
        "types": {
            "content": (str),
            "context": (str)
        }
    },
    "get_note_summary": {
        "required": ["note_id"],
        "optional": ["context"],
        "types": {
            "note_id": (str),
            "context": (str)
        }
    },
    "query_spending": {
        "required": ["time_range"],
        "optional": ["category", "limit"],
        "types": {
            "time_range": (str),
            "category": (str),
            "limit": (int)
        }
    },
    "feedback": {
        "required": ["feedback"],
        "optional": ["context"],
        "types": {
            "feedback": (str),
            "context": (str)
        }
    },
    "command": {
        "required": ["command"],
        "optional": ["parameters"],
        "types": {
            "command": (str),
            "parameters": (dict)
        }
    },
    "unknown": {
        "required": [],
        "optional": ["raw_text"],
        "types": {
            "raw_text": (str)
        }
    }
}

# === Enhanced LLM Prompt Engineering ===
LLM_EXAMPLES = """
Examples:
1. Input: "Remind me to call John at 3pm tomorrow"
   Output: {"intent": "set_reminder", "entities": {"content": "call John", "datetime": "2024-03-21T15:00:00Z"}}

2. Input: "I spent $45.50 on office supplies"
   Output: {"intent": "log_spending", "entities": {"amount": 45.50, "description": "office supplies"}}

3. Input: "What's my schedule for next week?"
   Output: {"intent": "get_reminders", "entities": {"filter": "next week"}}
"""

def build_llm_nlu_prompt(text: str) -> str:
    """ Constructs an enhanced prompt with examples and formatting guidance. """
    return f"""Perform detailed intent classification and entity extraction. Follow these steps:

1. Analyze the user's input for key actions and context
2. Identify the most specific intent from: {", ".join(VALID_INTENTS)}
3. Extract relevant entities using schema: {", ".join(COMMON_ENTITIES)}
4. Format response as JSON with "intent" and "entities" keys

{LLM_EXAMPLES}

Current Input: "{text}"
JSON Response:"""

# === Advanced Time Parsing ===
def parse_time_expression(text: str) -> Dict[str, Any]:

    """Handle null/empty input"""
    parsed = {"date": None, "time": None, "datetime": None}
    if not text:
        return parsed
    
    """Enhanced time parsing with relative expressions and fallbacks"""
    now = datetime.datetime.now(timezone.utc)
    parsed = {"date": None, "time": None, "datetime": None}
    
    if DATEUTIL_AVAILABLE:
        try:
            dt = dateutil.parser.parse(text, fuzzy=True, default=now)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            parsed.update({
                "date": dt.date().isoformat(),
                "time": dt.time().isoformat(),
                "datetime": dt.isoformat()
            })
            return parsed
        except:
            pass

    # Fallback relative time parsing
    relative_match = re.search(r'in\s+(\d+)\s+(hour|day|week)s?', text, re.I)
    if relative_match:
        num, unit = relative_match.groups()
        delta = relativedelta(**{f"{unit}s": int(num)})
        future = now + delta
        parsed["datetime"] = future.isoformat()
    
    return parsed

# === Enhanced Rule-Based Processing ===
def rule_based_processing(text: str) -> Dict[str, Any]:
    """Add null check for text input"""
    result = {"intent": "unknown", "entities": {}}
    if not text:
        return result
    
    text = text.strip()

    """Advanced pattern matching with context awareness"""
    result = {"intent": "unknown", "entities": {}}
    text_lower = text.lower()
    
    # Check all intent patterns
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                result["intent"] = intent
                result["entities"] = extract_entities(intent, match.groups())
                if validate_entities(intent, result["entities"]):
                    return result
                else:
                    result["intent"] = "unknown"  # Reset if invalid
    
    # Specialized checks
    if any(q_word in text_lower for q_word in ("schedule", "plan", "arrange")) and TIME_RELATED.search(text):
        result["intent"] = "schedule_meeting"
        result["entities"] = parse_time_expression(text)
    
    return result

def extract_entities(intent: str, match_groups: tuple) -> Dict:

    """Add null safety checks"""
    entities = {}
    if not match_groups:
        return entities
    try:
        """Entity extraction based on intent patterns"""
        if intent == "log_spending":
            entities["amount"] = float(match_groups[0].replace(',', '.'))
            entities["description"] = match_groups[1] if len(match_groups) > 1 else "Miscellaneous"
        elif intent == "schedule_meeting" and len(match_groups) >= 4:
                # Add index checks
                time_text = match_groups[-1] if match_groups else ""
                entities.update(parse_time_expression(time_text))
                entities["subject"] = match_groups[1] if len(match_groups) > 1 else "Meeting"
    except IndexError:
        logger.warning("Match groups index error during entity extraction")
    return entities

def validate_entities(intent: str, entities: Dict) -> bool:
    """Validate entities against intent requirements"""
    validation_rules = ENTITY_VALIDATION.get(intent, {})
    for field in validation_rules.get("required", []):
        if field not in entities:
            return False
    for field, types in validation_rules.get("types", {}).items():
        if not isinstance(entities.get(field), types):
            return False
    return True

# === Enhanced Hybrid Processing ===
async def get_nlu_results_hybrid(text: str, user_context: Dict = None) -> Dict[str, Any]:
    """Advanced hybrid processing with validation and context awareness"""
    logger.debug(f"Processing: '{text}'")
    
    # 1. Enhanced Rule-Based Analysis
    rule_result = rule_based_processing(text)
    if rule_result["intent"] != "unknown":
        logger.info(f"Rule-based match: {rule_result}")
        return rule_result
    
    # 2. Context-Aware LLM Fallback
    llm_result = await get_intent_and_entities_from_llm(text)
    if llm_result["intent"] != "unknown":
        if validate_entities(llm_result["intent"], llm_result["entities"]):
            logger.info(f"LLM valid result: {llm_result}")
            return llm_result
    
    # 3. Final Fallback with Semantic Analysis
    return {
        "intent": "save_note" if len(text) > 15 else "unknown",
        "entities": {"content": text}
    }

# === Enhanced LLM Response Processing ===
async def get_intent_and_entities_from_llm(text: str) -> Dict[str, Any]:
    """Improved LLM response handling with validation"""
    result = {"intent": "unknown", "entities": {}}
    try:
        llm_service = get_llm_service()
        prompt = build_llm_nlu_prompt(text)
        response = await llm_service.generate_text(prompt=prompt, max_tokens=300, temperature=0.1)
        
        # Robust JSON extraction
        json_str = extract_json(response)
        if json_str:
            parsed = json.loads(json_str)
            if validate_llm_response(parsed):
                result["intent"] = parsed["intent"]
                result["entities"] = filter_entities(parsed.get("entities", {}))
    
    except Exception as e:
        logger.error(f"LLM processing error: {e}")
    
    return result

def extract_json(text: str) -> str:
    """Robust JSON extraction using multiple methods"""
    # Method 1: Look for JSON blocks
    json_match = re.search(r'```json\n({.*?})\n```', text, re.DOTALL)
    if json_match:
        return json_match.group(1)
    
    # Method 2: Find first valid JSON
    for match in re.finditer(r'{.*}', text):
        try:
            json.loads(match.group())
            return match.group()
        except:
            continue
    return ""

def filter_entities(entities: Dict) -> Dict:
    """Filter entities to only include valid fields"""
    return {k: v for k, v in entities.items() if k in COMMON_ENTITIES}

def validate_llm_response(response: Dict) -> bool:
    """Comprehensive response validation"""
    return (
        response.get("intent") in VALID_INTENTS and
        isinstance(response.get("entities", {}), dict) and
        all(k in COMMON_ENTITIES for k in response.get("entities", {}).keys())
    )