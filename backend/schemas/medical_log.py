# backend/schemas/medical_log.py
from pydantic import BaseModel
from typing import List, Optional
import datetime

class MedicalLogBase(BaseModel):
    log_type: str # e.g., 'symptom', 'medication', 'appointment', 'measurement'
    content: str
    date: Optional[datetime.date] = None # Optional on create, defaults to today
    # Optional: Add specific fields for certain types, e.g., value: Optional[float] for measurements

class MedicalLogCreate(MedicalLogBase):
    pass

class MedicalLog(MedicalLogBase):
    id: int
    user_id: int
    timestamp: datetime.datetime
    date: datetime.date # Make non-optional in response

    class Config:
        orm_mode = True

class MedicalLogsOutput(BaseModel):
    medical_logs: List[MedicalLog]


class MedicalLogUpdate(MedicalLogBase):
    log_type: Optional[str] = None
    content: Optional[str] = None
    date: Optional[datetime.date] = None