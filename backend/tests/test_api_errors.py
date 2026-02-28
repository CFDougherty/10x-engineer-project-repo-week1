"""Error handling tests for PromptLab API.

These tests verify error handling and response formats.
"""

import pytest
from fastapi.testclient import TestClient

class TestDetailedErrorCases:
    """More detailed error case testing"""

    def test_invalid_uuid_format(self, client: TestClient):
        """Test with invalid UUID format"""
        response = client.get("/prompts/invalid-uuid-format")
        assert response.status_code == 404

    def test_malformed_json(self, client: TestClient):
        """Test with malformed JSON payload"""
        response = client.post("/prompts", data='{"title": "Test", "content": "Test"', headers={"Content-Type": "application/json"})
        assert response.status_code == 400  # Malformed JSON returns 400

    def test_sql_injection_attempt(self, client: TestClient):
        """Test SQL injection attempts are properly handled"""
        malicious_data = {
            "title": "'; DROP TABLE prompts; --",
            "content": "malicious content"
        }
        response = client.post("/prompts", json=malicious_data)
        assert response.status_code == 400  # Should be rejected

    def test_xss_attempt(self, client: TestClient):
        """Test XSS attempts are properly sanitized"""
        xss_data = {
            "title": "<script>alert('xss')</script>",
            "content": "<img src=x onerror=alert(1)>"
        }
        response = client.post("/prompts", json=xss_data)
        assert response.status_code == 201  # Should succeed but sanitize
        data = response.json()
        assert "<script>" not in data["title"]
        assert "<img" not in data["content"]

class TestAPIResponseFormat:
    """Tests for API response format consistency."""

    def test_error_response_format(self, client: TestClient):
        """Test that error responses have consistent format."""
        # Test 404 error
        response = client.get("/prompts/nonexistent-id")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

        # Test 400 error
        response = client.post("/prompts", json={"title": "", "content": "Content"})
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_list_response_format(self, client: TestClient):
        """Test that list responses have consistent format."""
        # Test prompts list
        prompts_response = client.get("/prompts")
        prompts_data = prompts_response.json()
        assert "prompts" in prompts_data
        assert "total" in prompts_data
        assert isinstance(prompts_data["prompts"], list)
        assert isinstance(prompts_data["total"], int)

        # Test collections list
        collections_response = client.get("/collections")
        collections_data = collections_response.json()
        assert "collections" in collections_data
        assert "total" in collections_data
        assert isinstance(collections_data["collections"], list)
        assert isinstance(collections_data["total"], int)

    def test_response_headers(self, client: TestClient):
        """Test that responses have required headers"""
        response = client.get("/prompts")
        assert "Content-Type" in response.headers
        assert "application/json" in response.headers["Content-Type"]

    def test_response_timestamps_format(self, client: TestClient):
        """Test that timestamp fields have consistent format"""
        prompt_data = {"title": "Test", "content": "Test"}
        response = client.post("/prompts", json=prompt_data)
        data = response.json()

        # Check created_at and updated_at format
        assert "created_at" in data
        assert "updated_at" in data
        # Should be ISO format or Unix timestamp
        try:
            from datetime import datetime
            datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        except ValueError:
            # If not ISO format, check if it's a timestamp
            assert isinstance(data["created_at"], (int, float))

    def test_id_format(self, client: TestClient):
        """Test that ID fields have consistent format"""
        prompt_data = {"title": "Test", "content": "Test"}
        response = client.post("/prompts", json=prompt_data)
        data = response.json()

        # IDs should be consistent (UUID, integer, etc.)
        assert "id" in data
        # Should be either UUID or integer
        assert isinstance(data["id"], str) or isinstance(data["id"], int)