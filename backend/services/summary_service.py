# backend/services/summary_service.py
import logging
from typing import List, Dict, Any

from backend.services.llm import get_llm_service # Import the factory

logger = logging.getLogger(__name__)

async def generate_daily_summary(data_to_summarize: List[Dict[str, Any]], user_preferences: Dict = None) -> str:
    """
    Generates a daily summary using the configured LLM provider.
    """
    item_count = len(data_to_summarize)
    logger.info(f"Summary Service: Generating daily summary for {item_count} items.")

    if not data_to_summarize:
        return "Nothing significant found to summarize for the specified period."

    # --- Prepare input for LLM ---
    # Format the logs into a string or structured list suitable for the LLM prompt
    formatted_logs = []
    for item in data_to_summarize:
        item_type = item.get("type", "log")
        content = item.get("content", "N/A")
        timestamp = item.get("timestamp")
        time_str = timestamp.strftime('%H:%M') if timestamp and hasattr(timestamp, 'strftime') else ''
        formatted_logs.append(f"- {time_str} ({item_type}): {content}")

    log_text = "\n".join(formatted_logs)
    prompt = f"Provide a brief summary of the key events and activities from the following daily logs:\n\n{log_text}\n\nSummary:"

    # --- Get LLM Service and Generate ---
    try:
        llm_service = get_llm_service()
        # --- Use await for ALL providers since base methods are async ---
        summary = await llm_service.generate_summary(documents=[log_text])
        # --- End Fix ---
        return summary
    except Exception as e:
        logger.error(f"Error generating daily summary via LLM: {e}", exc_info=True)
        return "[Error: Failed to generate summary using AI service]"


async def generate_note_summary(notes_content: List[str], criteria_tags: List[str] = None, criteria_keywords: List[str] = None) -> str:
    """
    Generates a summary of notes using the configured LLM provider.
    """
    note_count = len(notes_content)
    logger.info(f"Summary Service: Generating note summary for {note_count} notes.")

    if not notes_content:
        return "No notes found matching the criteria to summarize."

    criteria_desc = [];
    if criteria_tags: criteria_desc.append(f"tags: {', '.join(criteria_tags)}")
    if criteria_keywords: criteria_desc.append(f"keywords: {', '.join(criteria_keywords)}")
    criteria_str = f" based on {', '.join(criteria_desc)}" if criteria_desc else ""
    full_text = "\n\n---\n\n".join(notes_content) # TODO: Handle length limits
    prompt = f"Summarize the key points from the following {note_count} note(s){criteria_str}:\n\n{full_text}\n\nSummary:"

    try:
        llm_service = get_llm_service()
        # --- Use await for ALL providers since base methods are async ---
        summary = await llm_service.generate_summary(documents=[full_text])
        # --- End Fix ---
        return summary
    except Exception as e:
        logger.error(f"Error generating note summary via LLM: {e}", exc_info=True)
        return "[Error: Failed to generate note summary using AI service]"
