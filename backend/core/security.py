import os
import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.core.database import get_db

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super_secret_jwt_key_moderator_bot_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

SUPER_ADMIN_USERNAME = os.getenv("SUPER_ADMIN_USERNAME", "admin")
SUPER_ADMIN_PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD", "change_this_password_in_env")

security = HTTPBearer()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role", "admin")
        if username is None:
            raise HTTPException(status_code=401, detail="Недействительный токен")

        # Super Admin Check
        if username == SUPER_ADMIN_USERNAME and role == "admin":
            return {"username": SUPER_ADMIN_USERNAME, "role": "admin"}

        # Staff User Check from DB
        from backend.models.models import StaffUser
        res = await db.execute(select(StaffUser).where(StaffUser.username == username, StaffUser.is_active == True))
        staff = res.scalar_one_or_none()
        if staff:
            return {"username": staff.username, "role": staff.role}

        raise HTTPException(status_code=401, detail="Пользователь не найден")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Ошибка валидации токена авторизации")

async def get_current_user(user_info: dict = Depends(get_current_user_info)) -> str:
    return user_info["username"]

async def require_admin(user_info: dict = Depends(get_current_user_info)) -> str:
    if user_info.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен. Требуются права администратора.")
    return user_info["username"]
