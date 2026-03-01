"""Tests for admin API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.api import app
from app.storage import storage
from app.models import Prompt, Collection
import uuid

client = TestClient(app)

def test_populate_test_data():
    """Populate-test-data endpoint must create prompts and collections and report counts.

    Verifies the endpoint returns a success status, reports non-zero creation counts,
    and that the storage state matches the reported counts after the call.
    """
    storage.clear()

    assert len(storage.get_all_prompts()) == 0
    assert len(storage.get_all_collections()) == 0

    response = client.post("/admin/populate-test-data")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "prompts_created" in data
    assert "collections_created" in data
    assert data["prompts_created"] > 0
    assert data["collections_created"] > 0

    prompts = storage.get_all_prompts()
    collections = storage.get_all_collections()
    assert len(prompts) == data["prompts_created"]
    assert len(collections) == data["collections_created"]
    assert len(prompts) > 0
    assert len(collections) > 0

def test_clear_all_data():
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
    storage.create_prompt(test_prompt)

    test_collection = Collection(
        id=str(uuid.uuid4()),
        name="Test Collection",
        description="Test description"
    )
    storage.create_collection(test_collection)

    assert len(storage.get_all_prompts()) == 1
    assert len(storage.get_all_collections()) == 1

    response = client.delete("/admin/clear-all-data")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "prompts_removed" in data
    assert "collections_removed" in data
    assert data["prompts_removed"] == 1
    assert data["collections_removed"] == 1

    assert len(storage.get_all_prompts()) == 0
    assert len(storage.get_all_collections()) == 0

def test_clear_all_data_when_empty():
    """Clear-all-data endpoint must succeed and report zero removals when storage is empty.

    Confirms the endpoint is idempotent and handles an already-empty storage gracefully
    without errors.
    """
    storage.clear()

    assert len(storage.get_all_prompts()) == 0
    assert len(storage.get_all_collections()) == 0

    response = client.delete("/admin/clear-all-data")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["prompts_removed"] == 0
    assert data["collections_removed"] == 0

def test_admin_endpoints_clear_storage_between_tests():
    """Storage must be empty after an explicit clear, ensuring no state leaks between tests.

    Note:
        This test guards against inadvertent cross-test contamination by verifying that
        a manual storage.clear() leaves both prompts and collections collections empty.
    """
    storage.clear()

    assert len(storage.get_all_prompts()) == 0
    assert len(storage.get_all_collections()) == 0


def test_populate_test_data_all_prompts_have_versions():
    """Every prompt created by populate-test-data must have at least one version snapshot.

    Note:
        populate-test-data must call create_prompt_version for every prompt it creates,
        otherwise version history is unavailable for those prompts.
    """
    storage.clear()

    response = client.post("/admin/populate-test-data")
    assert response.status_code == 200

    prompts = storage.get_all_prompts()
    assert len(prompts) > 0, "populate-test-data created no prompts"

    for prompt in prompts:
        versions = storage.get_all_prompt_versions(prompt.id)
        assert len(versions) >= 1, (
            f"Prompt {prompt.id!r} ({prompt.title!r}) has no version snapshots. "
            "populate-test-data must call create_prompt_version for every prompt it creates."
        )
