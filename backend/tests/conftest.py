"""Test fixtures for PromptLab"""

import os
import pytest
import asyncpg
from fastapi.testclient import TestClient

# Point storage at the test database before any app imports touch the engine.
# Falls back to a local test DB if TEST_DATABASE_URL is not set.
os.environ.setdefault(
    "DATABASE_URL",
    os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://promptlab:promptlab@localhost:5432/promptlab_test"
    )
)

from app.api import app
from app.storage import storage
from app.database import Base, get_engine
import app.database as _db

# Swap the cached engine for a NullPool engine.
#
# The default pool (pool_size=5) caches asyncpg connections that are bound to
# the event loop that created them. pytest-asyncio creates a new loop per test
# and TestClient uses its own anyio loop, so any pooled connection from a
# previous loop causes "Future attached to a different loop". NullPool creates
# a fresh connection for every DB call, always on the current loop.
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine as _create_engine

_db._engine = _create_engine(
    os.environ["DATABASE_URL"],
    poolclass=NullPool,
)
_db._session_factory = None  # rebuilt automatically from the new engine


async def _ensure_test_db() -> None:
    """Create the test database and enable pgvector if they don't already exist.

    Connects to the admin 'postgres' database first (CREATE DATABASE cannot run
    inside a transaction against the target database), then switches to the test
    database to enable the vector extension. Both operations are idempotent.
    """
    from sqlalchemy.engine import make_url

    url = make_url(os.environ["DATABASE_URL"])
    host = url.host or "localhost"
    port = url.port or 5432
    user = url.username
    password = url.password
    db_name = url.database

    # Step 1: create the database if it doesn't exist
    admin_conn = await asyncpg.connect(
        host=host, port=port, user=user, password=password, database="postgres"
    )
    try:
        exists = await admin_conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        if not exists:
            # CREATE DATABASE cannot run inside a transaction block
            await admin_conn.execute(f'CREATE DATABASE "{db_name}"')
    finally:
        await admin_conn.close()

    # Step 2: enable pgvector in the test database
    test_conn = await asyncpg.connect(
        host=host, port=port, user=user, password=password, database=db_name
    )
    try:
        await test_conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    finally:
        await test_conn.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Ensure the test database exists, then create all tables."""
    await _ensure_test_db()
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture(autouse=True)
async def clear_storage():
    """Truncate all tables before and after each test."""
    await storage.clear()
    yield
    await storage.clear()


@pytest.fixture
def client():
    """Create a test client for the API."""
    return TestClient(app)


@pytest.fixture
def sample_prompt_data():
    """Sample prompt data for testing."""
    return {
        "title": "Code Review Prompt",
        "content": "Review the following code and provide feedback:\n\n{{code}}",
        "description": "A prompt for AI code review"
    }


@pytest.fixture
def sample_collection_data():
    """Sample collection data for testing."""
    return {
        "name": "Development",
        "description": "Prompts for development tasks"
    }
