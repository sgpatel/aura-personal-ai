# backend/api/v1/endpoints/users.py
# (No changes needed from previous version)
from fastapi import APIRouter, Depends, HTTPException

from backend.schemas.user import User
from backend.api import deps

router = APIRouter()

@router.get("/me", response_model=User)
async def read_users_me(
    current_user: User = Depends(deps.get_current_active_user)
):
    """ Get current user details. """
    return current_user
