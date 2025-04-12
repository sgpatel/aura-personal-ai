# backend/schemas/api_models.py
from pydantic import BaseModel
from typing import Optional, Dict, Any
import datetime

class ProcessInput(BaseModel):
    text: str
    # audio_data: Optional[bytes] = None # If handling audio upload

class ProcessOutput(BaseModel):
    reply: str

class SummaryOutput(BaseModel):
    summary: str
    date: datetime.date

# Optional: Generic message model for simple responses
class Message(BaseModel):
    message: str