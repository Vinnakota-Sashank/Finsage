"""
FinSage Backend — Application Configuration
Loads environment variables and provides typed config access.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./finsage.db"

    # JWT Auth
    secret_key: str = "dev-secret-key-not-for-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Gemini AI
    gemini_api_key: str = ""

    # CORS
    frontend_url: str = "http://localhost:8080"

    # Demo mode controls (useful for hackathon/public demo deployments)
    allow_demo_fallback: bool = True
    auto_seed_demo_data: bool = True

    # Environment
    environment: str = "development"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
