"""安全与鉴权：密码哈希、JWT、当前用户依赖。"""
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.models import User

bearer = HTTPBearer(auto_error=False)

# bcrypt 上限 72 字节，超长截断（直接用 bcrypt 库，passlib 已停止维护且与新版 bcrypt 不兼容）
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_token(user_id: int, role: str) -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "缺少认证信息")
    try:
        payload = jwt.decode(creds.credentials, settings.jwt_secret, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "无效或过期的令牌")

    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户不存在")
    return user


async def require_reviewer(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """审核工作台/知识库管理需要 reviewer 或 admin 角色。"""
    if user.role not in ("reviewer", "admin"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "需要审核员权限")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
ReviewerUser = Annotated[User, Depends(require_reviewer)]
DBSession = Annotated[AsyncSession, Depends(get_db)]
