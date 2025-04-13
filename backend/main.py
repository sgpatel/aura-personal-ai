# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings, logger
from backend.api.v1.api import api_router
from backend.db import session
from backend.services.llm import get_llm_service # Import factory
from backend.services.llm.ollama_service import OllamaLLMService # Import specific type for check

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root(): return {"message": f"Welcome to {settings.PROJECT_NAME}! API available at {settings.API_V1_STR}"}

@app.on_event("startup")
async def on_startup():
     logger.info("Application startup...")
     # Optional: Initialize LLM client eagerly if needed, or rely on factory's caching
     # try:
     #     get_llm_service() # Initialize default LLM service
     # except Exception as e:
     #     logger.error(f"Failed to initialize default LLM service on startup: {e}", exc_info=True)

     if session.engine:
         try: logger.info("Database tables check/creation skipped (use Alembic).")
         except Exception as e: logger.error(f"Error during startup DB check: {e}", exc_info=True)
     else: logger.error("Database engine not initialized.")

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Application shutdown...")
    # Gracefully close Ollama client if it was initialized
    try:
        # Access the cached instance if possible (this is a bit hacky, DI is better)
        llm_instance = get_llm_service() # Get potentially cached instance
        if isinstance(llm_instance, OllamaLLMService):
            await llm_instance.close_client()
    except Exception as e:
        # Log error if service wasn't initialized or closing failed
        logger.warning(f"Could not close Ollama client during shutdown: {e}", exc_info=True)


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