"""Database session factory and initialization."""

from __future__ import annotations

from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from maana_api.config import get_settings

settings = get_settings()
DATABASE_URL = settings.database_url


def get_sync_engine():
    return create_engine(DATABASE_URL, echo=(settings.environment == "development"))


def get_async_engine():
    return create_async_engine(
        DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=(settings.environment == "development"),
    )


async_session_factory = async_sessionmaker(
    get_async_engine(),
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session


def init_db() -> None:
    engine = get_sync_engine()
    SQLModel.metadata.create_all(engine)
