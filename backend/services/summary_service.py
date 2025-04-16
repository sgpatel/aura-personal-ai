# backend/services/summary_service.py
import logging; from typing import List, Dict, Any, Optional; from backend.services.llm import get_llm_service; from backend.core.config import logger
logger = logging.getLogger(__name__)
async def generate_daily_summary(data_to_summarize: List[Dict[str, Any]], user_preferences: Dict = None) -> str:
    if not data_to_summarize: return "No activities found for this period."
    timeline_entries = [f"{item.get('timestamp', '')} - {item.get('type', 'event').upper()}: {item.get('content', '')}" for item in data_to_summarize]
    activities_str = '\n'.join(timeline_entries); prompt = f"""Analyze daily activities:\n{activities_str}\nProvide:\n1. Time-bound summary\n2. Notable patterns\n3. Follow-ups\nSummary:"""
    try: llm = get_llm_service(); return await llm.generate_text(prompt=prompt, max_tokens=500)
    except Exception as e: logger.error(f"Daily summary error: {e}"); return "Couldn't generate daily summary. Raw entries:\n" + '\n'.join(timeline_entries[:5])
async def generate_note_summary(notes_content: List[str], criteria_tags: List[str] = None, criteria_keywords: List[str] = None) -> str:
    if not notes_content: return "No notes available for summarization."
    criteria_desc = [];
    if criteria_tags: criteria_desc.append(f"tags: {', '.join(criteria_tags)}")
    if criteria_keywords: criteria_desc.append(f"keywords: {', '.join(criteria_keywords)}")
    notes_str = '\n---\n'.join(notes_content[:10]); prompt = f"""Synthesize insights from notes{' filtered by ' + ' and '.join(criteria_desc) if criteria_desc else ''}:\nNotes:\n{notes_str}\nIdentify:\n1. Core themes\n2. Contradictions\n3. Actionable points\n4. Gaps\nSummary:"""
    try: llm = get_llm_service(); return await llm.generate_text(prompt=prompt, temperature=0.3)
    except Exception as e: logger.error(f"Note summary error: {e}"); return "Summary unavailable. Excerpts:\n" + '\n'.join(n[:100] for n in notes_content[:3])
async def generate_spending_summary(spending_data: List[Dict], time_range: str = "month") -> str:
    if not spending_data: return "No spending records found."
    total = sum(float(item['amount']) for item in spending_data); currency = spending_data[0].get('currency', 'USD') if spending_data else 'USD' # Get currency from first item
    breakdown = [f"- {item['date']}: {currency}{item['amount']:.2f} [{item.get('category', 'uncat.')}] {item.get('description', '')}" for item in spending_data]
    breakdown_str = '\n'.join(breakdown); prompt = f"""Analyze spending (Total: {currency}{total:.2f}):\n{breakdown_str}\nProvide:\n1. Trends by category\n2. Unusual expenditures\n3. Comparisons\n4. Budget suggestions\nAnalysis:"""
    try: llm = get_llm_service(); return await llm.generate_text(prompt=prompt, max_tokens=600)
    except Exception as e: logger.error(f"Spending summary error: {e}"); return f"Total spending: {currency}{total:.2f}\n" + '\n'.join(breakdown[:5])
async def generate_search_summary(results: List[Dict], query: str, context: Dict = None) -> str:
    if not results: return f"No results found for '{query}'."
    context_str = f" in context of {context['topic']}" if context and context.get('topic') else ""
    documents_str = '\n\n'.join(r.get('content','')[:500] for r in results) # Use get with default
    prompt = f"""Synthesize results for "{query}"{context_str}:\nDocuments:\n{documents_str}\nInclude:\n1. Relevance\n2. Findings\n3. Reliability\n4. Missing info\nSynthesis:"""
    try: llm = get_llm_service(); return await llm.generate_text(prompt=prompt, temperature=0.4, max_tokens=700)
    except Exception as e: logger.error(f"Search summary error: {e}"); return f"Top results for '{query}':\n" + '\n'.join(r.get('title', r.get('content',''))[:50] for r in results[:3]) # Use get with default
async def generate_meeting_summary(transcript: str, participants: List[str]) -> str:
    transcript_str = transcript[:5000]; participants_str = ', '.join(participants)
    prompt = f"""Convert transcript to minutes:\nParticipants: {participants_str}\nTranscript:\n{transcript_str}\nInclude:\n1. Decisions\n2. Action items\n3. Topics\n4. Follow-ups\nMinutes:"""
    try: llm = get_llm_service(); return await llm.generate_text(prompt=prompt, temperature=0.1, max_tokens=800)
    except Exception as e: logger.error(f"Meeting summary error: {e}"); return "Minutes unavailable. Transcript start:\n" + transcript[:500]

