# backend/schemas/investment_note.py
from pydantic import BaseModel
from typing import List, Optional
import datetime

class InvestmentNoteBase(BaseModel):
    title: Optional[str] = None
    content: str
    tags: Optional[List[str]] = None

class InvestmentNoteCreate(InvestmentNoteBase):
    pass

class InvestmentNoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None

class InvestmentNote(InvestmentNoteBase):
    id: int
    user_id: int
    timestamp: datetime.datetime

    class Config:
        from_attributes = True # Pydantic V2 update

class InvestmentNotesOutput(BaseModel):
    investment_notes: List[InvestmentNote]
