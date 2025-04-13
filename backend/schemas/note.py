# backend/schemas/note.py
from pydantic import BaseModel
from typing import List, Optional
import datetime

class NoteBase(BaseModel):
    content: str
    tags: Optional[List[str]] = None
    is_global: bool = False
    date_associated: Optional[datetime.date] = None

class NoteCreate(NoteBase):
    pass

class NoteUpdate(NoteBase):
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    is_global: Optional[bool] = None
    date_associated: Optional[datetime.date] = None

class Note(NoteBase):
    id: int
    user_id: int
    timestamp: datetime.datetime

    class Config:
        from_attributes = True # Pydantic V2 update

class NotesOutput(BaseModel):
    notes: List[Note]

class NoteSummaryOutput(BaseModel):
    summary: str
    criteria_tags: Optional[List[str]] = None
    criteria_keywords: Optional[List[str]] = None
    note_count: int
