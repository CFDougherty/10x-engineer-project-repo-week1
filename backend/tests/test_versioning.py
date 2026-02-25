"""Tests for prompt versioning feature.

This test suite covers the versioning system that preserves historical versions
of prompts while maintaining a simple API for common CRUD operations.
"""

import pytest
from fastapi.testclient import TestClient
from app.models import Prompt, PromptCreate, PromptUpdate
from app.storage import storage
from datetime import datetime
from typing import Dict, List

# ============== Test Fixtures ==============

@pytest.fixture
def client():
    """Create a test client for the API."""
    from app.api import app
    return TestClient(app)

@pytest.fixture(autouse=True)
def clear_storage():
    """Clear storage before each test."""
    storage.clear()
    yield
    storage.clear()

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

# ============== Versioning Models ==============

class TestVersioningModels:
    """Test the data models for versioning."""

    def test_prompt_version_model_exists(self):
        """Verify that PromptVersion model can be imported and instantiated."""
        from app.models import PromptVersion
        version = PromptVersion(
            prompt_id="test-id",
            version=1,
            title="Test",
            content="Test content",
            description="Test description",
            collection_id=None
        )
        assert version.prompt_id == "test-id"
        assert version.version == 1
        assert version.title == "Test"
        assert version.content == "Test content"
        assert version.description == "Test description"
        assert version.collection_id is None
        assert isinstance(version.created_at, datetime)

    def test_prompt_meta_model_exists(self):
        """Verify that PromptMeta model can be imported and instantiated."""
        from app.models import PromptMeta
        meta = PromptMeta(
            id="test-id",
            current_version=1,
            created_at=datetime.utcnow()
        )
        assert meta.id == "test-id"
        assert meta.current_version == 1
        assert isinstance(meta.created_at, datetime)

# ============== Versioning Storage ==============

class TestVersioningStorage:
    """Test the storage layer for versioning."""

    def test_storage_has_versioning_indexes(self):
        """Verify that storage has the required versioning indexes."""
        # Check that the storage instance has the required attributes
        assert hasattr(storage, '_prompts')
        assert hasattr(storage, '_collections')

        # These will be added for versioning
        # assert hasattr(storage, '_prompt_meta')
        # assert hasattr(storage, '_prompt_versions')

    def test_create_prompt_creates_version_1(self):
        """Creating a prompt should create version 1."""
        from app.models import PromptCreate
        prompt_data = PromptCreate(
            title="Test Prompt",
            content="Test content",
            description="Test description"
        )

        # Create prompt
        prompt = Prompt(**prompt_data.model_dump())
        created = storage.create_prompt(prompt)

        # Verify prompt was created
        assert created.id == prompt.id
        assert created.title == "Test Prompt"
        assert created.content == "Test content"

        # For now, this just creates a regular prompt
        # After implementation, we'll verify versioning

    def test_update_prompt_creates_new_version(self):
        """Updating a prompt should create a new version."""
        from app.models import PromptCreate, PromptUpdate

        # Create initial prompt
        prompt_data = PromptCreate(
            title="Original",
            content="Original content",
            description="Original description"
        )
        prompt = Prompt(**prompt_data.model_dump())
        storage.create_prompt(prompt)
        prompt_id = prompt.id

        # Update the prompt
        update_data = PromptUpdate(
            title="Updated",
            content="Updated content",
            description="Updated description"
        )
        updated = storage.update_prompt(prompt_id, Prompt(**update_data.model_dump()))

        # Verify update
        assert updated.title == "Updated"
        assert updated.content == "Updated content"

        # After implementation, we'll verify version increment

    def test_patch_prompt_creates_new_version(self):
        """Patching a prompt should create a new version."""
        from app.models import PromptCreate, PromptUpdateOptional

        # Create initial prompt
        prompt_data = PromptCreate(
            title="Original",
            content="Original content",
            description="Original description"
        )
        prompt = Prompt(**prompt_data.model_dump())
        storage.create_prompt(prompt)
        prompt_id = prompt.id

        # Patch the prompt
        patch_data = PromptUpdateOptional(
            title="Patched",
            content=None,  # Don't change content
            description=None  # Don't change description
        )
        patched = storage.patch_prompt(prompt_id, patch_data)

        # Verify patch
        assert patched.title == "Patched"
        assert patched.content == "Original content"

        # After implementation, we'll verify version increment

# ============== API Endpoints ==============

