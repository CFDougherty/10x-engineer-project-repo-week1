"""Versioning endpoint tests for PromptLab API.

These tests verify the versioning endpoints work correctly.
"""

import pytest
from fastapi.testclient import TestClient

class TestVersioningEndpoints:
    """Tests for prompt versioning endpoints.

    Covers version creation on PUT/PATCH, retrieval of specific versions,
    listing all versions, version promotion, immutability of historical
    snapshots, and edge cases such as no-op patches and sequential numbering.
    """

    def test_create_prompt_returns_version_metadata(self, client: TestClient):
        """POST /prompts should return version metadata with version number 1.

        Args:
            client: TestClient instance for making API requests.
        """
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
        """PUT /prompts/{id} should increment the version number by one.

        Args:
            client: TestClient instance for making API requests.
        """
        prompt_data = {
            "title": "Original",
            "content": "Original content",
            "description": "Original description"
        }
        create_response = client.post("/prompts", json=prompt_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]
        original_version = create_response.json()["version"]

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
        """PATCH /prompts/{id} should increment the version number by one.

        Args:
            client: TestClient instance for making API requests.
        """
        prompt_data = {
            "title": "Original",
            "content": "Original content",
            "description": "Original description"
        }
        create_response = client.post("/prompts", json=prompt_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]
        original_version = create_response.json()["version"]

        patch_data = {
            "title": "Patched"
        }
        patch_response = client.patch(f"/prompts/{prompt_id}", json=patch_data)
        assert patch_response.status_code == 200

        patched_data = patch_response.json()
        assert patched_data["version"] == original_version + 1
        assert patched_data["title"] == "Patched"
        assert patched_data["content"] == "Original content"

    def test_get_specific_version(self, client: TestClient):
        """GET /prompts/{id}/versions/{version} should return the exact historical snapshot.

        Args:
            client: TestClient instance for making API requests.
        """
        prompt_data = {
            "title": "Version 1",
            "content": "Content 1",
            "description": "Description 1"
        }
        create_response = client.post("/prompts", json=prompt_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]

        update_data = {
            "title": "Version 2",
            "content": "Content 2",
            "description": "Description 2"
        }
        client.put(f"/prompts/{prompt_id}", json=update_data)

        version_response = client.get(f"/prompts/{prompt_id}/versions/1")
        assert version_response.status_code == 200

        version_data = version_response.json()
        assert version_data["version"] == 1
        assert version_data["title"] == "Version 1"
        assert version_data["content"] == "Content 1"
        assert version_data["description"] == "Description 1"

        version_response = client.get(f"/prompts/{prompt_id}/versions/2")
        assert version_response.status_code == 200

        version_data = version_response.json()
        assert version_data["version"] == 2
        assert version_data["title"] == "Version 2"
        assert version_data["content"] == "Content 2"
        assert version_data["description"] == "Description 2"

    def test_list_all_versions(self, client: TestClient):
        """GET /prompts/{id}/versions should return all versions sorted newest first.

        Args:
            client: TestClient instance for making API requests.
        """
        prompt_data = {
            "title": "Version 1",
            "content": "Content 1",
            "description": "Description 1"
        }
        create_response = client.post("/prompts", json=prompt_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]

        update_data = {
            "title": "Version 2",
            "content": "Content 2",
            "description": "Description 2"
        }
        client.put(f"/prompts/{prompt_id}", json=update_data)

        update_data = {
            "title": "Version 3",
            "content": "Content 3",
            "description": "Description 3"
        }
        client.put(f"/prompts/{prompt_id}", json=update_data)

        versions_response = client.get(f"/prompts/{prompt_id}/versions")
        assert versions_response.status_code == 200

        versions_data = versions_response.json()
        assert versions_data["prompt_id"] == prompt_id
        assert versions_data["total"] == 3
        assert len(versions_data["versions"]) == 3

        assert versions_data["versions"][0]["version"] == 3
        assert versions_data["versions"][1]["version"] == 2
        assert versions_data["versions"][2]["version"] == 1

    def test_promote_version(self, client: TestClient):
        """POST /prompts/{id}/versions/{version}/promote should create a new version from an older one.

        Promoting copies the historical snapshot's content into a brand-new version
        at the head of the version list rather than overwriting any existing version.

        Args:
            client: TestClient instance for making API requests.
        """
        prompt_data = {
            "title": "Version 1",
            "content": "Content 1",
            "description": "Description 1"
        }
        create_response = client.post("/prompts", json=prompt_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]

        update_data = {
            "title": "Version 2",
            "content": "Content 2",
            "description": "Description 2"
        }
        client.put(f"/prompts/{prompt_id}", json=update_data)

        promote_response = client.post(f"/prompts/{prompt_id}/versions/1/promote")
        assert promote_response.status_code == 201

        promoted_data = promote_response.json()
        assert promoted_data["version"] == 3
        assert promoted_data["title"] == "Version 1"
        assert promoted_data["content"] == "Content 1"
        assert promoted_data["description"] == "Description 1"

        latest_response = client.get(f"/prompts/{prompt_id}")
        assert latest_response.status_code == 200
        latest_data = latest_response.json()
        assert latest_data["version"] == 3
        assert latest_data["title"] == "Version 1"

    def test_get_nonexistent_version(self, client: TestClient):
        """GET /prompts/{id}/versions/{version} should return 404 for a version that does not exist.

        Args:
            client: TestClient instance for making API requests.
        """
        prompt_data = {
            "title": "Test",
            "content": "Content",
            "description": "Description"
        }
        create_response = client.post("/prompts", json=prompt_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]

        response = client.get(f"/prompts/{prompt_id}/versions/999")
        assert response.status_code == 404

    def test_promote_nonexistent_version(self, client: TestClient):
        """POST /prompts/{id}/versions/{version}/promote should return 404 for a version that does not exist.

        Args:
            client: TestClient instance for making API requests.
        """
        prompt_data = {
            "title": "Test",
            "content": "Content",
            "description": "Description"
        }
        create_response = client.post("/prompts", json=prompt_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]

        response = client.post(f"/prompts/{prompt_id}/versions/999/promote")
        assert response.status_code == 404

    def test_promote_nonexistent_prompt(self, client: TestClient):
        """POST /prompts/{id}/versions/{version}/promote should return 404 for a prompt that does not exist.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.post(f"/prompts/nonexistent-id/versions/1/promote")
        assert response.status_code == 404

    def test_version_history_preserved_after_promotion(self, client: TestClient):
        """All previous versions should remain accessible after a version is promoted.

        Args:
            client: TestClient instance for making API requests.
        """
        prompt_data = {
            "title": "Version 1",
            "content": "Content 1",
            "description": "Description 1"
        }
        create_response = client.post("/prompts", json=prompt_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]

        update_data = {
            "title": "Version 2",
            "content": "Content 2",
            "description": "Description 2"
        }
        client.put(f"/prompts/{prompt_id}", json=update_data)

        client.post(f"/prompts/{prompt_id}/versions/1/promote")

        versions_response = client.get(f"/prompts/{prompt_id}/versions")
        assert versions_response.status_code == 200

        versions_data = versions_response.json()
        assert versions_data["total"] == 3

        version_1 = next((v for v in versions_data["versions"] if v["version"] == 1), None)
        version_2 = next((v for v in versions_data["versions"] if v["version"] == 2), None)
        version_3 = next((v for v in versions_data["versions"] if v["version"] == 3), None)

        assert version_1 is not None
        assert version_2 is not None
        assert version_3 is not None

        assert version_1["title"] == "Version 1"
        assert version_2["title"] == "Version 2"
        assert version_3["title"] == "Version 1"

    def test_get_latest_version_returns_current(self, client: TestClient):
        """GET /prompts/{id} should return the latest version after an update.

        Args:
            client: TestClient instance for making API requests.
        """
        prompt_data = {
            "title": "Version 1",
            "content": "Content 1",
            "description": "Description 1"
        }
        create_response = client.post("/prompts", json=prompt_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]

        update_data = {
            "title": "Version 2",
            "content": "Content 2",
            "description": "Description 2"
        }
        client.put(f"/prompts/{prompt_id}", json=update_data)

        latest_response = client.get(f"/prompts/{prompt_id}")
        assert latest_response.status_code == 200

        latest_data = latest_response.json()
        assert latest_data["version"] == 2
        assert latest_data["title"] == "Version 2"
        assert latest_data["content"] == "Content 2"
        assert latest_data["description"] == "Description 2"

    def test_patch_with_no_changes_does_not_create_new_version(self, client: TestClient):
        """PATCH with an empty payload should not increment the version number.

        Args:
            client: TestClient instance for making API requests.
        """
        prompt_data = {
            "title": "Test",
            "content": "Content",
            "description": "Description"
        }
        create_response = client.post("/prompts", json=prompt_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]
        original_version = create_response.json()["version"]

        patch_response = client.patch(f"/prompts/{prompt_id}", json={})
        assert patch_response.status_code == 200

        patched_data = patch_response.json()
        assert patched_data["version"] == original_version
        assert patched_data["title"] == "Test"

    def test_promote_version_preserves_original_created_at(self, client: TestClient):
        """Promoting a version must keep the original prompt's created_at, not reset it.

        Note:
            This is a known failing test. storage.promote_prompt_version() currently
            creates a new Prompt() with created_at=now(). The fix is to pass
            created_at=original_prompt.created_at when constructing the promoted Prompt.

        Args:
            client: TestClient instance for making API requests.
        """
        create_resp = client.post("/prompts", json={"title": "V1", "content": "Content 1"})
        assert create_resp.status_code == 201
        prompt_id = create_resp.json()["id"]
        original_created_at = create_resp.json()["created_at"]

        client.put(f"/prompts/{prompt_id}", json={"title": "V2", "content": "Content 2"})

        promote_resp = client.post(f"/prompts/{prompt_id}/versions/1/promote")
        assert promote_resp.status_code == 201

        assert promote_resp.json()["created_at"] == original_created_at

    def test_promote_version_updates_updated_at(self, client: TestClient):
        """Promoting a version should set updated_at to the promotion time, not the original creation time.

        Args:
            client: TestClient instance for making API requests.
        """
        import time
        create_resp = client.post("/prompts", json={"title": "V1", "content": "Content 1"})
        prompt_id = create_resp.json()["id"]
        original_updated_at = create_resp.json()["updated_at"]

        client.put(f"/prompts/{prompt_id}", json={"title": "V2", "content": "Content 2"})

        time.sleep(0.05)
        promote_resp = client.post(f"/prompts/{prompt_id}/versions/1/promote")
        assert promote_resp.status_code == 201

        assert promote_resp.json()["updated_at"] != original_updated_at

    def test_patch_with_same_values_does_not_increment_version_count(self, client: TestClient):
        """PATCH with identical field values keeps total version count at 1.

        Args:
            client: TestClient instance for making API requests.
        """
        create_resp = client.post("/prompts", json={
            "title": "Same Title",
            "content": "Same Content",
            "description": "Same Desc",
        })
        prompt_id = create_resp.json()["id"]

        client.patch(f"/prompts/{prompt_id}", json={"title": "Same Title"})

        versions = client.get(f"/prompts/{prompt_id}/versions").json()
        assert versions["total"] == 1

    def test_version_numbers_are_sequential(self, client: TestClient):
        """After 5 updates version numbers should be exactly 1 through 5.

        Args:
            client: TestClient instance for making API requests.
        """
        create_resp = client.post("/prompts", json={"title": "V1", "content": "Content"})
        prompt_id = create_resp.json()["id"]

        for i in range(2, 6):
            client.put(f"/prompts/{prompt_id}", json={"title": f"V{i}", "content": f"Content {i}"})

        versions = client.get(f"/prompts/{prompt_id}/versions").json()
        version_numbers = sorted(v["version"] for v in versions["versions"])
        assert version_numbers == [1, 2, 3, 4, 5]

    def test_promote_version_creates_new_version_not_overwrite(self, client: TestClient):
        """Promoting a version appends a new version instead of overwriting existing ones.

        Args:
            client: TestClient instance for making API requests.
        """
        create_resp = client.post("/prompts", json={"title": "V1", "content": "Content 1"})
        prompt_id = create_resp.json()["id"]

        client.put(f"/prompts/{prompt_id}", json={"title": "V2", "content": "Content 2"})

        client.post(f"/prompts/{prompt_id}/versions/1/promote")

        versions = client.get(f"/prompts/{prompt_id}/versions").json()
        assert versions["total"] == 3

    def test_version_snapshot_is_immutable(self, client: TestClient):
        """After updating a prompt, the v1 snapshot must still hold the original content.

        Args:
            client: TestClient instance for making API requests.
        """
        create_resp = client.post("/prompts", json={
            "title": "Original Title",
            "content": "Original Content",
        })
        prompt_id = create_resp.json()["id"]

        client.put(f"/prompts/{prompt_id}", json={
            "title": "Updated Title",
            "content": "Updated Content",
        })

        v1 = client.get(f"/prompts/{prompt_id}/versions/1").json()
        assert v1["title"] == "Original Title"
        assert v1["content"] == "Original Content"

    def test_get_versions_returns_newest_first(self, client: TestClient):
        """GET /prompts/{id}/versions must sort versions newest (highest number) first.

        Args:
            client: TestClient instance for making API requests.
        """
        create_resp = client.post("/prompts", json={"title": "V1", "content": "Content"})
        prompt_id = create_resp.json()["id"]

        for i in range(2, 5):
            client.put(f"/prompts/{prompt_id}", json={"title": f"V{i}", "content": f"Content {i}"})

        versions = client.get(f"/prompts/{prompt_id}/versions").json()["versions"]
        version_numbers = [v["version"] for v in versions]
        assert version_numbers == sorted(version_numbers, reverse=True)
