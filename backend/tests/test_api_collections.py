"""Collection endpoint tests for PromptLab API.

These tests verify the collection CRUD endpoints work correctly.
"""

import pytest
from fastapi.testclient import TestClient

class TestCollections:
    """Tests for the /collections CRUD endpoints.

    Covers creation, retrieval, update (PUT and PATCH), deletion, response
    format validation, and cascading behaviour when a collection is removed.
    """

    def test_create_collection(self, client: TestClient, sample_collection_data):
        """Creating a new collection returns 201 with the expected fields.

        Args:
            client: TestClient instance for making API requests.
            sample_collection_data: Fixture providing base collection creation data.
        """
        response = client.post("/collections", json=sample_collection_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_collection_data["name"]
        assert "id" in data

    def test_create_collection_with_empty_name(self, client: TestClient):
        """Creating a collection with an empty name string must be rejected with 400.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.post("/collections", json={"name": ""})
        assert response.status_code == 400

    def test_create_collection_with_very_long_name(self, client: TestClient):
        """Creating a collection whose name exceeds 100 characters must be rejected with 400.

        Args:
            client: TestClient instance for making API requests.
        """
        long_name = "A" * 101
        response = client.post("/collections", json={"name": long_name})
        assert response.status_code == 400

    def test_create_collection_with_special_characters(self, client: TestClient):
        """Creating a collection with special characters in the name and description is allowed.

        Args:
            client: TestClient instance for making API requests.
        """
        special_data = {
            "name": "Test <script>alert('xss')</script>",
            "description": "Special chars: \n\t\r, quotes '\""
        }
        response = client.post("/collections", json=special_data)
        assert response.status_code == 201

    def test_create_collection_with_null_values(self, client: TestClient):
        """Creating a collection with a null name must be rejected with 400.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.post("/collections", json={"name": None})
        assert response.status_code == 400

    def test_create_collection_missing_required_field(self, client: TestClient):
        """Creating a collection without the required name field must be rejected with 400.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.post("/collections", json={"description": "Some description"})
        assert response.status_code == 400

    def test_list_collections(self, client: TestClient, sample_collection_data):
        """Listing collections after creating one returns exactly one result.

        Args:
            client: TestClient instance for making API requests.
            sample_collection_data: Fixture providing base collection creation data.
        """
        client.post("/collections", json=sample_collection_data)

        response = client.get("/collections")
        assert response.status_code == 200
        data = response.json()
        assert len(data["collections"]) == 1

    def test_list_collections_empty(self, client: TestClient):
        """Listing collections when none exist returns an empty list with total=0.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.get("/collections")
        assert response.status_code == 200
        data = response.json()
        assert data["collections"] == []
        assert data["total"] == 0

    def test_get_collection_not_found(self, client: TestClient):
        """Retrieving a non-existent collection by ID must return 404.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.get("/collections/nonexistent-id")
        assert response.status_code == 404

    def test_update_collection(self, client: TestClient, sample_collection_data):
        """PUT /collections/{id} updates name and description of an existing collection.

        Args:
            client: TestClient instance for making API requests.
            sample_collection_data: Fixture providing base collection creation data.
        """
        create_response = client.post("/collections", json=sample_collection_data)
        collection_id = create_response.json()["id"]

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
        """PUT /collections/{id} with an empty name must be rejected with 400.

        Args:
            client: TestClient instance for making API requests.
            sample_collection_data: Fixture providing base collection creation data.
        """
        create_response = client.post("/collections", json=sample_collection_data)
        collection_id = create_response.json()["id"]

        response = client.put(f"/collections/{collection_id}", json={"name": ""})
        assert response.status_code == 400

    def test_update_collection_not_found(self, client: TestClient):
        """PUT /collections/{id} on a non-existent ID must return 404.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.put("/collections/nonexistent-id", json={"name": "New Name"})
        assert response.status_code == 404

    def test_patch_collection_partial_update(self, client: TestClient, sample_collection_data):
        """PATCH /collections/{id} updates only the supplied fields leaving others intact.

        Args:
            client: TestClient instance for making API requests.
            sample_collection_data: Fixture providing base collection creation data.
        """
        create_response = client.post("/collections", json=sample_collection_data)
        collection_id = create_response.json()["id"]
        original_data = create_response.json()

        partial_update_data = {
            "name": "Partially Updated Name"
        }

        response = client.patch(f"/collections/{collection_id}", json=partial_update_data)
        assert response.status_code == 200
        updated_data = response.json()

        assert updated_data["name"] == partial_update_data["name"]
        assert updated_data["description"] == original_data["description"]

    def test_patch_collection_non_existent(self, client: TestClient):
        """PATCH /collections/{id} on a non-existent ID must return 404.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.patch("/collections/nonexistent-id", json={"name": "New Name"})
        assert response.status_code == 404

    def test_patch_collection_empty_payload(self, client: TestClient, sample_collection_data):
        """PATCH /collections/{id} with an empty payload leaves the collection unchanged.

        Args:
            client: TestClient instance for making API requests.
            sample_collection_data: Fixture providing base collection creation data.
        """
        create_response = client.post("/collections", json=sample_collection_data)
        collection_id = create_response.json()["id"]
        original_data = create_response.json()

        response = client.patch(f"/collections/{collection_id}", json={})
        assert response.status_code == 200
        unchanged_data = response.json()

        assert unchanged_data == original_data

    def test_delete_collection_nonexistent(self, client: TestClient):
        """Deleting a non-existent collection must return 404.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.delete("/collections/nonexistent-id")
        assert response.status_code == 404

    def test_delete_collection_twice(self, client: TestClient, sample_collection_data):
        """Deleting a collection a second time must return 404 after the first deletion succeeds.

        Args:
            client: TestClient instance for making API requests.
            sample_collection_data: Fixture providing base collection creation data.
        """
        col_response = client.post("/collections", json=sample_collection_data)
        collection_id = col_response.json()["id"]

        response1 = client.delete(f"/collections/{collection_id}")
        assert response1.status_code == 204

        response2 = client.delete(f"/collections/{collection_id}")
        assert response2.status_code == 404

    def test_delete_collection_also_deletes_prompts(self, client: TestClient, sample_collection_data, sample_prompt_data):
        """Deleting a collection must also delete all prompts that belong to it.

        Args:
            client: TestClient instance for API requests.
            sample_collection_data: Data used to create a test collection.
            sample_prompt_data: Data used to create a test prompt.
        """
        col_response = client.post("/collections", json=sample_collection_data)
        collection_id = col_response.json()["id"]

        prompt_data = {**sample_prompt_data, "collection_id": collection_id}
        client.post("/prompts", json=prompt_data)

        client.delete(f"/collections/{collection_id}")

        response = client.get("/prompts")
        assert response.json()["prompts"] == []

    def test_collection_response_format(self, client: TestClient, sample_collection_data):
        """GET /collections/{id} response must contain all required and optional fields.

        Args:
            client: TestClient instance for making API requests.
            sample_collection_data: Fixture providing base collection creation data.
        """
        create_response = client.post("/collections", json=sample_collection_data)
        collection_id = create_response.json()["id"]

        get_response = client.get(f"/collections/{collection_id}")
        data = get_response.json()

        required_fields = ["id", "name", "created_at"]
        for field in required_fields:
            assert field in data

        optional_fields = ["description"]
        for field in optional_fields:
            assert field in data

    def test_collection_validation_consistency(self, client: TestClient):
        """Validation rules for collection name are consistently enforced across requests.

        Args:
            client: TestClient instance for making API requests.
        """
        response1 = client.post("/collections", json={"name": ""})
        assert response1.status_code == 400

        response2 = client.post("/collections", json={"name": "A" * 101})
        assert response2.status_code == 400

    def test_put_collection_preserves_created_at(self, client: TestClient, sample_collection_data):
        """PUT /collections/{id} must not change the original created_at timestamp.

        Args:
            client: TestClient instance for making API requests.
            sample_collection_data: Fixture providing base collection creation data.
        """
        create_resp = client.post("/collections", json=sample_collection_data)
        collection_id = create_resp.json()["id"]
        original_created_at = create_resp.json()["created_at"]

        put_resp = client.put(
            f"/collections/{collection_id}",
            json={"name": "Renamed Collection", "description": "New desc"}
        )
        assert put_resp.status_code == 200
        assert put_resp.json()["created_at"] == original_created_at

    def test_patch_collection_preserves_created_at(self, client: TestClient, sample_collection_data):
        """PATCH /collections/{id} must not change the original created_at timestamp.

        Args:
            client: TestClient instance for making API requests.
            sample_collection_data: Fixture providing base collection creation data.
        """
        create_resp = client.post("/collections", json=sample_collection_data)
        collection_id = create_resp.json()["id"]
        original_created_at = create_resp.json()["created_at"]

        patch_resp = client.patch(f"/collections/{collection_id}", json={"name": "Patched Name"})
        assert patch_resp.status_code == 200
        assert patch_resp.json()["created_at"] == original_created_at

    def test_put_collection_updates_existing_in_place(self, client: TestClient, sample_collection_data):
        """PUT /collections/{id} must not create a duplicate — total count stays the same.

        Args:
            client: TestClient instance for making API requests.
            sample_collection_data: Fixture providing base collection creation data.
        """
        client.post("/collections", json=sample_collection_data)
        collections_before = client.get("/collections").json()
        count_before = collections_before["total"]
        collection_id = collections_before["collections"][0]["id"]

        client.put(f"/collections/{collection_id}", json={"name": "In-place Update"})

        collections_after = client.get("/collections").json()
        assert collections_after["total"] == count_before

    def test_get_collection_response_includes_prompt_ids(self, client: TestClient, sample_collection_data):
        """GET /collections/{id} response must include a prompt_ids list.

        Note:
            This is a known failing test — the API does not currently return
            prompt_ids in the collection response body.

        Args:
            client: TestClient instance for making API requests.
            sample_collection_data: Fixture providing base collection creation data.
        """
        create_resp = client.post("/collections", json=sample_collection_data)
        collection_id = create_resp.json()["id"]

        resp = client.get(f"/collections/{collection_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "prompt_ids" in data
        assert isinstance(data["prompt_ids"], list)

    def test_get_collections_list_each_has_prompt_ids(self, client: TestClient, sample_collection_data):
        """GET /collections must include prompt_ids on every collection in the list.

        Note:
            This is a known failing test — the API does not currently return
            prompt_ids in the collection list response.

        Args:
            client: TestClient instance for making API requests.
            sample_collection_data: Fixture providing base collection creation data.
        """
        client.post("/collections", json=sample_collection_data)
        client.post("/collections", json={"name": "Second Collection"})

        resp = client.get("/collections")
        assert resp.status_code == 200
        for collection in resp.json()["collections"]:
            assert "prompt_ids" in collection
            assert isinstance(collection["prompt_ids"], list)

    def test_prompt_ids_updates_when_prompt_added_to_collection(
        self, client: TestClient, sample_collection_data, sample_prompt_data
    ):
        """prompt_ids list should grow when a prompt is assigned to the collection.

        Args:
            client: TestClient instance for making API requests.
            sample_collection_data: Fixture providing base collection creation data.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        col_resp = client.post("/collections", json=sample_collection_data)
        collection_id = col_resp.json()["id"]

        resp = client.get(f"/collections/{collection_id}")
        assert resp.json()["prompt_ids"] == []

        prompt_data = {**sample_prompt_data, "collection_id": collection_id}
        prompt_resp = client.post("/prompts", json=prompt_data)
        prompt_id = prompt_resp.json()["id"]

        resp = client.get(f"/collections/{collection_id}")
        assert prompt_id in resp.json()["prompt_ids"]
        assert len(resp.json()["prompt_ids"]) == 1

    def test_prompt_ids_updates_when_prompt_removed_from_collection(
        self, client: TestClient, sample_collection_data, sample_prompt_data
    ):
        """prompt_ids list should shrink when an associated prompt is deleted.

        Args:
            client: TestClient instance for making API requests.
            sample_collection_data: Fixture providing base collection creation data.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        col_resp = client.post("/collections", json=sample_collection_data)
        collection_id = col_resp.json()["id"]

        prompt_data = {**sample_prompt_data, "collection_id": collection_id}
        prompt_resp = client.post("/prompts", json=prompt_data)
        prompt_id = prompt_resp.json()["id"]

        resp = client.get(f"/collections/{collection_id}")
        assert prompt_id in resp.json()["prompt_ids"]

        client.delete(f"/prompts/{prompt_id}")

        resp = client.get(f"/collections/{collection_id}")
        assert resp.json()["prompt_ids"] == []

    def test_delete_collection_removes_all_10_associated_prompts(
        self, client: TestClient, sample_collection_data, sample_prompt_data
    ):
        """Deleting a collection with 10 prompts must remove every one of them.

        Args:
            client: TestClient instance for making API requests.
            sample_collection_data: Fixture providing base collection creation data.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        col_resp = client.post("/collections", json=sample_collection_data)
        collection_id = col_resp.json()["id"]

        for i in range(10):
            prompt_data = {
                **sample_prompt_data,
                "title": f"Cascade Prompt {i}",
                "collection_id": collection_id,
            }
            client.post("/prompts", json=prompt_data)

        before = client.get("/prompts").json()
        assert before["total"] == 10

        del_resp = client.delete(f"/collections/{collection_id}")
        assert del_resp.status_code == 204

        after = client.get("/prompts").json()
        assert after["total"] == 0
        assert after["prompts"] == []

    def test_delete_collection_prompt_count_excludes_other_collections(
        self, client: TestClient, sample_collection_data, sample_prompt_data
    ):
        """After deleting one collection only that collection's prompts are removed.

        Args:
            client: TestClient instance for making API requests.
            sample_collection_data: Fixture providing base collection creation data.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        col1_resp = client.post("/collections", json=sample_collection_data)
        col1_id = col1_resp.json()["id"]

        col2_resp = client.post("/collections", json={"name": "Keeper Collection"})
        col2_id = col2_resp.json()["id"]

        for i in range(3):
            client.post("/prompts", json={
                **sample_prompt_data,
                "title": f"Col1 Prompt {i}",
                "collection_id": col1_id,
            })
        for i in range(2):
            client.post("/prompts", json={
                **sample_prompt_data,
                "title": f"Col2 Prompt {i}",
                "collection_id": col2_id,
            })

        client.delete(f"/collections/{col1_id}")

        remaining = client.get("/prompts").json()
        assert remaining["total"] == 2
        assert all(p["collection_id"] == col2_id for p in remaining["prompts"])

    def test_patch_collection_with_empty_string_name_normalized(
        self, client: TestClient, sample_collection_data
    ):
        """PATCH /collections/{id} with name="" must normalize to None and leave name unchanged.

        CollectionUpdateOptional.check_empty_values converts "" to None before validation,
        so the existing name is preserved.

        Args:
            client: TestClient instance for making API requests.
            sample_collection_data: Fixture providing base collection creation data.
        """
        create_resp = client.post("/collections", json=sample_collection_data)
        collection_id = create_resp.json()["id"]
        original_name = create_resp.json()["name"]

        patch_resp = client.patch(f"/collections/{collection_id}", json={"name": ""})
        assert patch_resp.status_code == 200
        assert patch_resp.json()["name"] == original_name
