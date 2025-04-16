# backend/schemas/spending_log.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import datetime
from datetime import date

class SpendingLogBase(BaseModel):
    description: str
    amount: float = Field(..., gt=0)
    category: Optional[str] = None
    date: Optional[datetime.date] = None
    currency: Optional[str] = Field('USD', max_length=3)

    @validator('currency', pre=True, always=True)
    def uppercase_currency(cls, v):
        return v.upper() if v else 'USD'

class SpendingLogCreate(SpendingLogBase):
    pass

class SpendingLogUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    category: Optional[str] = None
    date: Optional[datetime.date] = None
    currency: Optional[str] = Field(None, max_length=3)

    @validator('currency', pre=True, always=True)
    def uppercase_currency_update(cls, v):
         return v.upper() if v else None

class SpendingLog(SpendingLogBase):
    id: int
    user_id: int
    timestamp: datetime.datetime
    date: datetime.date
    currency: str

    class Config:
        from_attributes = True

class SpendingLogsOutput(BaseModel):
    spending_logs: List[SpendingLog]
    total_amount: Optional[float] = None
    currency: Optional[str] = None

# class SpendingLogCreate(BaseModel):
#     amount: float
#     currency: str = "USD"
#     description: str
#     category: str = "Other"
#     date: Optional[date]