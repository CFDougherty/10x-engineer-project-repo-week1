"""Async SQLAlchemy engine, session factory, and declarative base for PromptLab."""

import os
from functools import lru_cache

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://promptlab:promptlab@localhost:5432/promptlab"
    test_database_url: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()


class Base(DeclarativeBase):
    pass


# Module-level engine and session factory — initialized lazily on first use
_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _session_factory


def AsyncSessionLocal() -> AsyncSession:
    """Return a new async session from the factory."""
    return get_session_factory()()


async def init_db():
    """Create all tables. Called from the FastAPI lifespan handler."""
    from app.database import Base  # noqa — triggers model registration via models_db import
    import app.models_db  # noqa: F401
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
