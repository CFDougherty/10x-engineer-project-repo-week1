"""Collection endpoint tests for PromptLab API.

These tests verify the collection CRUD endpoints work correctly.
"""

import pytest
from fastapi.testclient import TestClient

class TestCollections:
    """Tests for collection endpoints."""

    def test_create_collection(self, client: TestClient, sample_collection_data):
        """Test the creation of a new collection."""

        response = client.post("/collections", json=sample_collection_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_collection_data["name"]
        assert "id" in data

    def test_create_collection_with_empty_name(self, client: TestClient):
        """Test creating a collection with empty name."""
        response = client.post("/collections", json={"name": ""})
        assert response.status_code == 400

    def test_create_collection_with_very_long_name(self, client: TestClient):
        """Test creating a collection with very long name."""
        long_name = "A" * 101  # Exceeds 100 character limit
        response = client.post("/collections", json={"name": long_name})
        assert response.status_code == 400

    def test_create_collection_with_special_characters(self, client: TestClient):
        """Test creating a collection with special characters."""
        special_data = {
            "name": "Test <script>alert('xss')</script>",
            "description": "Special chars: \n\t\r, quotes '\""
        }
        response = client.post("/collections", json=special_data)
        assert response.status_code == 201

    def test_create_collection_with_null_values(self, client: TestClient):
        """Test creating a collection with null values."""
        response = client.post("/collections", json={"name": None})
        assert response.status_code == 400

    def test_create_collection_missing_required_field(self, client: TestClient):
        """Test creating a collection without name."""
        response = client.post("/collections", json={"description": "Some description"})
        assert response.status_code == 400

    def test_list_collections(self, client: TestClient, sample_collection_data):
        """Test listing collections by creating and retrieving a collection.

        Args:
            client: A test client for sending HTTP requests.
            sample_collection_data: Sample data to be used for creating a collection.
        """
        client.post("/collections", json=sample_collection_data)

        response = client.get("/collections")
        assert response.status_code == 200
        data = response.json()
        assert len(data["collections"]) == 1

    def test_list_collections_empty(self, client: TestClient):
        """Test listing collections when none exist."""
        response = client.get("/collections")
        assert response.status_code == 200
        data = response.json()
        assert data["collections"] == []
        assert data["total"] == 0

    def test_get_collection_not_found(self, client: TestClient):
        # The following function tests that retrieving a non-existent collection
        # returns a 404 status code.

        """
        Test that retrieving a non-existent collection returns a 404 status code.

        Args:
            client: TestClient used to send requests to the API.
        """
        response = client.get("/collections/nonexistent-id")
        assert response.status_code == 404

    def test_update_collection(self, client: TestClient, sample_collection_data):
        """Test updating an existing collection."""
        # Create a collection first
        create_response = client.post("/collections", json=sample_collection_data)
        collection_id = create_response.json()["id"]

        # Update it
        updated_data = {
            "name": "Updated Collection Name",
            "description": "Updated description for the collection"
        }

        response = client.put(f"/collections/{collection_id}", json=updated_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Collection Name"
        assert data["description"] == "Updated description for the collection"

    def test_update_collection_with_invalid_data(self, client: TestClient, sample_collection_data):
        """Test updating a collection with invalid data."""
        # Create a collection first
        create_response = client.post("/collections", json=sample_collection_data)
        collection_id = create_response.json()["id"]

        # Try to update with empty name
        response = client.put(f"/collections/{collection_id}", json={"name": ""})
        assert response.status_code == 400

    def test_update_collection_not_found(self, client: TestClient):
        """Test updating a non-existent collection."""
        response = client.put("/collections/nonexistent-id", json={"name": "New Name"})
        assert response.status_code == 404

    def test_patch_collection_partial_update(self, client: TestClient, sample_collection_data):
        """Test partially updating a collection."""
        # Create a collection first
        create_response = client.post("/collections", json=sample_collection_data)
        collection_id = create_response.json()["id"]
        original_data = create_response.json()

        # Partially update
        partial_update_data = {
            "name": "Partially Updated Name"
        }

        response = client.patch(f"/collections/{collection_id}", json=partial_update_data)
        assert response.status_code == 200
        updated_data = response.json()

        # Verify updated fields
        assert updated_data["name"] == partial_update_data["name"]

        # Verify unchanged fields
        assert updated_data["description"] == original_data["description"]

    def test_patch_collection_non_existent(self, client: TestClient):
        """Test patching a non-existent collection."""
        response = client.patch("/collections/nonexistent-id", json={"name": "New Name"})
        assert response.status_code == 404

    def test_patch_collection_empty_payload(self, client: TestClient, sample_collection_data):
        """Test patch request with empty payload."""
        # Create a collection first
        create_response = client.post("/collections", json=sample_collection_data)
        collection_id = create_response.json()["id"]
        original_data = create_response.json()

        # Patch with empty payload
        response = client.patch(f"/collections/{collection_id}", json={})
        assert response.status_code == 200
        unchanged_data = response.json()

        # Verify the data remains unchanged
        assert unchanged_data == original_data

    def test_delete_collection_with_prompts(self, client: TestClient, sample_collection_data, sample_prompt_data):
        """Test the deletion of a collection with associated prompts.

        Args:
        client: The test client used to perform API requests.
        sample_collection_data: The data for creating a sample collection.
        sample_prompt_data: The data for creating a sample prompt.

        NOTE: Bug #4 - prompts become orphaned after collection deletion.
        This test documents the current (buggy) behavior.
        After fixing, update the test to verify correct behavior.
        """
        # Create collection
        col_response = client.post("/collections", json=sample_collection_data)
        collection_id = col_response.json()["id"]

        # Create prompt in collection
        prompt_data = {**sample_prompt_data, "collection_id": collection_id}
        prompt_response = client.post("/prompts", json=prompt_data)
        prompt_id = prompt_response.json()["id"]

        # Delete collection
        client.delete(f"/collections/{collection_id}")

        # The prompt still exists but has invalid collection_id
        # This is Bug #4 - should be handled properly
        prompts = client.get("/prompts").json()["prompts"]
        if prompts:
            # Prompt exists with orphaned collection_id
            assert prompts[0]["collection_id"] == collection_id
            # After fix, collection_id should be None or prompt should be deleted

    def test_delete_collection_nonexistent(self, client: TestClient):
        """Test deleting a non-existent collection."""
        response = client.delete("/collections/nonexistent-id")
        assert response.status_code == 404

    def test_delete_collection_twice(self, client: TestClient, sample_collection_data):
        """Test deleting a collection twice."""
        # Create collection
        col_response = client.post("/collections", json=sample_collection_data)
        collection_id = col_response.json()["id"]

        # Delete it once
        response1 = client.delete(f"/collections/{collection_id}")
        assert response1.status_code == 204

        # Try to delete it again
        response2 = client.delete(f"/collections/{collection_id}")
        assert response2.status_code == 404

    def test_delete_collection_also_deletes_prompts(self, client: TestClient, sample_collection_data, sample_prompt_data):
        """Verify prompts are deleted when a collection is deleted.

        Args:
            client: TestClient instance for API requests.
            sample_collection_data: Data used to create a test collection.
            sample_prompt_data: Data used to create a test prompt.
        """
        # Create collection
        col_response = client.post("/collections", json=sample_collection_data)
        collection_id = col_response.json()["id"]

        # Create prompt in collection
        prompt_data = {**sample_prompt_data, "collection_id": collection_id}
        client.post("/prompts", json=prompt_data)

        # Delete collection
        client.delete(f"/collections/{collection_id}")

        # Verify all prompts are deleted
        response = client.get("/prompts")
        assert response.json()["prompts"] == []

    def test_delete_collection_sets_prompt_collection_id_to_none(self, client: TestClient, sample_collection_data, sample_prompt_data):
        """Test collection deletion sets prompts' collection_id to None.

        Args:
            client: A test client instance for making HTTP requests.
            sample_collection_data: Sample data for creating a collection.
            sample_prompt_data: Sample data for creating a prompt.
        """
        # Create collection
        col_response = client.post("/collections", json=sample_collection_data)
        collection_id = col_response.json()["id"]

        # Create prompt in collection
        prompt_data = {**sample_prompt_data, "collection_id": collection_id}
        client.post("/prompts", json=prompt_data)

        # Delete collection
        client.delete(f"/collections/{collection_id}")

        # Verify prompts collection_id is None
        response = client.get("/prompts")
        for prompt in response.json()["prompts"]:
            assert prompt["collection_id"] is None

    def test_collection_response_format(self, client: TestClient, sample_collection_data):
        """Test that collection responses have consistent format."""
        # Create collection
        create_response = client.post("/collections", json=sample_collection_data)
        collection_id = create_response.json()["id"]

        # Get collection
        get_response = client.get(f"/collections/{collection_id}")
        data = get_response.json()

        # Verify required fields
        required_fields = ["id", "name", "created_at"]
        for field in required_fields:
            assert field in data

        # Verify optional fields
        optional_fields = ["description"]
        for field in optional_fields:
            assert field in data

    def test_collection_validation_consistency(self, client: TestClient):
        """Test that collection validation rules are consistently applied."""
        # Test name validation
        response1 = client.post("/collections", json={"name": ""})
        assert response1.status_code == 400

        # Test name length validation
        response2 = client.post("/collections", json={"name": "A" * 101})
        assert response2.status_code == 400