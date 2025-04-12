# backend/schemas/reminder.py
from pydantic import BaseModel, Field
from typing import List, Optional
import datetime

class ReminderBase(BaseModel):
    content: str
    remind_at: datetime.datetime # Must include timezone info on input
    is_active: bool = True
    # recurrence_rule: Optional[str] = None # Optional recurrence

class ReminderCreate(ReminderBase):
    pass

class ReminderUpdate(ReminderBase):
    # Allow partial updates
    content: Optional[str] = None
    remind_at: Optional[datetime.datetime] = None
    is_active: Optional[bool] = None
    # recurrence_rule: Optional[str] = None

class Reminder(ReminderBase):
    id: int
    user_id: int
    created_at: datetime.datetime
    # triggered_at: Optional[datetime.datetime] = None # Optional field

    class Config:
        orm_mode = True

class RemindersOutput(BaseModel):
    reminders: List[Reminder]