class TestVersioningEndpoints:
    """Test the API endpoints for versioning."""

    def test_create_prompt_returns_version_metadata(self, client: TestClient):
        """POST /prompts should return version metadata."""
        prompt_data = {
            "title": "New Prompt",
            "content": "Prompt content",
            "description": "Prompt description"
        }

        response = client.post("/prompts", json=prompt_data)
        assert response.status_code == 201

        data = response.json()
        assert "id" in data
        assert "version" in data
        assert data["version"] == 1
        assert data["title"] == "New Prompt"
        assert data["content"] == "Prompt content"

    def test_update_prompt_creates_new_version(self, client: TestClient):
        """PUT /prompts/{id} should create a new version."""
        # Create initial prompt
        prompt_data = {
            "title": "Original",
            "content": "Original content",
            "description": "Original description"
        }
        create_response = client.post("/prompts", json=prompt_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]
        original_version = create_response.json()["version"]

        # Update the prompt
        update_data = {
            "title": "Updated",
            "content": "Updated content",
            "description": "Updated description"
        }
        update_response = client.put(f"/prompts/{prompt_id}", json=update_data)
        assert update_response.status_code == 200

        updated_data = update_response.json()
        assert updated_data["version"] == original_version + 1
        assert updated_data["title"] == "Updated"
        assert updated_data["content"] == "Updated content"

    def test_patch_prompt_creates_new_version(self, client: TestClient):
        """PATCH /prompts/{id} should create a new version."""
        # Create initial prompt
        prompt_data = {
            "title": "Original",
            "content": "Original content",
            "description": "Original description"
        }
        create_response = client.post("/prompts", json=prompt_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]
        original_version = create_response.json()["version"]

        # Patch the prompt
        patch_data = {
            "title": "Patched"
        }
        patch_response = client.patch(f"/prompts/{prompt_id}", json=patch_data)
        assert patch_response.status_code == 200

        patched_data = patch_response.json()
        assert patched_data["version"] == original_version + 1
        assert patched_data["title"] == "Patched"
        assert patched_data["content"] == "Original content"  # Unchanged

    def test_get_specific_version(self, client: TestClient):
        """GET /prompts/{id}/versions/{version} should return specific version."""
        # Create initial prompt
        prompt_data = {
            "title": "Version 1",
            "content": "Content 1",
            "description": "Description 1"
        }
        create_response = client.post("/prompts", json=prompt_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]

        # Update to create version 2
        update_data = {
            "title": "Version 2",
            "content": "Content 2",
            "description": "Description 2"
        }
        client.put(f"/prompts/{prompt_id}", json=update_data)

        # Get version 1
        version_response = client.get(f"/prompts/{prompt_id}/versions/1")
        assert version_response.status_code == 200

        version_data = version_response.json()
        assert version_data["version"] == 1
        assert version_data["title"] == "Version 1"
        assert version_data["content"] == "Content 1"
        assert version_data["description"] == "Description 1"

        # Get version 2
        version_response = client.get(f"/prompts/{prompt_id}/versions/2")
        assert version_response.status_code == 200

        version_data = version_response.json()
        assert version_data["version"] == 2
        assert version_data["title"] == "Version 2"
        assert version_data["content"] == "Content 2"
        assert version_data["description"] == "Description 2"

    def test_list_all_versions(self, client: TestClient):
        """GET /prompts/{id}/versions should return all versions."""
        # Create initial prompt
        prompt_data = {
            "title": "Version 1",
            "content": "Content 1",
            "description": "Description 1"
        }
        create_response = client.post("/prompts", json=prompt_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]

        # Update to create version 2
        update_data = {
            "title": "Version 2",
            "content": "Content 2",
            "description": "Description 2"
        }
        client.put(f"/prompts/{prompt_id}", json=update_data)

        # Update to create version 3
        update_data = {
            "title": "Version 3",
            "content": "Content 3",
            "description": "Description 3"
        }
        client.put(f"/prompts/{prompt_id}", json=update_data)

        # List all versions
        versions_response = client.get(f"/prompts/{prompt_id}/versions")
        assert versions_response.status_code == 200

        versions_data = versions_response.json()
        assert versions_data["prompt_id"] == prompt_id
        assert versions_data["total"] == 3
        assert len(versions_data["versions"]) == 3

        # Versions should be in descending order (newest first)
        assert versions_data["versions"][0]["version"] == 3
        assert versions_data["versions"][1]["version"] == 2
        assert versions_data["versions"][2]["version"] == 1

    def test_promote_version(self, client: TestClient):
        """POST /prompts/{id}/versions/{version}/promote should promote a version."""
        # Create initial prompt
        prompt_data = {
            "title": "Version 1",
            "content": "Content 1",
            "description": "Description 1"
        }
        create_response = client.post("/prompts", json=prompt_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]

        # Update to create version 2
        update_data = {
            "title": "Version 2",
            "content": "Content 2",
            "description": "Description 2"
        }
        client.put(f"/prompts/{prompt_id}", json=update_data)

        # Promote version 1
        promote_response = client.post(f"/prompts/{prompt_id}/versions/1/promote")
        assert promote_response.status_code == 201

        promoted_data = promote_response.json()
        assert promoted_data["version"] == 3  # New version created
        assert promoted_data["title"] == "Version 1"  # Same as version 1
        assert promoted_data["content"] == "Content 1"
        assert promoted_data["description"] == "Description 1"

        # Verify the latest version is now the promoted one
        latest_response = client.get(f"/prompts/{prompt_id}")
        assert latest_response.status_code == 200
        latest_data = latest_response.json()
        assert latest_data["version"] == 3
        assert latest_data["title"] == "Version 1"

