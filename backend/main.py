import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.database import init_db
from backend.core.tasks import start_periodic_log_cleanup_worker
from backend.api import auth, chats, settings, logs, users

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    await init_db()
    
    # Launch automated daily log cleanup background worker
    cleanup_task = asyncio.create_task(start_periodic_log_cleanup_worker(retention_days=90))
    
    yield
    
    cleanup_task.cancel()

app = FastAPI(
    title="Telegram Moderator Bot API",
    version="1.0.0",
    description="Backend API for managing Telegram Moderation Bot and Web Panel Settings",
    lifespan=lifespan
)

# CORS setup for Web Panel
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    os.getenv("FRONTEND_URL", "http://localhost:3000"),
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(chats.router)
app.include_router(settings.router)
app.include_router(logs.router)
app.include_router(users.router)

@app.get("/")
async def root():
    return {"status": "online", "service": "Telegram Moderator Bot API"}
