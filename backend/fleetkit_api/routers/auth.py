from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fleetkit_api.db import get_db
from fleetkit_api.deps import get_current_user
from fleetkit_api.models import User
from fleetkit_api.schemas import LoginIn, TokenOut, UserOut
from fleetkit_api.security import create_access_token, verify_password
from fleetkit_api.security_suite.auth_hardening import login_protector

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn, request: Request, db: AsyncSession = Depends(get_db)) -> TokenOut:
    key = f"{body.email.lower()}|{request.client.host if request.client else 'unknown'}"
    if login_protector.is_locked(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много неудачных попыток. Подожди и попробуй снова.",
        )
    result = await db.execute(select(User).where(User.email == body.email.lower()))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        login_protector.register_failure(key)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный email или пароль")
    login_protector.register_success(key)
    token = create_access_token(user.id, extra={"email": user.email})
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> User:
    return user
