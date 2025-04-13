# backend/core/config.py
import os
from dotenv import load_dotenv
from urllib.parse import urlparse
# Import BaseSettings from pydantic_settings now
from pydantic_settings import BaseSettings
# Keep other pydantic imports
from pydantic import PostgresDsn, AnyHttpUrl, validator, HttpUrl, Field
from typing import List, Optional, Union, Literal

# Load .env file from the project root
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Aura Backend"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: Optional[PostgresDsn] = Field(default=None, env="DATABASE_URL") # Use Field for env var mapping
    @validator("DATABASE_URL", pre=True)
    def check_db_url(cls, v):
        if not v: raise ValueError("DATABASE_URL environment variable is not set!")
        return v

    # Security
    SECRET_KEY: str = Field(default="DEFAULT_SECRET_CHANGE_ME_IN_ENV", env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    BACKEND_CORS_ORIGINS: List[Union[AnyHttpUrl, str]] = Field(default=["*"], env="BACKEND_CORS_ORIGINS")
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["): return [i.strip() for i in v.split(",")]
        elif isinstance(v, list): return v
        if v == "*": return ["*"]
        raise ValueError(v)

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")

    # --- LLM Configuration ---
    DEFAULT_LLM_PROVIDER: Literal["openai", "gemini", "ollama"] = Field(default="openai", env="DEFAULT_LLM_PROVIDER")

    # OpenAI Settings
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_MODEL_NAME: str = Field(default="gpt-4o", env="OPENAI_MODEL_NAME") # Added specific model config

    # Google Gemini Settings
    GOOGLE_API_KEY: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    # GOOGLE_MODEL_NAME: str = Field(default="gemini-1.5-flash", env="GOOGLE_MODEL_NAME") # Optional

    # Ollama Settings
    OLLAMA_BASE_URL: Optional[HttpUrl] = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    OLLAMA_DEFAULT_MODEL: str = Field(default="llama3", env="OLLAMA_DEFAULT_MODEL")


    # --- Add Validations for LLM Keys based on Provider ---
    # Pydantic V2 validators are slightly different
    # --- Validations ---
    @validator("OPENAI_API_KEY", always=True, pre=False)
    def check_openai_key(cls, v, values):
        if values.get("DEFAULT_LLM_PROVIDER") == "openai" and not v:
            raise ValueError("OPENAI_API_KEY must be set if DEFAULT_LLM_PROVIDER is 'openai'")
        return v

    @validator("GOOGLE_API_KEY", always=True, pre=False)
    def check_google_key(cls, v, values):
        if values.get("DEFAULT_LLM_PROVIDER") == "gemini" and not v:
            raise ValueError("GOOGLE_API_KEY must be set if DEFAULT_LLM_PROVIDER is 'gemini'")
        return v

    class Config:
        case_sensitive = True

settings = Settings()

# Logging Configuration
import logging
# Use LOG_LEVEL from settings after validation
log_level_processed = settings.LOG_LEVEL.upper()
logging.basicConfig(level=log_level_processed)
logger = logging.getLogger("aura_backend")

logger.info(f"Log level set to: {log_level_processed}")
if settings.DATABASE_URL: logger.info(f"Database URL Host (example): {settings.DATABASE_URL}")
if settings.DATABASE_URL:
    logger.info(f"Database URL: {settings.DATABASE_URL}")
    
    # Parse the DATABASE_URL to extract specific components
    parsed_url = urlparse(str(settings.DATABASE_URL))  # Convert PostgresDsn to string and parse
    
    # Extract host, username, password, etc.
    db_host = parsed_url.hostname
    db_port = parsed_url.port
    db_user = parsed_url.username
    db_password = parsed_url.password
    db_name = parsed_url.path.lstrip("/")  # Remove leading slash
    logger.info(f"Database Host: {db_host}")
    logger.info(f"Database Port: {db_port}")
    logger.info(f"Database User: {db_user}")
else: logger.warning("DATABASE_URL is not set, database connection will not be established.")
if settings.SECRET_KEY == "DEFAULT_SECRET_CHANGE_ME_IN_ENV": logger.warning("Security Warning: Using default SECRET_KEY.")
logger.info(f"Default LLM Provider set to: {settings.DEFAULT_LLM_PROVIDER}")
if settings.DEFAULT_LLM_PROVIDER == "openai":
    logger.info(f"Using OpenAI Model: {settings.OPENAI_MODEL_NAME}") # Log the model being used
if settings.DEFAULT_LLM_PROVIDER == "ollama":
    logger.info(f"Ollama Base URL: {settings.OLLAMA_BASE_URL}")
    logger.info(f"Ollama Default Model: {settings.OLLAMA_DEFAULT_MODEL}")