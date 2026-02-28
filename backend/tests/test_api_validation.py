"""Validation tests for PromptLab API.

These tests verify data validation edge cases.
"""

import pytest
from fastapi.testclient import TestClient

class TestDataValidation:
    """Tests for data validation edge cases"""

    def test_title_whitespace_only(self, client: TestClient):
        """Test title with only whitespace"""
        response = client.post("/prompts", json={
            "title": "   \t\n",
            "content": "Content"
        })
        assert response.status_code == 400

    def test_content_whitespace_only(self, client: TestClient):
        """Test content with only whitespace"""
        response = client.post("/prompts", json={
            "title": "Title",
            "content": "   \t\n"
        })
        assert response.status_code == 400

    def test_title_exact_max_length(self, client: TestClient):
        """Test title with exactly maximum length"""
        exact_max_title = "A" * 200
        response = client.post("/prompts", json={
            "title": exact_max_title,
            "content": "Content"
        })
        assert response.status_code == 201

    def test_description_exact_max_length(self, client: TestClient):
        """Test description with exactly maximum length"""
        exact_max_desc = "A" * 500
        response = client.post("/prompts", json={
            "title": "Title",
            "content": "Content",
            "description": exact_max_desc
        })
        assert response.status_code == 201

    def test_collection_name_exact_max_length(self, client: TestClient):
        """Test collection name with exactly maximum length"""
        exact_max_name = "A" * 100
        response = client.post("/collections", json={
            "name": exact_max_name
        })
        assert response.status_code == 201

class TestAPIContract:
    """Tests to verify API contract consistency"""

    def test_prompt_response_format(self, client: TestClient, sample_prompt_data):
        """Test that prompt responses have consistent format."""
        # Create prompt
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]

        # Get prompt
        get_response = client.get(f"/prompts/{prompt_id}")
        data = get_response.json()

        # Verify required fields
        required_fields = ["id", "title", "content", "created_at", "updated_at"]
        for field in required_fields:
            assert field in data

        # Verify optional fields
        optional_fields = ["description", "collection_id"]
        for field in optional_fields:
            assert field in data