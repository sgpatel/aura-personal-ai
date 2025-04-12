# backend/core/config.py
import os
from dotenv import load_dotenv
from pydantic import PostgresDsn, AnyHttpUrl, validator
from typing import List, Optional, Union

from pydantic_settings import BaseSettings

# Load .env file from the project root
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Aura Backend"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL = "postgresql://postgres:password@localhost:5432/auradb"
    print("Loading environment variables...", DATABASE_URL)
    # Database
    DATABASE_URL: Optional[PostgresDsn] = DATABASE_URL #os.getenv("DATABASE_URL") # Make optional initially

    @validator("DATABASE_URL", pre=True)
    def check_db_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL environment variable is not set!")
        return v

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "DEFAULT_SECRET_CHANGE_ME_IN_ENV")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # Default: 30 minutes

    # CORS - Allow AnyHttpUrl or "*"
    BACKEND_CORS_ORIGINS: List[Union[AnyHttpUrl, str]] = ["*"] # Default to allow all for easier dev setup

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            # Allow comma-separated string like "http://localhost,http://127.0.0.1"
             return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        # Allow "*" or specific list from env var
        if v == "*":
            return ["*"]
        raise ValueError(v)


    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    class Config:
        case_sensitive = True


settings = Settings()

# Logging Configuration
import logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("aura_backend") # Give logger a specific name

logger.info(f"Log level set to: {settings.LOG_LEVEL}")
if settings.DATABASE_URL:
    logger.info(f"Database URL Host (example): {settings.DATABASE_URL}")
else:
    logger.error("DATABASE_URL is not configured!")

if settings.SECRET_KEY == "DEFAULT_SECRET_CHANGE_ME_IN_ENV":
    logger.warning("Security Warning: Using default SECRET_KEY. Please set a strong secret in your .env file!")
