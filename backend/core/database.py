import os
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres_password@postgres:5432/moderator_db"
)

# Convert standard postgres:// or postgresql:// to postgresql+asyncpg:// if needed
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Auto-migrate new columns for existing tables
        migrations = [
            "ALTER TABLE chat_settings ADD COLUMN IF NOT EXISTS warn_expire_hours INTEGER DEFAULT 24;",
            "ALTER TABLE chat_settings ADD COLUMN IF NOT EXISTS captcha_enabled_types TEXT DEFAULT 'button,math,math_advanced,emoji,question,category,compare,shapes,sequence';",
            "ALTER TABLE chat_settings ADD COLUMN IF NOT EXISTS custom_captcha_question TEXT;",
            "ALTER TABLE chat_settings ADD COLUMN IF NOT EXISTS custom_captcha_answer VARCHAR(255);"
        ]
        for query in migrations:
            try:
                await conn.execute(text(query))
            except Exception as e:
                print(f"Migration note: {e}")
