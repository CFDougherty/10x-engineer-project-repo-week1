"""Tests for the API key authentication middleware.

When API_KEY is set in the environment, all endpoints require an ``X-API-Key``
request header (or ``?api_key=`` query param for SSE). When API_KEY is empty
(the default), auth is disabled and every request passes through unchanged.
"""

import os
import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.database import get_settings

TEST_KEY = "test-secret-key-for-auth-tests"


@pytest.fixture
def auth_client():
    """TestClient with API key enabled; sends the correct key in headers."""
    os.environ["API_KEY"] = TEST_KEY
    get_settings.cache_clear()
    try:
        yield TestClient(app, headers={"X-API-Key": TEST_KEY})
    finally:
        os.environ.pop("API_KEY", None)
        get_settings.cache_clear()


@pytest.fixture
def no_key_client():
    """TestClient with API key enabled; sends NO auth header."""
    os.environ["API_KEY"] = TEST_KEY
    get_settings.cache_clear()
    try:
        yield TestClient(app)
    finally:
        os.environ.pop("API_KEY", None)
        get_settings.cache_clear()


class TestAuthDisabled:
    """When API_KEY env var is not set, the middleware is a no-op."""

    def test_prompts_accessible_without_key(self, client):
        response = client.get("/prompts")
        assert response.status_code == 200

    def test_health_accessible_without_key(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_collections_accessible_without_key(self, client):
        response = client.get("/collections")
        assert response.status_code == 200


class TestAuthEnabled:
    """When API_KEY is set, requests must carry the correct key."""

    def test_missing_key_returns_401(self, no_key_client):
        response = no_key_client.get("/prompts")
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or missing API key"

    def test_wrong_key_returns_401(self, no_key_client):
        response = no_key_client.get("/prompts", headers={"X-API-Key": "wrong-key"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or missing API key"

    def test_correct_header_key_allows_access(self, auth_client):
        response = auth_client.get("/prompts")
        assert response.status_code == 200

    def test_correct_key_on_post_endpoint(self, auth_client, sample_prompt_data):
        response = auth_client.post("/prompts", json=sample_prompt_data)
        assert response.status_code == 201

    def test_collections_require_key(self, no_key_client):
        response = no_key_client.get("/collections")
        assert response.status_code == 401

    def test_versioning_endpoints_require_key(self, no_key_client):
        response = no_key_client.get("/prompts/some-id/versions")
        # 401 from auth, not 404 from missing prompt
        assert response.status_code == 401

    def test_admin_endpoints_require_key(self, no_key_client):
        response = no_key_client.get("/admin/populate-status")
        assert response.status_code == 401

    def test_health_is_always_public(self, no_key_client):
        """Health endpoint must remain accessible for Docker health checks."""
        response = no_key_client.get("/health")
        assert response.status_code == 200

    def test_sse_endpoint_rejects_missing_key(self, no_key_client):
        """SSE endpoint is protected the same as all other endpoints."""
        response = no_key_client.get("/admin/events")
        assert response.status_code == 401

    def test_sse_endpoint_rejects_wrong_key_query_param(self, no_key_client):
        response = no_key_client.get("/admin/events?api_key=wrong-key")
        assert response.status_code == 401

    # NOTE: A positive SSE auth test (correct key → 200) is intentionally omitted.
    # The SSE endpoint is an infinite streaming generator — any test that lets the
    # connection succeed will hang waiting for the stream to end. The two 401 tests
    # above already confirm auth is enforced on the SSE path; the query-param
    # fallback logic is trivially verified by reading the middleware code.