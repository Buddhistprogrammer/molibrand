"""认证：注册 / 登录。"""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core import DBSession, create_token, hash_password, verify_password
from app.models import User
from app.schemas import LoginIn, RegisterIn, TokenOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut)
async def register(body: RegisterIn, db: DBSession):
    exists = await db.scalar(select(User).where(User.phone == body.phone))
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "手机号已注册")
    user = User(
        phone=body.phone,
        nickname=body.nickname or body.phone,
        password_hash=hash_password(body.password),
        role="user",
        plan="single",
        quota_left=1,  # 注册赠送 1 次体验（PRD 免费试用）
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return TokenOut(
        access_token=create_token(user.id, user.role),
        role=user.role,
        nickname=user.nickname,
    )


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn, db: DBSession):
    user = await db.scalar(select(User).where(User.phone == body.phone))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "手机号或密码错误")
    return TokenOut(
        access_token=create_token(user.id, user.role),
        role=user.role,
        nickname=user.nickname,
    )
