"""Tests for admin API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.api import app
from app.storage import storage
from app.models import Prompt, Collection
import uuid

client = TestClient(app)

def test_populate_test_data():
    """Test the populate test data endpoint."""
    # Clear any existing data
    storage.clear()

    # Verify storage is empty
    assert len(storage.get_all_prompts()) == 0
    assert len(storage.get_all_collections()) == 0

    # Call the endpoint
    response = client.post("/admin/populate-test-data")

    # Verify success
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "prompts_created" in data
    assert "collections_created" in data
    assert data["prompts_created"] > 0
    assert data["collections_created"] > 0

    # Verify data was actually created
    prompts = storage.get_all_prompts()
    collections = storage.get_all_collections()
    assert len(prompts) == data["prompts_created"]
    assert len(collections) == data["collections_created"]
    assert len(prompts) > 0
    assert len(collections) > 0

def test_clear_all_data():
    """Test the clear all data endpoint."""
    # First, populate some data
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

    # Verify data exists
    assert len(storage.get_all_prompts()) == 1
    assert len(storage.get_all_collections()) == 1

    # Call the endpoint
    response = client.delete("/admin/clear-all-data")

    # Verify success
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "prompts_removed" in data
    assert "collections_removed" in data
    assert data["prompts_removed"] == 1
    assert data["collections_removed"] == 1

    # Verify data was actually cleared
    assert len(storage.get_all_prompts()) == 0
    assert len(storage.get_all_collections()) == 0

def test_clear_all_data_when_empty():
    """Test clearing data when storage is already empty."""
    # Clear any existing data first
    storage.clear()

    # Verify storage is empty
    assert len(storage.get_all_prompts()) == 0
    assert len(storage.get_all_collections()) == 0

    # Call the endpoint
    response = client.delete("/admin/clear-all-data")

    # Verify success
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["prompts_removed"] == 0
    assert data["collections_removed"] == 0

def test_admin_endpoints_clear_storage_between_tests():
    """Test that admin endpoints properly clear storage."""
    # This test ensures that the storage is properly cleared
    # and doesn't leak between tests

    # Clear storage first
    storage.clear()

    # Verify it's empty
    assert len(storage.get_all_prompts()) == 0
    assert len(storage.get_all_collections()) == 0