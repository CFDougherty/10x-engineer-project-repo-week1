"""Test fixtures for PromptLab"""

import os
import pytest
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


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Create all tables once per test session."""
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
