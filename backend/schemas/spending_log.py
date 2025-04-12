# backend/schemas/spending_log.py
from pydantic import BaseModel, Field
from typing import List, Optional
import datetime

class SpendingLogBase(BaseModel):
    description: str
    amount: float = Field(..., gt=0) # Ensure amount is positive
    category: Optional[str] = None
    date: Optional[datetime.date] = None # Optional on create, defaults to today

class SpendingLogCreate(SpendingLogBase):
    pass

class SpendingLog(SpendingLogBase):
    id: int
    user_id: int
    timestamp: datetime.datetime
    date: datetime.date # Make non-optional in response

    class Config:
        orm_mode = True

class SpendingLogsOutput(BaseModel):
    spending_logs: List[SpendingLog]
    total_amount: Optional[float] = None # Optional field for aggregations

class SpendingLogUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)  # Ensure amount is positive if provided
    category: Optional[str] = None
    date: Optional[datetime.date] = None

