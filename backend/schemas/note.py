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

# Schema for updating notes (allows partial updates)
class NoteUpdate(NoteBase):
    content: Optional[str] = None # Make fields optional for partial update
    tags: Optional[List[str]] = None
    is_global: Optional[bool] = None
    date_associated: Optional[datetime.date] = None

class Note(NoteBase):
    id: int
    user_id: int
    timestamp: datetime.datetime
    class Config:
        orm_mode = True

class NotesOutput(BaseModel):
    notes: List[Note]

# New Schema for Note Summary Output
class NoteSummaryOutput(BaseModel):
    summary: str
    criteria_tags: Optional[List[str]] = None
    criteria_keywords: Optional[List[str]] = None
    note_count: int

class NoteSummary(BaseModel):
    """
    Represents a summary of a note, typically including only key fields.
    """
    id: int
    content: str
    tags: Optional[List[str]] = None
    is_global: bool = False
    date_associated: Optional[datetime.date] = None