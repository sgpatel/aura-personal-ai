# backend/schemas/reminder.py
from pydantic import BaseModel, Field
from typing import List, Optional
import datetime

class ReminderBase(BaseModel):
    content: str
    remind_at: datetime.datetime
    is_active: bool = True

class ReminderCreate(ReminderBase):
    pass

class ReminderUpdate(BaseModel):
    content: Optional[str] = None
    remind_at: Optional[datetime.datetime] = None
    is_active: Optional[bool] = None

class Reminder(ReminderBase):
    id: int
    user_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True # Pydantic V2 update

class RemindersOutput(BaseModel):
    reminders: List[Reminder]