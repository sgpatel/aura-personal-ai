# backend/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Updated schema imports
from backend.schemas.user import User, ProfileUpdate
from backend.api import deps
from backend import crud # Import crud package
from backend.db.session import get_db # Import get_db
from backend.db.models.user import UserDB # Import DB model for type hint

router = APIRouter()

@router.get("/me", response_model=User)
async def read_users_me(
    # Use the dependency that returns the Pydantic User model
    current_user: User = Depends(deps.get_current_active_user)
):
    """ Get current user details. """
    return current_user

# --- New Endpoint for Profile Update ---
@router.put("/me", response_model=User)
async def update_user_me(
    *,
    db: Session = Depends(get_db),
    profile_in: ProfileUpdate, # Use the new schema for input validation
    current_user_db: UserDB = Depends(deps.get_current_user_db_object) # Dependency to get DB object
):
    """
    Update own user profile (currently only full_name).
    """
    # The crud.user.update method expects the DB object and the update schema
    updated_user = crud.user.update(db=db, db_obj=current_user_db, obj_in=profile_in)
    # Return the updated user info using the User schema (which excludes password)
    return updated_user
# --- End New Endpoint ---
