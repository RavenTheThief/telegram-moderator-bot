from fastapi import APIRouter, Depends, HTTPException, status
from backend.core.security import verify_admin_credentials, create_access_token, get_current_user, ADMIN_LOGIN
from backend.schemas.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    if not verify_admin_credentials(credentials.username, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": credentials.username})
    return TokenResponse(access_token=access_token, token_type="bearer", username=credentials.username)

@router.get("/me")
async def get_me(username: str = Depends(get_current_user)):
    return {"username": username, "role": "admin"}
