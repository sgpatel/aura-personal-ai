# backend/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str

# Properties to return via API
class User(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True # Enable mapping from DB models

# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None