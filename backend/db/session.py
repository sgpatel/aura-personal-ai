# backend/db/session.py
# (No significant changes needed, ensure DATABASE_URL check in config)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.db.base_class import Base
from backend.core.config import settings, logger

if not settings.DATABASE_URL:
    logger.error("DATABASE_URL not set, database connection cannot be established.")
    # Depending on desired behavior, could exit or raise critical error
    # For now, engine creation might fail later if URL is None
    engine = None
    SessionLocal = None
else:
    engine = create_engine(str(settings.DATABASE_URL), pool_pre_ping=True) # Ensure URL is string
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get DB session
from typing import Generator

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a SQLAlchemy database session.
    Ensures the session is closed after the request.
    """
    if SessionLocal is None:
        raise RuntimeError("Database session not configured. Check DATABASE_URL.")
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database Session error: {e}", exc_info=True) # Log traceback
        db.rollback() # Rollback on error within the request handling
        raise
    finally:
        db.close()
        logger.info("Database session closed.")