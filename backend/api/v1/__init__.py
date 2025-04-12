from fastapi import APIRouter

router = APIRouter()

from .endpoints import auth, users, process, notes, summary

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(process.router, prefix="/process", tags=["process"])
router.include_router(notes.router, prefix="/notes", tags=["notes"])
router.include_router(summary.router, prefix="/summary", tags=["summary"])