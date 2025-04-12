# backend/api/v1/endpoints/investments.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.db.session import get_db
from backend.schemas.investment_note import InvestmentNote, InvestmentNoteCreate, InvestmentNoteUpdate, InvestmentNotesOutput
from backend.schemas.user import User
from backend.schemas.api_models import Message
from backend.api import deps
from backend import crud
from backend.core.config import logger

router = APIRouter()

@router.post("/", response_model=InvestmentNote, status_code=status.HTTP_201_CREATED)
async def create_new_investment_note(
    note_in: InvestmentNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """ Create a new investment note for the current user. """
    note_db = crud.investment_note.create_with_owner(db=db, obj_in=note_in, user_id=current_user.id)
    logger.info(f"Investment note {note_db.id} created for user {current_user.id}")
    return note_db

@router.get("/", response_model=InvestmentNotesOutput)
async def read_investment_notes(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
):
    """ Retrieve investment notes for the current user. """
    notes_db = crud.investment_note.get_multi_by_owner(db=db, user_id=current_user.id, skip=skip, limit=limit)
    return InvestmentNotesOutput(investment_notes=notes_db)

@router.get("/{note_id}", response_model=InvestmentNote)
async def read_investment_note_by_id(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """ Get a specific investment note by ID. """
    note_db = crud.investment_note.get(db=db, id=note_id)
    if not note_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investment note not found")
    if note_db.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return note_db

@router.put("/{note_id}", response_model=InvestmentNote)
async def update_investment_note_by_id(
    note_id: int,
    note_in: InvestmentNoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """ Update a specific investment note. """
    note_db = crud.investment_note.get(db=db, id=note_id)
    if not note_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investment note not found")
    if note_db.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    updated_note = crud.investment_note.update(db=db, db_obj=note_db, obj_in=note_in)
    return updated_note

@router.delete("/{note_id}", response_model=Message)
async def delete_investment_note_by_id(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """ Delete a specific investment note. """
    note_db = crud.investment_note.get(db=db, id=note_id)
    if not note_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investment note not found")
    if note_db.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    crud.investment_note.remove(db=db, id=note_id)
    return {"message": "Investment note deleted successfully"}