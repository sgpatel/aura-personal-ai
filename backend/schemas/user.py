# backend/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str

# Properties to receive via API on update (excluding password for now)
# Password updates should ideally have a separate flow with current password verification
class UserUpdate(BaseModel): # Renamed from previous placeholder UserUpdate
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    # password: Optional[str] = None # Exclude password from general update

# --- New Schema for Profile Update ---
# Define specific fields allowed for user self-update via profile endpoint
class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100) # Example validation
    # Add other updatable profile fields here later (e.g., preferences, timezone)

# Properties to return via API (current user)
class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True # Pydantic V2