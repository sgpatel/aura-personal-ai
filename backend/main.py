# backend/main.py
# (No changes needed from previous version - structure handles imports)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings, logger
from backend.api.v1.api import api_router
from backend.db import session # Import session to access Base and engine


# --- FastAPI App Initialization ---
app = FastAPI(title=settings.PROJECT_NAME)

# --- CORS Middleware ---
# Allows requests from specified origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS], # Handles AnyHttpUrl and "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include API Router ---
app.include_router(api_router, prefix=settings.API_V1_STR)

# --- Root Endpoint ---
@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}! API available at {settings.API_V1_STR}"}


# --- Startup/Shutdown Events ---
@app.on_event("startup")
async def on_startup():
     logger.info("Application startup...")
     # Create tables if they don't exist (Use Alembic for production)
     if session.engine: # Check if engine was initialized
         try:
             session.Base.metadata.create_all(bind=session.engine)
             logger.info("Database tables checked/created successfully.")
         except Exception as e:
             logger.error(f"Error creating database tables during startup: {e}", exc_info=True)
     else:
         logger.error("Database engine not initialized. Skipping table creation.")
     # Optional: Connect async database if using 'databases' library
     # if session.database: await session.database.connect()

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Application shutdown...")
    # Optional: Disconnect async database
    # if session.database: await session.database.disconnect()

# --- How to Run (Reminder) ---
# 1. Create a .env file based on .env.example
# 2. Install requirements: pip install -r requirements.txt
# 3. Set up PostgreSQL database and user matching .env
# 4. Optional: Initialize Alembic and run migrations (recommended)
#    alembic init alembic
#    # Configure alembic.ini and env.py...
#    alembic revision --autogenerate -m "Initial models"
#    alembic upgrade head
# 5. Run: uvicorn backend.main:app --reload --port 8000
#    (Run from the parent directory 'aura-project')