# ============== Edge Cases ==============

class TestVersioningEdgeCases:
    """Test edge cases and error conditions for versioning."""

    def test_get_nonexistent_version(self, client: TestClient):
        """GET /prompts/{id}/versions/{version} should return 404 for nonexistent version."""
        # Create a prompt
        prompt_data = {
            "title": "Test",
            "content": "Content",
            "description": "Description"
        }
        create_response = client.post("/prompts", json=prompt_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]

        # Try to get version 999 (doesn't exist)
        response = client.get(f"/prompts/{prompt_id}/versions/999")
        assert response.status_code == 404

    def test_promote_nonexistent_version(self, client: TestClient):
        """POST /prompts/{id}/versions/{version}/promote should return 404 for nonexistent version."""
        # Create a prompt
        prompt_data = {
            "title": "Test",
            "content": "Content",
            "description": "Description"
        }
        create_response = client.post("/prompts", json=prompt_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]

        # Try to promote version 999 (doesn't exist)
        response = client.post(f"/prompts/{prompt_id}/versions/999/promote")
        assert response.status_code == 404

    def test_promote_nonexistent_prompt(self, client: TestClient):
        """POST /prompts/{id}/versions/{version}/promote should return 404 for nonexistent prompt."""
        response = client.post(f"/prompts/nonexistent-id/versions/1/promote")
        assert response.status_code == 404

    def test_version_history_preserved_after_promotion(self, client: TestClient):
        """Version history should be preserved after promoting a version."""
        # Create initial prompt
        prompt_data = {
            "title": "Version 1",
            "content": "Content 1",
            "description": "Description 1"
        }
        create_response = client.post("/prompts", json=prompt_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]

        # Update to create version 2
        update_data = {
            "title": "Version 2",
            "content": "Content 2",
            "description": "Description 2"
        }
        client.put(f"/prompts/{prompt_id}", json=update_data)

        # Promote version 1
        client.post(f"/prompts/{prompt_id}/versions/1/promote")

        # List all versions - should have 3 versions now
        versions_response = client.get(f"/prompts/{prompt_id}/versions")
        assert versions_response.status_code == 200

        versions_data = versions_response.json()
        assert versions_data["total"] == 3

        # All original versions should still exist
        version_1 = next((v for v in versions_data["versions"] if v["version"] == 1), None)
        version_2 = next((v for v in versions_data["versions"] if v["version"] == 2), None)
        version_3 = next((v for v in versions_data["versions"] if v["version"] == 3), None)

        assert version_1 is not None
        assert version_2 is not None
        assert version_3 is not None

        assert version_1["title"] == "Version 1"
        assert version_2["title"] == "Version 2"
        assert version_3["title"] == "Version 1"  # Promoted version

    def test_get_latest_version_returns_current(self, client: TestClient):
        """GET /prompts/{id} should return the latest version."""
        # Create initial prompt
        prompt_data = {
            "title": "Version 1",
            "content": "Content 1",
            "description": "Description 1"
        }
        create_response = client.post("/prompts", json=prompt_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]

        # Update to create version 2
        update_data = {
            "title": "Version 2",
            "content": "Content 2",
            "description": "Description 2"
        }
        client.put(f"/prompts/{prompt_id}", json=update_data)

        # Get latest version
        latest_response = client.get(f"/prompts/{prompt_id}")
        assert latest_response.status_code == 200

        latest_data = latest_response.json()
        assert latest_data["version"] == 2
        assert latest_data["title"] == "Version 2"
        assert latest_data["content"] == "Content 2"
        assert latest_data["description"] == "Description 2"

    def test_patch_with_no_changes_does_not_create_new_version(self, client: TestClient):
        """PATCH with no actual changes should not create a new version."""
        # Create initial prompt
        prompt_data = {
            "title": "Test",
            "content": "Content",
            "description": "Description"
        }
        create_response = client.post("/prompts", json=prompt_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]
        original_version = create_response.json()["version"]

        # Patch with no changes
        patch_response = client.patch(f"/prompts/{prompt_id}", json={})
        assert patch_response.status_code == 200

        patched_data = patch_response.json()
        assert patched_data["version"] == original_version  # Should not increment
        assert patched_data["title"] == "Test"

# ============== Integration Tests ==============

