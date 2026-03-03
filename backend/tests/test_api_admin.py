"""Tests for admin API endpoints."""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.api import app
from app.storage import storage
from app.models import Prompt, Collection
import uuid

client = TestClient(app)

async def test_populate_test_data():
    """Populate-test-data endpoint must create prompts and collections and report counts.

    Verifies the endpoint returns a success status, reports non-zero creation counts,
    and that the storage state matches the reported counts after the call.
    """
    await storage.clear()

    assert len(await storage.get_all_prompts()) == 0
    assert len(await storage.get_all_collections()) == 0

    response = client.post("/admin/populate-test-data")

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "started"
    assert data["total"] > 0

    # BackgroundTasks run synchronously in TestClient, so data is present now.
    # Poll /admin/populate-status for creation counts (not the 202 response).
    status_response = client.get("/admin/populate-status")
    assert status_response.status_code == 200
    status = status_response.json()

    prompts = await storage.get_all_prompts()
    collections = await storage.get_all_collections()
    assert len(prompts) == status["prompts_created"]
    assert len(collections) == status["collections_created"]
    assert len(prompts) > 0
    assert len(collections) > 0

async def test_clear_all_data():
    """Clear-all-data endpoint must remove all existing prompts and collections.

    Seeds storage with one prompt and one collection, calls the endpoint, and
    confirms both the reported removal counts and the resulting empty storage state.
    """
    test_prompt = Prompt(
        id=str(uuid.uuid4()),
        title="Test Prompt",
        content="Test content",
        description="Test description",
        tags=["test"]
    )
    await storage.create_prompt(test_prompt)

    test_collection = Collection(
        id=str(uuid.uuid4()),
        name="Test Collection",
        description="Test description"
    )
    await storage.create_collection(test_collection)

    assert len(await storage.get_all_prompts()) == 1
    assert len(await storage.get_all_collections()) == 1

    response = client.delete("/admin/clear-all-data")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "prompts_removed" in data
    assert "collections_removed" in data
    assert data["prompts_removed"] == 1
    assert data["collections_removed"] == 1

    assert len(await storage.get_all_prompts()) == 0
    assert len(await storage.get_all_collections()) == 0

async def test_clear_all_data_when_empty():
    """Clear-all-data endpoint must succeed and report zero removals when storage is empty.

    Confirms the endpoint is idempotent and handles an already-empty storage gracefully
    without errors.
    """
    await storage.clear()

    assert len(await storage.get_all_prompts()) == 0
    assert len(await storage.get_all_collections()) == 0

    response = client.delete("/admin/clear-all-data")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["prompts_removed"] == 0
    assert data["collections_removed"] == 0

async def test_admin_endpoints_clear_storage_between_tests():
    """Storage must be empty after an explicit clear, ensuring no state leaks between tests.

    Note:
        This test guards against inadvertent cross-test contamination by verifying that
        a manual storage.clear() leaves both prompts and collections collections empty.
    """
    await storage.clear()

    assert len(await storage.get_all_prompts()) == 0
    assert len(await storage.get_all_collections()) == 0


async def test_populate_test_data_all_prompts_have_versions():
    """Every prompt created by populate-test-data must have at least one version snapshot.

    Note:
        populate-test-data must call create_prompt_version for every prompt it creates,
        otherwise version history is unavailable for those prompts.
    """
    await storage.clear()

    response = client.post("/admin/populate-test-data")
    assert response.status_code == 202

    # BackgroundTasks run synchronously in TestClient, so data is present now
    prompts = await storage.get_all_prompts()
    assert len(prompts) > 0, "populate-test-data created no prompts"

    for prompt in prompts:
        versions = await storage.get_all_prompt_versions(prompt.id)
        assert len(versions) >= 1, (
            f"Prompt {prompt.id!r} ({prompt.title!r}) has no version snapshots. "
            "populate-test-data must call create_prompt_version for every prompt it creates."
        )


def test_populate_test_data_storage_exception_records_error():
    """populate-test-data must record errors in populate-status when the background task fails.

    Since the endpoint returns 202 immediately (fire-and-forget), exceptions cannot
    surface as HTTP status codes. Instead they must be written to _populate_progress["error"]
    so that polling clients (e.g. PopulateStatusBar) can surface the failure.
    TestClient executes BackgroundTasks synchronously, so the error is present
    by the time we poll /admin/populate-status after the POST.
    """
    import app.api as api_module
    api_module._populate_progress.update({"current": 0, "total": 0, "active": False, "error": None})

    with patch.object(storage, "create_prompt", side_effect=RuntimeError("boom")):
        response = client.post("/admin/populate-test-data")

    assert response.status_code == 202

    status = client.get("/admin/populate-status")
    assert status.status_code == 200
    data = status.json()
    assert data["active"] is False
    assert data["error"] is not None
    assert "boom" in data["error"]


def test_populate_test_data_returns_409_when_already_running():
    """populate-test-data must return 409 Conflict if a populate is already in progress."""
    import app.api as api_module
    original = api_module._populate_progress.copy()
    api_module._populate_progress["active"] = True
    try:
        response = client.post("/admin/populate-test-data")
        assert response.status_code == 409
        assert "already in progress" in response.json()["detail"]
    finally:
        api_module._populate_progress.update(original)
        api_module._populate_progress["active"] = False


def test_clear_all_data_storage_exception_returns_500():
    """clear-all-data must return 500 when storage raises an unexpected exception.

    Uses mock to force storage.clear to raise, triggering the except block.
    """
    with patch.object(storage, "clear", side_effect=RuntimeError("boom")):
        response = client.delete("/admin/clear-all-data")
    assert response.status_code == 500
    assert "Failed to clear data" in response.json()["detail"]
