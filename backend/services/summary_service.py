# backend/services/summary_service.py
import logging
from typing import List, Dict, Any, Optional

from backend.services.llm import get_llm_service
from backend.core.config import logger

logger = logging.getLogger(__name__)

async def generate_daily_summary(data_to_summarize: List[Dict[str, Any]], user_preferences: Dict = None) -> str:
    """Generates daily summary with temporal analysis and highlights"""
    if not data_to_summarize:
        return "No activities found for this period."
    
    # Structure data for LLM processing
    timeline_entries = [
        f"{item.get('timestamp', '')} - {item.get('type', 'event').upper()}: "
        f"{item.get('content', '')}" 
        for item in data_to_summarize
    ]
    
    # Create formatted strings first
    activities_str = '\n'.join(timeline_entries)
    prompt = f"""Analyze these daily activities and provide:
1. Time-bound summary of key events
2. Notable patterns or anomalies
3. Suggested follow-ups if any

Activities:
{activities_str}

Summary:"""
    
    try:
        llm = get_llm_service()
        return await llm.generate_text(prompt=prompt, max_tokens=500)
    except Exception as e:
        logger.error(f"Daily summary error: {e}")
        return "Couldn't generate daily summary. Showing raw entries:\n" + '\n'.join(timeline_entries[:5])

async def generate_note_summary(notes_content: List[str], criteria_tags: List[str] = None, criteria_keywords: List[str] = None) -> str:
    """Generates thematic summary with concept linking"""
    if not notes_content:
        return "No notes available for summarization."
    
    # Build criteria description
    criteria_desc = []
    if criteria_tags:
        criteria_desc.append(f"tags: {', '.join(criteria_tags)}")
    if criteria_keywords:
        criteria_desc.append(f"keywords: {', '.join(criteria_keywords)}")
    
    # Format notes content
    notes_str = '\n---\n'.join(notes_content[:10])  # Limit to first 10 notes
    prompt = f"""Synthesize key insights from these notes{' filtered by ' + ' and '.join(criteria_desc) if criteria_desc else ''}:

Notes:
{notes_str}

Identify:
1. Core themes
2. Contradictions
3. Actionable points
4. Knowledge gaps

Summary:"""
    
    try:
        llm = get_llm_service()
        return await llm.generate_text(prompt=prompt, temperature=0.3)
    except Exception as e:
        logger.error(f"Note summary error: {e}")
        return "Summary unavailable. Here are key excerpts:\n" + '\n'.join(n[:100] for n in notes_content[:3])

async def generate_spending_summary(spending_data: List[Dict], time_range: str = "month") -> str:
    """Generates financial analysis with trend detection"""
    if not spending_data:
        return "No spending records found."
    
    # Process data for LLM
    total = sum(float(item['amount']) for item in spending_data)
    breakdown = [
        f"- {item['date']}: {item['currency']}{item['amount']} "
        f"[{item.get('category', 'uncategorized')}] {item.get('description', '')}"
        for item in spending_data
    ]
    
    # Format breakdown
    breakdown_str = '\n'.join(breakdown)
    prompt = f"""Analyze these spending records (Total: {total:.2f}):

{breakdown_str}

Provide:
1. Spending trends by category
2. Unusual expenditures
3. Weekly/monthly comparisons
4. Budgeting suggestions

Analysis:"""
    
    try:
        llm = get_llm_service()
        return await llm.generate_text(prompt=prompt, max_tokens=600)
    except Exception as e:
        logger.error(f"Spending summary error: {e}")
        return f"Total spending: {total:.2f}\n" + '\n'.join(breakdown[:5])

async def generate_search_summary(results: List[Dict], query: str, context: Dict = None) -> str:
    """Generates contextual search results synthesis"""
    if not results:
        return f"No results found for '{query}'."
    
    # Build context string
    context_str = f" in the context of {context['topic']}" if context and context.get('topic') else ""
    
    # Format document content
    documents_str = '\n\n'.join(r['content'][:500] for r in results)
    prompt = f"""Synthesize results for "{query}"{context_str}:

Documents:
{documents_str}

Include:
1. Relevance assessment
2. Key findings
3. Source reliability indicators
4. Missing information

Synthesis:"""
    
    try:
        llm = get_llm_service()
        return await llm.generate_text(
            prompt=prompt,
            temperature=0.4,
            max_tokens=700
        )
    except Exception as e:
        logger.error(f"Search summary error: {e}")
        return f"Top results for '{query}':\n" + '\n'.join(r['title'] for r in results[:3])

async def generate_meeting_summary(transcript: str, participants: List[str]) -> str:
    """Generates structured meeting minutes from raw transcript"""
    # Format transcript
    transcript_str = transcript[:5000]  # Truncate to 5000 characters
    participants_str = ', '.join(participants)
    
    prompt = f"""Convert this meeting transcript into structured minutes:

Participants: {participants_str}
Transcript:
{transcript_str}

Include:
1. Key decisions
2. Action items (owner, deadline)
3. Discussion topics
4. Follow-up requirements

Meeting Minutes:"""
    
    try:
        llm = get_llm_service()
        return await llm.generate_text(
            prompt=prompt,
            temperature=0.1,
            max_tokens=800
        )
    except Exception as e:
        logger.error(f"Meeting summary error: {e}")
        return "Couldn't generate minutes. Here's the raw transcript start:\n" + transcript[:500]