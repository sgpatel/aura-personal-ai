# backend/api/deps.py
# Use User.model_validate instead of User.from_orm for Pydantic V2
# Added dependency to get the raw DB object for updates
from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt
from pydantic import EmailStr, ValidationError

from backend.core import security
from backend.core.config import settings, logger
from backend.db.session import get_db
from backend.db.models.user import UserDB # Import DB model
from backend.schemas.token import TokenData
from backend.schemas.user import User # Import Pydantic model
from backend import crud # Import crud package

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

# --- Dependency to get the UserDB object ---
# Needed for operations that require the SQLAlchemy model instance (like update)
def get_current_user_db_object(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> Optional[UserDB]:
    """ Validates token and retrieves user DB object from DB. """
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

    try: token_data = TokenData(email=email)
    except ValidationError:
         logger.warning(f"Invalid email format in token: {email}")
         raise credentials_exception

    # Use the CRUD function to get the DB object
    user_db = crud.user.get_by_email(db, email=token_data.email)

    if user_db is None:
        logger.warning(f"User not found for email in token: {token_data.email}")
        raise credentials_exception
    return user_db
# --- End Dependency ---


# --- Dependency to get the Pydantic User model ---
# Used for endpoints returning user info or checking basic auth
def get_current_user(
    user_db: UserDB = Depends(get_current_user_db_object) # Depend on the DB object getter
) -> Optional[User]:
    """ Validates token and retrieves Pydantic User model. """
    if user_db is None: return None # Should be caught by get_current_user_db_object already
    try:
        # Use model_validate for Pydantic V2 instead of from_orm
        user_pydantic = User.model_validate(user_db)
    except Exception as e:
         logger.error(f"Pydantic validation error for user {user_db.id}: {e}", exc_info=True)
         # Raise 500 because this indicates a programming error (schema mismatch)
         raise HTTPException(status_code=500, detail="Internal server error validating user data.")
    return user_pydantic


def get_current_active_user(
    current_user: User = Depends(get_current_user),
     current_user_db: UserDB = Depends(get_current_user_db_object) # Also get DB object if needed
) -> User: # Return Pydantic model for consistency in endpoint signature
    """ Dependency to get the current active user (Pydantic model). """
    if not current_user_db.is_active: # Check the is_active flag on the DB model
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user # Return the validated Pydantic model

# Optional: Dependency to get the active user's DB object directly
# def get_current_active_user_db_object(
#     current_user_db: UserDB = Depends(get_current_user_db_object),
# ) -> UserDB:
#     if not current_user_db.is_active:
#         raise HTTPException(status_code=400, detail="Inactive user")
#     return current_user_db