"""Health endpoint tests for PromptLab API.

These tests verify the health check endpoint works correctly.
"""

import pytest
from fastapi.testclient import TestClient
from app import __version__

class TestHealth:
    """Tests for health endpoint."""

    def test_health_check(self, client: TestClient):
        """
        Test the health check endpoint to ensure it returns a valid response.

        Args:
            client: TestClient used to make the request.

        """
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_health_response_format(self, client: TestClient):
        """Test that health endpoint returns consistent response format."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert isinstance(data["status"], str)
        assert isinstance(data["version"], str)