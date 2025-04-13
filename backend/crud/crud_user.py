# backend/crud/crud_user.py
from typing import Optional
from sqlalchemy.orm import Session

from backend.core.security import get_password_hash, verify_password
from backend.crud.base import CRUDBase
from backend.db.models.user import UserDB
# Import UserUpdate schema correctly
from backend.schemas.user import UserCreate, UserUpdate

# Use UserUpdate schema for the update method type hint
class CRUDUser(CRUDBase[UserDB, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[UserDB]:
        return db.query(self.model).filter(UserDB.email == email).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> UserDB:
        db_obj = UserDB(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # The update method inherited from CRUDBase should work for non-password fields.
    # If password updates were allowed via UserUpdate, we would override update here
    # to handle hashing like in the create method.

    def authenticate(
        self, db: Session, *, email: str, password: str
    ) -> Optional[UserDB]:
        user = self.get_by_email(db, email=email)
        if not user: return None
        if not verify_password(password, user.hashed_password): return None
        return user

user = CRUDUser(UserDB)