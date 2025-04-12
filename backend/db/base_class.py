# backend/db/base_class.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr

class Base:
    @declared_attr
    def __tablename__(cls):
        # Optional: Auto-generate table names from class names (e.g., UserDB -> users)
        # return cls.__name__.lower().replace('db', '') + 's'
        # Or keep explicit __tablename__ in models
        return cls.__name__.lower() # Requires explicit __tablename__ in models

Base = declarative_base(cls=Base)