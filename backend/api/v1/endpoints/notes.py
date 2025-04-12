# backend/api/v1/endpoints/notes.py
from fastapi import APIRouter, Depends, HTTPException, status, Query # Import Query
from sqlalchemy.orm import Session
import datetime
from typing import List, Optional # Import Optional

from backend.db.session import get_db
# Updated schema imports
from backend.schemas.note import Note, NoteCreate, NotesOutput, NoteUpdate, NoteSummaryOutput
from backend.schemas.user import User
from backend.schemas.api_models import Message
from backend.api import deps
from backend import crud
from backend.core.config import logger
from backend.services import summary_service # Import summary service

router = APIRouter()

@router.post("/", response_model=Note, status_code=status.HTTP_201_CREATED)
async def create_new_note(
    note_in: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    note_db = crud.note.create_with_owner(db=db, obj_in=note_in, user_id=current_user.id)
    logger.info(f"Note {note_db.id} created via API for user {current_user.id}")
    return note_db

@router.get("/global", response_model=NotesOutput)
async def read_global_notes(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
):
    notes_db = crud.note.get_global(db=db, user_id=current_user.id) # Add skip/limit later
    return NotesOutput(notes=notes_db)


@router.get("/by_date/{date_str}", response_model=NotesOutput) # Changed path for clarity
async def read_notes_for_date( # Renamed function
    date_str: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """ Retrieve notes associated with a specific date. """
    try:
        target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    notes_db = crud.note.get_by_date(db=db, user_id=current_user.id, date=target_date)
    return NotesOutput(notes=notes_db)

# --- New Endpoint for Note Summary ---
@router.get("/summary", response_model=NoteSummaryOutput)
async def summarize_notes_by_criteria(
    tags: Optional[List[str]] = Query(None, description="List of tags to filter notes (AND logic)"),
    keywords: Optional[List[str]] = Query(None, description="List of keywords to search in note content (OR logic)"),
    limit: int = Query(50, description="Max notes to consider for summary", le=200), # Limit notes processed
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Summarize notes based on tags and/or keywords.
    Requires either 'tags' or 'keywords' query parameter.
    """
    if not tags and not keywords:
        raise HTTPException(status_code=400, detail="Please provide 'tags' or 'keywords' query parameter.")

    # Fetch notes using the new CRUD function
    notes_to_summarize = crud.note.get_notes_by_tags_keywords(
        db=db, user_id=current_user.id, tags=tags, keywords=keywords, limit=limit
    )

    if not notes_to_summarize:
        raise HTTPException(status_code=404, detail="No notes found matching the criteria.")

    # Extract content for summarization service
    notes_content = [note.content for note in notes_to_summarize]

    # Call the summarization service
    try:
        summary = summary_service.generate_note_summary(
            notes_content=notes_content,
            criteria_tags=tags,
            criteria_keywords=keywords
        )
    except Exception as e:
        logger.error(f"Note Summary Service error for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error generating summary.")

    return NoteSummaryOutput(
        summary=summary,
        criteria_tags=tags,
        criteria_keywords=keywords,
        note_count=len(notes_to_summarize)
    )
# --- End New Endpoint ---


@router.get("/{note_id}", response_model=Note)
async def read_note_by_id(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """ Get a specific note by ID. """
    note_db = crud.note.get(db=db, id=note_id)
    if not note_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    if note_db.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return note_db

@router.put("/{note_id}", response_model=Note)
async def update_note_by_id(
    note_id: int,
    note_in: NoteUpdate, # Use update schema
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """ Update a specific note. """
    note_db = crud.note.get(db=db, id=note_id)
    if not note_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    if note_db.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    updated_note = crud.note.update(db=db, db_obj=note_db, obj_in=note_in)
    return updated_note

@router.delete("/{note_id}", response_model=Message)
async def delete_note_by_id(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """ Delete a specific note. """
    note_db = crud.note.get(db=db, id=note_id)
    if not note_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    if note_db.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    crud.note.remove(db=db, id=note_id)
    return {"message": "Note deleted successfully"}