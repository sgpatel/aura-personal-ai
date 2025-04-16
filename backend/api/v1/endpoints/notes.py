# backend/api/v1/endpoints/notes.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import datetime
from typing import List, Optional
from backend.db.session import get_db
from backend.schemas.note import Note, NoteCreate, NotesOutput, NoteUpdate, NoteSummaryOutput
from backend.schemas.user import User
from backend.schemas.api_models import Message
from backend.api import deps
from backend import crud
from backend.core.config import logger
from backend.services import summary_service

router = APIRouter()

@router.post("/", response_model=Note, status_code=status.HTTP_201_CREATED)
async def create_new_note(note_in: NoteCreate, db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_active_user)):
    note_db = crud.note.create_with_owner(db=db, obj_in=note_in, user_id=current_user.id); 
    logger.info(f"Note {note_db.id} created for user {current_user.id}"); return note_db

@router.get("/global", response_model=NotesOutput)
async def read_global_notes(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
    start_date: Optional[datetime.date] = Query(None, description="Filter notes created from this date"),
    end_date: Optional[datetime.date] = Query(None, description="Filter notes created up to this date"),
    skip: int = 0,
    limit: int = 100,
):
    """Retrieve global notes for the current user, optionally filtered by creation date."""
    notes_db = crud.note.get_global(
        db=db,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,  # Pass filters to CRUD
        skip=skip,
        limit=limit,
    )
    return NotesOutput(notes=notes_db)

# --- Path Changed back to /important/{date_str} ---
@router.get("/important/{date_str}", response_model=NotesOutput)
async def read_important_notes_for_date( # Renamed function for clarity
    date_str: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """ Retrieve notes associated with a specific date (marked as important implicitly by being dated). """
    try: target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError: raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    # Assuming get_by_date fetches notes relevant for that day (non-global)
    notes_db = crud.note.get_by_date(db=db, user_id=current_user.id, date=target_date);
    return NotesOutput(notes=notes_db)
# --- End Path Change ---

@router.get("/summary", response_model=NoteSummaryOutput)
async def summarize_notes_by_criteria(tags: Optional[List[str]] = Query(None), keywords: Optional[List[str]] = Query(None), limit: int = Query(50, le=200), db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_active_user)):
    if not tags and not keywords: raise HTTPException(status_code=400, detail="Provide 'tags' or 'keywords'.")
    notes_to_summarize = crud.note.get_notes_by_tags_keywords(db=db, user_id=current_user.id, tags=tags, keywords=keywords, limit=limit)
    if not notes_to_summarize: raise HTTPException(status_code=404, detail="No notes found.")
    notes_content = [note.content for note in notes_to_summarize]
    try: summary = await summary_service.generate_note_summary(notes_content=notes_content, criteria_tags=tags, criteria_keywords=keywords)
    except Exception as e: logger.error(f"Note Summary Service error: {e}", exc_info=True); raise HTTPException(status_code=500, detail="Error generating summary.")
    return NoteSummaryOutput(summary=summary, criteria_tags=tags, criteria_keywords=keywords, note_count=len(notes_to_summarize))

@router.get("/{note_id}", response_model=Note)
async def read_note_by_id(note_id: int, db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_active_user)):
    note_db = crud.note.get(db=db, id=note_id)
    if not note_db: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    if note_db.user_id != current_user.id: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return note_db

@router.put("/{note_id}", response_model=Note)
async def update_note_by_id(note_id: int, note_in: NoteUpdate, db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_active_user)):
    note_db = crud.note.get(db=db, id=note_id)
    if not note_db: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    if note_db.user_id != current_user.id: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    updated_note = crud.note.update(db=db, db_obj=note_db, obj_in=note_in); return updated_note

@router.delete("/{note_id}", response_model=Message)
async def delete_note_by_id(note_id: int, db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_active_user)):
    note_db = crud.note.get(db=db, id=note_id)
    if not note_db: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    if note_db.user_id != current_user.id: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    crud.note.remove(db=db, id=note_id); return {"message": "Note deleted successfully"}