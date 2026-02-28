"""Versioning endpoint tests for PromptLab API.

These tests verify the versioning endpoints work correctly.
"""

import pytest
from fastapi.testclient import TestClient

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