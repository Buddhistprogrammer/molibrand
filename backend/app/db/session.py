"""数据库连接：MySQL（业务）+ PostgreSQL（向量），均为异步引擎。"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

# ---- MySQL：业务数据 ----
mysql_engine = create_async_engine(
    settings.mysql_dsn,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=5,
    echo=False,
)
MySQLSession = async_sessionmaker(mysql_engine, expire_on_commit=False, class_=AsyncSession)

# ---- PostgreSQL：向量数据 ----
pg_engine = create_async_engine(
    settings.pg_dsn,
    pool_pre_ping=True,
    pool_size=5,
    echo=False,
)
PGSession = async_sessionmaker(pg_engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：业务数据库会话。"""
    async with MySQLSession() as session:
        yield session


async def get_pg() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：向量数据库会话。"""
    async with PGSession() as session:
        yield session
