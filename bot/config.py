import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres_password@postgres:5432/moderator_db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    WEB_PANEL_URL: str = os.getenv("WEB_PANEL_URL", "https://localhost:8081")
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Normalize Postgres connection string
if settings.DATABASE_URL.startswith("postgresql://"):
    settings.DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif settings.DATABASE_URL.startswith("postgres://"):
    settings.DATABASE_URL = settings.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
