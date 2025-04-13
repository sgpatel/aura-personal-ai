# backend/schemas/medical_log.py
from pydantic import BaseModel
from typing import List, Optional
import datetime

class MedicalLogBase(BaseModel):
    log_type: str
    content: str
    date: Optional[datetime.date] = None

class MedicalLogCreate(MedicalLogBase):
    pass

class MedicalLogUpdate(BaseModel):
    log_type: Optional[str] = None
    content: Optional[str] = None
    date: Optional[datetime.date] = None

class MedicalLog(MedicalLogBase):
    id: int
    user_id: int
    timestamp: datetime.datetime
    date: datetime.date

    class Config:
        from_attributes = True # Pydantic V2 update

class MedicalLogsOutput(BaseModel):
    medical_logs: List[MedicalLog]
