# backend/api/deps.py
# (No significant changes needed, ensure TokenData schema imports EmailStr)
from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt
from pydantic import EmailStr # Import EmailStr

from backend.core import security
from backend.core.config import settings
from backend.db.session import get_db
from backend.schemas.token import TokenData
from backend.schemas.user import User
from backend.crud import crud_user # Use instance

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> Optional[User]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = security.decode_access_token(token)
    if payload is None:
         raise credentials_exception
    email: Optional[EmailStr] = payload.get("sub") # Use EmailStr for validation
    if email is None:
        raise credentials_exception
    token_data = TokenData(email=email)

    user_db = crud_user.user.get_by_email(db, email=token_data.email) # Use instance

    if user_db is None:
        raise credentials_exception
    return User.from_orm(user_db)

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    # if not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user