class TestVersioningIntegration:
    """Integration tests for versioning workflows."""

    def test_complete_versioning_workflow(self, client: TestClient):
        """Test a complete workflow: create, update, list, get specific, promote."""
        # 1. Create a prompt (version 1)
        prompt_data = {
            "title": "Summarize content",
            "content": "Summarize: {{input}}",
            "description": "Summarizes text input"
        }
        create_response = client.post("/prompts", json=prompt_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]
        assert create_response.json()["version"] == 1

        # 2. Update the prompt (version 2)
        update_data = {
            "title": "Summarize content v2",
            "content": "Summarize: {{input}}\nBe concise.",
            "description": "Summarizes text input concisely"
        }
        update_response = client.put(f"/prompts/{prompt_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["version"] == 2

        # 3. List all versions
        versions_response = client.get(f"/prompts/{prompt_id}/versions")
        assert versions_response.status_code == 200
        assert versions_response.json()["total"] == 2

        # 4. Get specific version (version 1)
        version_1_response = client.get(f"/prompts/{prompt_id}/versions/1")
        assert version_1_response.status_code == 200
        assert version_1_response.json()["title"] == "Summarize content"
        assert version_1_response.json()["content"] == "Summarize: {{input}}"

        # 5. Promote version 1 (creates version 3)
        promote_response = client.post(f"/prompts/{prompt_id}/versions/1/promote")
        assert promote_response.status_code == 201
        assert promote_response.json()["version"] == 3
        assert promote_response.json()["title"] == "Summarize content"

        # 6. Verify latest is now the promoted version
        latest_response = client.get(f"/prompts/{prompt_id}")
        assert latest_response.status_code == 200
        assert latest_response.json()["version"] == 3
        assert latest_response.json()["title"] == "Summarize content"

        # 7. Verify all 3 versions still exist
        final_versions_response = client.get(f"/prompts/{prompt_id}/versions")
        assert final_versions_response.status_code == 200
        assert final_versions_response.json()["total"] == 3

    def test_versioning_with_collection(self, client: TestClient):
        """Test versioning when prompts belong to collections."""
        # Create a collection
        collection_data = {
            "name": "Test Collection",
            "description": "Test collection"
        }
        collection_response = client.post("/collections", json=collection_data)
        assert collection_response.status_code == 201
        collection_id = collection_response.json()["id"]

        # Create a prompt in the collection (version 1)
        prompt_data = {
            "title": "Test Prompt",
            "content": "Test content",
            "description": "Test description",
            "collection_id": collection_id
        }
        create_response = client.post("/prompts", json=prompt_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]
        assert create_response.json()["version"] == 1
        assert create_response.json()["collection_id"] == collection_id

        # Update the prompt (version 2) - change collection
        update_data = {
            "title": "Updated Prompt",
            "content": "Updated content",
            "description": "Updated description",
            "collection_id": None
        }
        update_response = client.put(f"/prompts/{prompt_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["version"] == 2
        assert update_response.json()["collection_id"] is None

        # Get version 1 - should still have the original collection_id
        version_1_response = client.get(f"/prompts/{prompt_id}/versions/1")
        assert version_1_response.status_code == 200
        assert version_1_response.json()["collection_id"] == collection_id

        # Get version 2 - should have None
        version_2_response = client.get(f"/prompts/{prompt_id}/versions/2")
        assert version_2_response.status_code == 200
        assert version_2_response.json()["collection_id"] is None

    def test_multiple_prompts_independent_versioning(self, client: TestClient):
        """Test that multiple prompts maintain independent version histories."""
        # Create two prompts
        prompt1_data = {
            "title": "Prompt 1",
            "content": "Content 1",
            "description": "Description 1"
        }
        prompt1_response = client.post("/prompts", json=prompt1_data)
        assert prompt1_response.status_code == 201
        prompt1_id = prompt1_response.json()["id"]

        prompt2_data = {
            "title": "Prompt 2",
            "content": "Content 2",
            "description": "Description 2"
        }
        prompt2_response = client.post("/prompts", json=prompt2_data)
        assert prompt2_response.status_code == 201
        prompt2_id = prompt2_response.json()["id"]

        # Update prompt 1 twice
        client.put(f"/prompts/{prompt1_id}", json={"title": "Prompt 1 v2", "content": "Content 1 v2", "description": "Description 1 v2"})
        client.put(f"/prompts/{prompt1_id}", json={"title": "Prompt 1 v3", "content": "Content 1 v3", "description": "Description 1 v3"})

        # Update prompt 2 once
        client.put(f"/prompts/{prompt2_id}", json={"title": "Prompt 2 v2", "content": "Content 2 v2", "description": "Description 2 v2"})

        # Check versions
        prompt1_versions = client.get(f"/prompts/{prompt1_id}/versions")
        assert prompt1_versions.json()["total"] == 3

        prompt2_versions = client.get(f"/prompts/{prompt2_id}/versions")
        assert prompt2_versions.json()["total"] == 2