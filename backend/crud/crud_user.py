# backend/crud/crud_user.py
from typing import Optional
from sqlalchemy.orm import Session

from backend.core.security import get_password_hash, verify_password
from backend.crud.base import CRUDBase # Import base class
from backend.db.models.user import UserDB
from backend.schemas.user import UserCreate, UserUpdate, UserBase # Add UserBase schema if needed

class CRUDUser(CRUDBase[UserDB, UserCreate, UserUpdate]): # Specify types
    def get_by_email(self, db: Session, *, email: str) -> Optional[UserDB]:
        return db.query(self.model).filter(UserDB.email == email).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> UserDB:
        # Override create to handle password hashing
        db_obj = UserDB(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # Add update method if needed, potentially handling password updates

    def authenticate(
        self, db: Session, *, email: str, password: str
    ) -> Optional[UserDB]:
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

# Create an instance for use in endpoints
user = CRUDUser(UserDB)

# Define UserUpdate schema in schemas/user.py if needed for updates
class UserUpdate(UserBase):
    password: Optional[str] = None