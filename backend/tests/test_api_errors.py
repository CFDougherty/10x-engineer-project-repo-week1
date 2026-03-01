"""Error handling tests for PromptLab API.

These tests verify error handling and response formats.
"""

import pytest
from fastapi.testclient import TestClient

class TestDetailedErrorCases:
    """Detailed error-case coverage for prompt and collection endpoints."""

    def test_invalid_uuid_format(self, client: TestClient):
        """A prompt lookup with a non-UUID path segment must return 404.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.get("/prompts/invalid-uuid-format")
        assert response.status_code == 404

    def test_malformed_json(self, client: TestClient):
        """A POST body containing malformed JSON must return 400.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.post("/prompts", content="{title: Test}", headers={"Content-Type": "application/json"})
        assert response.status_code == 400

    def test_sql_injection_attempt(self, client: TestClient):
        """SQL injection patterns in the title field must be rejected with 400.

        Args:
            client: TestClient instance for making API requests.
        """
        malicious_data = {
            "title": "'; DROP TABLE prompts; --",
            "content": "malicious content"
        }
        response = client.post("/prompts", json=malicious_data)
        assert response.status_code == 400

    def test_xss_attempt(self, client: TestClient):
        """XSS payloads must be sanitized before storage and must not appear in the response.

        Args:
            client: TestClient instance for making API requests.
        """
        xss_data = {
            "title": "<script>alert('xss')</script>",
            "content": "<img src=x onerror=alert(1)>"
        }
        response = client.post("/prompts", json=xss_data)
        assert response.status_code == 201
        data = response.json()
        assert "<script>" not in data["title"]
        assert "<img" not in data["content"]

class TestAPIResponseFormat:
    """Tests for API response format consistency."""

    def test_error_response_format(self, client: TestClient):
        """Error responses for 404 and 400 status codes must contain a string 'detail' field.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.get("/prompts/nonexistent-id")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

        response = client.post("/prompts", json={"title": "", "content": "Content"})
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_list_response_format(self, client: TestClient):
        """List endpoints for prompts and collections must return a 'total' count and typed list.

        Args:
            client: TestClient instance for making API requests.
        """
        prompts_response = client.get("/prompts")
        prompts_data = prompts_response.json()
        assert "prompts" in prompts_data
        assert "total" in prompts_data
        assert isinstance(prompts_data["prompts"], list)
        assert isinstance(prompts_data["total"], int)

        collections_response = client.get("/collections")
        collections_data = collections_response.json()
        assert "collections" in collections_data
        assert "total" in collections_data
        assert isinstance(collections_data["collections"], list)
        assert isinstance(collections_data["total"], int)

    def test_response_headers(self, client: TestClient):
        """GET /prompts must respond with an application/json Content-Type header.

        Args:
            client: TestClient instance for making API requests.
        """
        response = client.get("/prompts")
        assert "Content-Type" in response.headers
        assert "application/json" in response.headers["Content-Type"]

    def test_response_timestamps_format(self, client: TestClient):
        """Timestamp fields on a created prompt must be ISO 8601 strings or numeric timestamps.

        Args:
            client: TestClient instance for making API requests.
        """
        prompt_data = {"title": "Test", "content": "Test"}
        response = client.post("/prompts", json=prompt_data)
        data = response.json()

        assert "created_at" in data
        assert "updated_at" in data
        try:
            from datetime import datetime
            datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        except ValueError:
            assert isinstance(data["created_at"], (int, float))

    def test_id_format(self, client: TestClient):
        """The 'id' field on a created prompt must be a string or integer.

        Args:
            client: TestClient instance for making API requests.
        """
        prompt_data = {"title": "Test", "content": "Test"}
        response = client.post("/prompts", json=prompt_data)
        data = response.json()

        assert "id" in data
        assert isinstance(data["id"], str) or isinstance(data["id"], int)


class TestHTTPMethodBehavior:
    """HTTP method and API contract edge cases."""

    def test_get_nonexistent_prompt_returns_404_not_500(self, client: TestClient):
        """GET /prompts/{id} for an unknown ID must return 404, not an unhandled 500.

        Args:
            client: TestClient instance for making API requests.
        """
        resp = client.get("/prompts/completely-made-up-id")
        assert resp.status_code == 404

    def test_get_nonexistent_collection_returns_404_not_500(self, client: TestClient):
        """GET /collections/{id} for an unknown ID must return 404, not an unhandled 500.

        Args:
            client: TestClient instance for making API requests.
        """
        resp = client.get("/collections/completely-made-up-id")
        assert resp.status_code == 404

    def test_promote_version_on_nonexistent_prompt_returns_404(self, client: TestClient):
        """POST /prompts/{id}/versions/{v}/promote for a missing prompt must return 404.

        Args:
            client: TestClient instance for making API requests.
        """
        resp = client.post("/prompts/nonexistent/versions/1/promote")
        assert resp.status_code == 404

    def test_get_versions_on_nonexistent_prompt_returns_404(self, client: TestClient):
        """GET /prompts/{id}/versions for a missing prompt must return 404.

        Args:
            client: TestClient instance for making API requests.
        """
        resp = client.get("/prompts/nonexistent/versions")
        assert resp.status_code == 404

    def test_html_xss_sanitized_in_response(self, client: TestClient):
        """XSS payloads in input must be HTML-escaped in the stored and returned data.

        Note:
            Verifies that HTML entities such as '&lt;' appear in the response title,
            confirming active sanitization rather than simple rejection.

        Args:
            client: TestClient instance for making API requests.
        """
        resp = client.post("/prompts", json={
            "title": "<script>alert('xss')</script>",
            "content": "<img src=x onerror=alert(1)>",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "<script>" not in data["title"]
        assert "<img" not in data["content"]
        assert "&lt;" in data["title"]

    def test_sql_injection_in_content_is_rejected(self, client: TestClient):
        """SQL injection patterns in the title must be rejected by the validator with 400.

        Args:
            client: TestClient instance for making API requests.
        """
        resp = client.post("/prompts", json={
            "title": "'; DROP TABLE prompts; --",
            "content": "malicious",
        })
        assert resp.status_code == 400
