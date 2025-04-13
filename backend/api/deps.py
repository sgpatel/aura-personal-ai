# backend/api/deps.py
# Use User.model_validate instead of User.from_orm for Pydantic V2
from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt
from pydantic import EmailStr, ValidationError

from backend.core import security
from backend.core.config import settings, logger # Import logger
from backend.db.session import get_db
from backend.schemas.token import TokenData
from backend.schemas.user import User
from backend.crud import crud_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> Optional[User]: # Return Pydantic User model
    """ Validates token and retrieves user from DB. """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = security.decode_access_token(token)
    if payload is None:
         logger.warning("Token decoding failed or token expired.")
         raise credentials_exception

    email: Optional[EmailStr] = payload.get("sub")
    if email is None:
        logger.warning("Token payload missing 'sub' (email).")
        raise credentials_exception

    # Validate email format using TokenData (optional but good practice)
    try:
        token_data = TokenData(email=email)
    except ValidationError:
         logger.warning(f"Invalid email format in token: {email}")
         raise credentials_exception

    user_db = crud_user.user.get_by_email(db, email=token_data.email)

    if user_db is None:
        logger.warning(f"User not found for email in token: {token_data.email}")
        raise credentials_exception

    # Use model_validate for Pydantic V2 instead of from_orm
    try:
        user_pydantic = User.model_validate(user_db)
    except Exception as e:
         logger.error(f"Pydantic validation error for user {user_db.id}: {e}", exc_info=True)
         raise HTTPException(status_code=500, detail="Internal server error validating user data.")

    return user_pydantic


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """ Dependency to get the current active user. """
    # if not current_user.is_active: # Check is_active flag from the Pydantic model
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user