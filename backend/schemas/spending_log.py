# backend/schemas/spending_log.py
from pydantic import BaseModel, Field
from typing import List, Optional
import datetime

class SpendingLogBase(BaseModel):
    description: str
    amount: float = Field(..., gt=0)
    category: Optional[str] = None
    date: Optional[datetime.date] = None

class SpendingLogCreate(SpendingLogBase):
    pass

class SpendingLogUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    category: Optional[str] = None
    date: Optional[datetime.date] = None

class SpendingLog(SpendingLogBase):
    id: int
    user_id: int
    timestamp: datetime.datetime
    date: datetime.date

    class Config:
        from_attributes = True # Pydantic V2 update

class SpendingLogsOutput(BaseModel):
    spending_logs: List[SpendingLog]
    total_amount: Optional[float] = None
