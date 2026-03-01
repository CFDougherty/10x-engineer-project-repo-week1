"""Validation tests for PromptLab API.

These tests verify data validation edge cases.
"""

import pytest
from fastapi.testclient import TestClient

class TestDataValidation:
    """Data validation edge cases for prompt and collection creation endpoints."""

    def test_title_whitespace_only(self, client: TestClient):
        """A prompt title composed entirely of whitespace characters must be rejected with 400.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.post("/prompts", json={
            "title": "   \t\n",
            "content": "Content"
        })
        assert response.status_code == 400

    def test_content_whitespace_only(self, client: TestClient):
        """A prompt content field composed entirely of whitespace characters must be rejected with 400.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.post("/prompts", json={
            "title": "Title",
            "content": "   \t\n"
        })
        assert response.status_code == 400

    def test_title_exact_max_length(self, client: TestClient):
        """A prompt title at exactly the maximum allowed length must be accepted with 201.

        Args:
            client: TestClient instance for making API requests.
        """
        exact_max_title = "A" * 200
        response = client.post("/prompts", json={
            "title": exact_max_title,
            "content": "Content"
        })
        assert response.status_code == 201

    def test_description_exact_max_length(self, client: TestClient):
        """A prompt description at exactly the maximum allowed length must be accepted with 201.

        Args:
            client: TestClient instance for making API requests.
        """
        exact_max_desc = "A" * 500
        response = client.post("/prompts", json={
            "title": "Title",
            "content": "Content",
            "description": exact_max_desc
        })
        assert response.status_code == 201

    def test_collection_name_exact_max_length(self, client: TestClient):
        """A collection name at exactly the maximum allowed length must be accepted with 201.

        Args:
            client: TestClient instance for making API requests.
        """
        exact_max_name = "A" * 100
        response = client.post("/collections", json={
            "name": exact_max_name
        })
        assert response.status_code == 201

    def test_create_collection_whitespace_only_name_returns_400(self, client: TestClient):
        """A collection name composed entirely of spaces must be rejected with 400.

        CollectionBase does not strip whitespace, so "   " passes min_length=1 but
        validate_non_whitespace_name catches it and raises ValueError.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.post("/collections", json={"name": "   "})
        assert response.status_code == 400

class TestAPIContract:
    """API contract consistency tests for prompt and collection endpoints."""

    def test_prompt_response_format(self, client: TestClient, sample_prompt_data):
        """A retrieved prompt must include all required fields and the optional standard fields.

        Args:
            client: TestClient instance for making API requests.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]

        get_response = client.get(f"/prompts/{prompt_id}")
        data = get_response.json()

        required_fields = ["id", "title", "content", "created_at", "updated_at"]
        for field in required_fields:
            assert field in data

        optional_fields = ["description", "collection_id"]
        for field in optional_fields:
            assert field in data

    def test_content_type_enforcement_only_applies_to_post_prompts(
        self, client: TestClient, sample_prompt_data
    ):
        """Content-type middleware only guards POST /prompts — PUT and PATCH must still work.

        Note:
            TestClient defaults to application/json for json= calls, so this test confirms
            PUT and PATCH are not blocked by any content-type middleware that targets only
            the POST /prompts route.

        Args:
            client: TestClient instance for making API requests.
            sample_prompt_data: Fixture providing base prompt creation data.
        """
        create_resp = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_resp.json()["id"]

        put_resp = client.put(
            f"/prompts/{prompt_id}",
            json={"title": "Updated", "content": "Updated content"},
        )
        assert put_resp.status_code == 200

        patch_resp = client.patch(
            f"/prompts/{prompt_id}",
            json={"title": "Patched"},
        )
        assert patch_resp.status_code == 200

    def test_post_prompts_with_wrong_content_type_returns_415(self, client: TestClient):
        """POST /prompts with a non-JSON content type must return 415 Unsupported Media Type.

        Args:
            client: TestClient instance for making API requests.
        """
        resp = client.post(
            "/prompts",
            content='{"title": "Test", "content": "Content"}',
            headers={"Content-Type": "text/plain"},
        )
        assert resp.status_code == 415

    def test_all_error_responses_have_detail_field(self, client: TestClient):
        """Every 4xx error response must contain a 'detail' key for consistent error messages.

        Args:
            client: TestClient instance for making API requests.
        """
        cases = [
            client.get("/prompts/nonexistent-id"),
            client.post("/prompts", json={"title": "", "content": "x"}),
            client.get("/collections/nonexistent-id"),
        ]
        for resp in cases:
            assert resp.status_code >= 400
            data = resp.json()
            assert "detail" in data, f"Missing 'detail' in {resp.status_code} response: {data}"

    def test_api_create_prompt_with_9_char_content_succeeds(self, client: TestClient):
        """Model allows content as short as 1 char — 9 chars must succeed at API level.

        Note:
            Documents that validate_prompt_content() in utils.py (which enforces a 10-character
            minimum after stripping) is NOT called by the API endpoints. Only Pydantic model
            validators apply, so a 9-character content string must be accepted with 201.

        Args:
            client: TestClient instance for making API requests.
        """
        resp = client.post("/prompts", json={"title": "Test", "content": "123456789"})
        assert resp.status_code == 201

    def test_delete_nonexistent_prompt_returns_404(self, client: TestClient):
        """DELETE /prompts/{id} for a non-existent ID must return 404, not 204.

        Args:
            client: TestClient instance for making API requests.
        """
        resp = client.delete("/prompts/does-not-exist")
        assert resp.status_code == 404

    def test_delete_nonexistent_collection_returns_404(self, client: TestClient):
        """DELETE /collections/{id} for a non-existent ID must return 404, not 204.

        Args:
            client: TestClient instance for making API requests.
        """
        resp = client.delete("/collections/does-not-exist")
        assert resp.status_code == 404
