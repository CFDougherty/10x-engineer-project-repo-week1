"""Prompt endpoint tests for PromptLab API.

These tests verify the prompt CRUD endpoints work correctly.
"""

import time
from datetime import datetime
import pytest
from fastapi.testclient import TestClient

class TestPrompts:
    """Tests for prompt CRUD endpoints including create, read, update, delete, list, and patch operations."""

    def test_create_prompt(self, client: TestClient, sample_prompt_data):
        """A prompt is created successfully and returned with generated id and created_at fields.

        Args:
            client: TestClient instance for making API requests.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        response = client.post("/prompts", json=sample_prompt_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_prompt_data["title"]
        assert data["content"] == sample_prompt_data["content"]
        assert "id" in data
        assert "created_at" in data

    def test_create_prompt_with_empty_strings(self, client: TestClient):
        """Creating a prompt with empty title and content is rejected with 400.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.post("/prompts", json={"title": "", "content": ""})
        assert response.status_code == 400

    def test_create_prompt_with_very_long_strings(self, client: TestClient):
        """Creating a prompt with strings exceeding field length limits is rejected with 400.

        Note:
            The title field has a max_length of 200, so a 10000-character string must be
            rejected by Pydantic validation.

        Args:
            client: TestClient instance for making API requests.
        """
        long_string = "A" * 10000
        response = client.post("/prompts", json={"title": long_string, "content": long_string})
        assert response.status_code == 400

    def test_create_prompt_with_special_characters(self, client: TestClient):
        """A prompt containing special characters, emoji, HTML, and Unicode is accepted.

        Args:
            client: TestClient instance for making API requests.
        """
        special_data = {
            "title": "Test with émojis 🎉 and <script>alert('xss')</script>",
            "content": "Special chars: \n\t\r, quotes '\"",
            "description": "Unicode: 日本語, 中文, 한국어"
        }
        response = client.post("/prompts", json=special_data)
        assert response.status_code == 201

    def test_create_prompt_missing_required_field(self, client: TestClient):
        """Creating a prompt without a title is rejected with 400.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.post("/prompts", json={"content": "Some content"})
        assert response.status_code == 400

    def test_create_prompt_with_null_values(self, client: TestClient):
        """Creating a prompt with null values for required fields is rejected with 400.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.post("/prompts", json={"title": None, "content": None})
        assert response.status_code == 400

    def test_create_prompt_with_invalid_collection_id(self, client: TestClient):
        """Creating a prompt with a non-existent collection ID is rejected with 400.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.post("/prompts", json={
            "title": "Test",
            "content": "Content",
            "collection_id": "invalid-collection-id"
        })
        assert response.status_code == 400

    def test_create_prompt_with_title_too_long(self, client: TestClient):
        """Creating a prompt with a title exceeding the 200-character maximum is rejected with 400.

        Args:
            client: TestClient instance for making API requests.
        """
        long_title = "A" * 201
        response = client.post("/prompts", json={
            "title": long_title,
            "content": "Content"
        })
        assert response.status_code == 400

    def test_create_prompt_with_description_too_long(self, client: TestClient):
        """Creating a prompt with a description exceeding the 500-character maximum is rejected with 400.

        Args:
            client: TestClient instance for making API requests.
        """
        long_description = "A" * 501
        response = client.post("/prompts", json={
            "title": "Test",
            "content": "Content",
            "description": long_description
        })
        assert response.status_code == 400

    def test_create_prompt_with_whitespace_only_strings(self, client: TestClient):
        """Creating a prompt with whitespace-only title and content is rejected with 400.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.post("/prompts", json={
            "title": "   ",
            "content": "   "
        })
        assert response.status_code == 400

    def test_list_prompts_empty(self, client: TestClient):
        """GET /prompts returns an empty list and zero total when no prompts exist.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.get("/prompts")
        assert response.status_code == 200
        data = response.json()
        assert data["prompts"] == []
        assert data["total"] == 0

    def test_list_prompts_with_data(self, client: TestClient, sample_prompt_data):
        """GET /prompts returns the created prompt and a total of 1 after one prompt is added.

        Args:
            client: TestClient instance for making API requests.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        client.post("/prompts", json=sample_prompt_data)

        response = client.get("/prompts")
        assert response.status_code == 200
        data = response.json()
        assert len(data["prompts"]) == 1
        assert data["total"] == 1

    def test_list_prompts_with_sorting(self, client: TestClient):
        """Prompts are returned in ascending alphabetical order when sort_by=title is used.

        Args:
            client: TestClient instance for making API requests.
        """
        prompt1 = {"title": "Zebra", "content": "Content for Zebra"}
        prompt2 = {"title": "Apple", "content": "Content for Apple"}

        client.post("/prompts", json=prompt1)
        time.sleep(0.1)
        client.post("/prompts", json=prompt2)

        response = client.get("/prompts?sort_by=title")
        prompts = response.json()["prompts"]
        assert prompts[0]["title"] == "Apple"
        assert prompts[1]["title"] == "Zebra"

    def test_list_prompts_with_filtering(self, client: TestClient):
        """Only prompts matching the search term are returned when search parameter is provided.

        Args:
            client: TestClient instance for making API requests.
        """
        prompt1 = {"title": "Apple", "content": "Fruit content"}
        prompt2 = {"title": "Banana", "content": "Another fruit"}

        client.post("/prompts", json=prompt1)
        time.sleep(0.1)
        client.post("/prompts", json=prompt2)

        response = client.get("/prompts?search=Apple")
        prompts = response.json()["prompts"]
        assert len(prompts) == 1
        assert prompts[0]["title"] == "Apple"

    def test_list_prompts_with_pagination(self, client: TestClient):
        """Pagination returns the correct page size and accurate total count.

        Args:
            client: TestClient instance for making API requests.
        """
        for i in range(5):
            client.post("/prompts", json={"title": f"Prompt {i}", "content": f"Content {i}"})

        response = client.get("/prompts?limit=2&offset=0")
        data = response.json()
        assert len(data["prompts"]) == 2
        assert data["total"] >= 5

    def test_list_prompts_with_collection_filter(self, client: TestClient):
        """Only prompts belonging to the specified collection are returned when collection_id filter is used.

        Args:
            client: TestClient instance for making API requests.
        """
        collection_response = client.post("/collections", json={"name": "Test Collection"})
        collection_id = collection_response.json()["id"]

        prompt1 = {"title": "Prompt 1", "content": "Content 1", "collection_id": collection_id}
        prompt2 = {"title": "Prompt 2", "content": "Content 2"}

        client.post("/prompts", json=prompt1)
        client.post("/prompts", json=prompt2)

        response = client.get(f"/prompts?collection_id={collection_id}")
        prompts = response.json()["prompts"]
        assert len(prompts) == 1
        assert prompts[0]["collection_id"] == collection_id

    def test_list_prompts_with_search(self, client: TestClient):
        """Only the prompt whose title matches the search term is returned.

        Args:
            client: TestClient instance for making API requests.
        """
        prompt1 = {"title": "Python", "content": "Python programming language"}
        prompt2 = {"title": "JavaScript", "content": "JavaScript programming language"}

        client.post("/prompts", json=prompt1)
        client.post("/prompts", json=prompt2)

        response = client.get("/prompts?search=Python")
        prompts = response.json()["prompts"]
        assert len(prompts) == 1
        assert prompts[0]["title"] == "Python"

    def test_list_prompts_with_combined_filters(self, client: TestClient):
        """Combining collection_id and search filters returns only the matching intersection.

        Args:
            client: TestClient instance for making API requests.
        """
        collection_response = client.post("/collections", json={"name": "Test Collection"})
        collection_id = collection_response.json()["id"]

        prompt1 = {"title": "Python Search", "content": "Python programming language", "collection_id": collection_id}
        prompt2 = {"title": "JavaScript Search", "content": "JavaScript programming language", "collection_id": collection_id}
        prompt3 = {"title": "Python Other", "content": "Python other content"}

        client.post("/prompts", json=prompt1)
        client.post("/prompts", json=prompt2)
        client.post("/prompts", json=prompt3)

        response = client.get(f"/prompts?collection_id={collection_id}&search=Python")
        prompts = response.json()["prompts"]
        assert len(prompts) == 1
        assert prompts[0]["title"] == "Python Search"
        assert prompts[0]["collection_id"] == collection_id

    def test_get_prompt_success(self, client: TestClient, sample_prompt_data):
        """GET /prompts/{id} returns the prompt with the correct id after creation.

        Args:
            client: TestClient instance for making API requests.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]

        response = client.get(f"/prompts/{prompt_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == prompt_id

    def test_get_prompt_not_found(self, client: TestClient):
        """GET /prompts/{id} returns 404 when the prompt does not exist.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.get("/prompts/nonexistent-id")
        assert response.status_code == 404

    def test_get_prompt_with_special_id(self, client: TestClient):
        """GET /prompts/{id} with special characters in the path returns 404.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.get("/prompts/!@#$%^&*()_+-=[]{}|;:',.<>?`~\\")
        assert response.status_code == 404

    def test_delete_prompt(self, client: TestClient, sample_prompt_data):
        """DELETE /prompts/{id} removes the prompt so subsequent GET returns 404.

        Args:
            client: TestClient instance for making API requests.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]

        response = client.delete(f"/prompts/{prompt_id}")
        assert response.status_code == 204

        get_response = client.get(f"/prompts/{prompt_id}")
        assert get_response.status_code == 404

    def test_delete_prompt_twice(self, client: TestClient, sample_prompt_data):
        """Attempting to delete an already-deleted prompt returns 404 on the second attempt.

        Args:
            client: TestClient instance for making API requests.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]

        response1 = client.delete(f"/prompts/{prompt_id}")
        assert response1.status_code == 204

        response2 = client.delete(f"/prompts/{prompt_id}")
        assert response2.status_code == 404

    def test_update_prompt(self, client: TestClient, sample_prompt_data):
        """PUT /prompts/{id} updates the prompt fields and advances the updated_at timestamp.

        A small delay is introduced before the update to guarantee the updated_at value
        differs from the original, since timestamps may have limited precision.

        Args:
            client: TestClient instance for making API requests.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]
        original_updated_at = create_response.json()["updated_at"]

        updated_data = {
            "title": "Updated Title",
            "content": "Updated content for the prompt",
            "description": "Updated description"
        }

        time.sleep(0.1)

        response = client.put(f"/prompts/{prompt_id}", json=updated_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

        assert data["updated_at"] != original_updated_at

    def test_update_prompt_with_invalid_data(self, client: TestClient, sample_prompt_data):
        """PUT /prompts/{id} with an empty title is rejected with 400.

        Args:
            client: TestClient instance for making API requests.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]

        response = client.put(f"/prompts/{prompt_id}", json={"title": ""})
        assert response.status_code == 400

    def test_update_prompt_with_special_characters(self, client: TestClient, sample_prompt_data):
        """PUT /prompts/{id} accepts special characters and Unicode in all text fields.

        Args:
            client: TestClient instance for making API requests.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]

        updated_data = {
            "title": "Test <script>alert('xss')</script>",
            "content": "Special chars: \n\t\r",
            "description": "Unicode: 日本語"
        }

        response = client.put(f"/prompts/{prompt_id}", json=updated_data)
        assert response.status_code == 200

    def test_sorting_order(self, client: TestClient):
        """The most recently created prompt appears first in the default list order.

        Note:
            This test might fail due to Bug 3 if the default sort order is not newest-first.

        Args:
            client: TestClient instance for making API requests.
        """
        prompt1 = {"title": "First", "content": "First prompt content"}
        prompt2 = {"title": "Second", "content": "Second prompt content"}

        client.post("/prompts", json=prompt1)
        time.sleep(0.1)
        client.post("/prompts", json=prompt2)

        response = client.get("/prompts")
        prompts = response.json()["prompts"]

        assert prompts[0]["title"] == "Second"

    def test_concurrent_prompt_creation(self, client: TestClient):
        """Creating 10 prompts in rapid succession results in all 10 being stored.

        Args:
            client: TestClient instance for making API requests.
        """
        prompts_data = [
            {"title": f"Prompt {i}", "content": f"Content {i}"}
            for i in range(10)
        ]

        for prompt_data in prompts_data:
            response = client.post("/prompts", json=prompt_data)
            assert response.status_code == 201

        response = client.get("/prompts")
        prompts = response.json()["prompts"]
        assert len(prompts) == 10

    def test_prompt_with_all_optional_fields(self, client: TestClient):
        """A prompt created with only required fields has null values for all optional fields.

        Args:
            client: TestClient instance for making API requests.
        """
        prompt_data = {
            "title": "Minimal Prompt",
            "content": "Minimal content"
        }

        response = client.post("/prompts", json=prompt_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal Prompt"
        assert data["content"] == "Minimal content"
        assert data["description"] is None
        assert data["collection_id"] is None

    def test_prompt_with_all_fields(self, client: TestClient):
        """A prompt created with all fields, including collection_id, stores every value correctly.

        Args:
            client: TestClient instance for making API requests.
        """
        collection_response = client.post("/collections", json={"name": "Test Collection"})
        collection_id = collection_response.json()["id"]

        prompt_data = {
            "title": "Complete Prompt",
            "content": "Complete content",
            "description": "Complete description",
            "collection_id": collection_id
        }

        response = client.post("/prompts", json=prompt_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Complete Prompt"
        assert data["content"] == "Complete content"
        assert data["description"] == "Complete description"
        assert data["collection_id"] == collection_id

    def test_prompt_lifecycle(self, client: TestClient):
        """The full create-read-update-delete lifecycle completes with correct status codes.

        Args:
            client: TestClient instance for making API requests.
        """
        create_data = {"title": "Lifecycle Test", "content": "Original content"}
        create_response = client.post("/prompts", json=create_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]

        get_response = client.get(f"/prompts/{prompt_id}")
        assert get_response.status_code == 200

        update_data = {"title": "Updated Title", "content": "Updated content"}
        update_response = client.put(f"/prompts/{prompt_id}", json=update_data)
        assert update_response.status_code == 200

        delete_response = client.delete(f"/prompts/{prompt_id}")
        assert delete_response.status_code == 204

        verify_response = client.get(f"/prompts/{prompt_id}")
        assert verify_response.status_code == 404

    def test_patch_prompt_partial_update(self, client: TestClient, sample_prompt_data):
        """PATCH /prompts/{id} updates only specified fields and leaves others unchanged.

        Args:
            client: TestClient instance for making API requests.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]
        original_data = create_response.json()

        partial_update_data = {
            "title": "Partially Updated Title"
        }

        response = client.patch(f"/prompts/{prompt_id}", json=partial_update_data)
        assert response.status_code == 200
        updated_data = response.json()

        assert updated_data["title"] == partial_update_data["title"]

        assert updated_data["content"] == original_data["content"]
        assert updated_data["description"] == original_data["description"]

    def test_patch_prompt_non_existent(self, client: TestClient):
        """PATCH /prompts/{id} on a non-existent prompt returns 404.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.patch("/prompts/nonexistent-id", json={"title": "New Title"})
        assert response.status_code == 404

    def test_patch_prompt_invalid_collection(self, client: TestClient, sample_prompt_data):
        """PATCH /prompts/{id} with an invalid collection_id is rejected with 400.

        Args:
            client: TestClient instance for making API requests.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]

        response = client.patch(f"/prompts/{prompt_id}", json={"collection_id": "invalid-collection-id"})
        assert response.status_code == 400

    def test_patch_prompt_empty_payload(self, client: TestClient, sample_prompt_data):
        """PATCH /prompts/{id} with an empty payload returns the prompt unchanged.

        Args:
            client: TestClient instance for making API requests.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]
        original_data = create_response.json()

        response = client.patch(f"/prompts/{prompt_id}", json={})
        assert response.status_code == 200
        unchanged_data = response.json()

        assert unchanged_data == original_data

    def test_patch_prompt_updates_timestamp(self, client: TestClient, sample_prompt_data):
        """PATCH /prompts/{id} advances the updated_at timestamp when a field value changes.

        A small delay is introduced before the patch to guarantee the timestamp differs,
        since timestamps may have limited precision.

        Args:
            client: TestClient instance for making API requests.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]
        original_updated_at = create_response.json()["updated_at"]

        time.sleep(0.1)

        partial_update_data = {
            "title": "Updated Title"
        }

        response = client.patch(f"/prompts/{prompt_id}", json=partial_update_data)
        assert response.status_code == 200
        updated_data = response.json()

        assert updated_data["updated_at"] != original_updated_at

    def test_patch_prompt_no_changes(self, client: TestClient, sample_prompt_data):
        """PATCH /prompts/{id} with identical values does not advance the updated_at timestamp.

        Args:
            client: TestClient instance for making API requests.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]
        original_updated_at = create_response.json()["updated_at"]

        response = client.patch(f"/prompts/{prompt_id}", json=sample_prompt_data)
        assert response.status_code == 200
        updated_data = response.json()

        assert updated_data["updated_at"] == original_updated_at

    def test_prompt_data_integrity(self, client: TestClient):
        """A prompt retrieved by id contains the exact values provided at creation time.

        Args:
            client: TestClient instance for making API requests.
        """
        original_data = {
            "title": "Integrity Test",
            "content": "Original content",
            "description": "Original description"
        }

        create_response = client.post("/prompts", json=original_data)
        prompt_id = create_response.json()["id"]

        get_response = client.get(f"/prompts/{prompt_id}")
        retrieved_data = get_response.json()

        assert retrieved_data["title"] == original_data["title"]
        assert retrieved_data["content"] == original_data["content"]
        assert retrieved_data["description"] == original_data["description"]
        assert retrieved_data["id"] == prompt_id
        assert "created_at" in retrieved_data
        assert "updated_at" in retrieved_data

    def test_prompt_validation_consistency(self, client: TestClient):
        """Validation rejects empty title, empty content, and both empty independently.

        Args:
            client: TestClient instance for making API requests.
        """
        response1 = client.post("/prompts", json={"title": "", "content": "Content"})
        assert response1.status_code == 400

        response2 = client.post("/prompts", json={"title": "Title", "content": ""})
        assert response2.status_code == 400

        response3 = client.post("/prompts", json={"title": "", "content": ""})
        assert response3.status_code == 400

    def test_prompt_collection_relationship(self, client: TestClient):
        """A prompt stores the correct collection_id and appears in the collection-filtered list.

        Args:
            client: TestClient instance for making API requests.
        """
        collection_response = client.post("/collections", json={"name": "Test Collection"})
        collection_id = collection_response.json()["id"]

        prompt_data = {
            "title": "Test Prompt",
            "content": "Test content",
            "collection_id": collection_id
        }
        prompt_response = client.post("/prompts", json=prompt_data)
        prompt_id = prompt_response.json()["id"]

        get_prompt_response = client.get(f"/prompts/{prompt_id}")
        prompt = get_prompt_response.json()
        assert prompt["collection_id"] == collection_id

        list_response = client.get(f"/prompts?collection_id={collection_id}")
        prompts = list_response.json()["prompts"]
        assert len(prompts) == 1
        assert prompts[0]["id"] == prompt_id

    def test_create_prompt_with_invalid_json(self, client: TestClient):
        """Sending malformed JSON in the request body is rejected with 400.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.post("/prompts", content="invalid json", headers={"Content-Type": "application/json"})
        assert response.status_code == 400

    def test_create_prompt_with_wrong_content_type(self, client: TestClient):
        """Sending a request with Content-Type text/plain is rejected with 415.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.post("/prompts", content='{"title": "Test", "content": "Test"}', headers={"Content-Type": "text/plain"})
        assert response.status_code == 415

    def test_list_prompts_with_invalid_sort_field(self, client: TestClient):
        """An unknown sort_by parameter value is silently ignored and returns 200.

        Note:
            FastAPI does not declare sort_by as a typed enum parameter, so unrecognized
            values are passed through and the API falls back to default sort behavior.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.get("/prompts?sort_by=invalid_field")
        assert response.status_code == 200

    def test_list_prompts_with_invalid_filter(self, client: TestClient):
        """An unknown query parameter is silently ignored by FastAPI and returns 200.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.get("/prompts?invalid_param=value")
        assert response.status_code == 200

    def test_list_prompts_total_is_pre_pagination_count(self, client: TestClient, sample_prompt_data):
        """The total field reflects the full result set size, not just the current page.

        Args:
            client: TestClient instance for making API requests.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        for i in range(10):
            client.post("/prompts", json={**sample_prompt_data, "title": f"Prompt {i}"})

        resp = client.get("/prompts?limit=3&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["prompts"]) == 3
        assert data["total"] == 10

    def test_list_prompts_zero_limit_returns_empty_with_correct_total(
        self, client: TestClient, sample_prompt_data
    ):
        """limit=0 yields an empty prompts list but the correct pre-pagination total.

        Args:
            client: TestClient instance for making API requests.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        for i in range(3):
            client.post("/prompts", json={**sample_prompt_data, "title": f"Prompt {i}"})

        resp = client.get("/prompts?limit=0")
        assert resp.status_code == 200
        data = resp.json()
        assert data["prompts"] == []
        assert data["total"] == 3

    def test_list_prompts_offset_beyond_total_returns_empty_with_correct_total(
        self, client: TestClient, sample_prompt_data
    ):
        """An offset past the end of the result set returns an empty page with the real total.

        Args:
            client: TestClient instance for making API requests.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        for i in range(3):
            client.post("/prompts", json={**sample_prompt_data, "title": f"Prompt {i}"})

        resp = client.get("/prompts?offset=100")
        assert resp.status_code == 200
        data = resp.json()
        assert data["prompts"] == []
        assert data["total"] == 3

    def test_list_prompts_very_large_limit_returns_all(
        self, client: TestClient, sample_prompt_data
    ):
        """A very large limit value returns all available prompts without error.

        Args:
            client: TestClient instance for making API requests.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        for i in range(5):
            client.post("/prompts", json={**sample_prompt_data, "title": f"Prompt {i}"})

        resp = client.get("/prompts?limit=1000000")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["prompts"]) == 5

    def test_list_prompts_negative_offset_behavior(self, client: TestClient, sample_prompt_data):
        """A negative offset is either rejected with 4xx or clamped to 0; a 500 is never acceptable.

        Note:
            The API has two valid behaviors for negative offset: reject with a 4xx status code,
            or clamp the value to 0 and return results from the beginning. Either is acceptable,
            but an unhandled server error (500) is not.

        Args:
            client: TestClient instance for making API requests.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        client.post("/prompts", json=sample_prompt_data)

        resp = client.get("/prompts?offset=-1")
        assert resp.status_code in [200, 400, 422]
        if resp.status_code == 200:
            assert len(resp.json()["prompts"]) == 1

    def test_list_prompts_negative_limit_behavior(self, client: TestClient, sample_prompt_data):
        """A negative limit is either rejected with 4xx or treated as 0; a 500 is never acceptable.

        Note:
            The API has two valid behaviors for negative limit: reject with a 4xx status code,
            or treat it as 0 and return an empty list. Either is acceptable, but an unhandled
            server error (500) is not.

        Args:
            client: TestClient instance for making API requests.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        client.post("/prompts", json=sample_prompt_data)

        resp = client.get("/prompts?limit=-1")
        assert resp.status_code in [200, 400, 422]
