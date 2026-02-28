"""Integration tests for PromptLab API.

These tests verify complex workflows and interactions between endpoints.
"""

import pytest
from fastapi.testclient import TestClient

class TestIntegration:
    """Integration tests between different endpoints"""

    def test_prompt_collection_integration(self, client: TestClient):
        """Test the complete integration between prompts and collections"""
        # Create collection
        col_response = client.post("/collections", json={"name": "Integration Test"})
        collection_id = col_response.json()["id"]

        # Create prompt in collection
        prompt_response = client.post("/prompts", json={
            "title": "Integration Prompt",
            "content": "Integration content",
            "collection_id": collection_id
        })
        prompt_id = prompt_response.json()["id"]

        # Verify through collection endpoint
        col_prompts = client.get(f"/prompts?collection_id={collection_id}").json()["prompts"]
        assert len(col_prompts) == 1
        assert col_prompts[0]["id"] == prompt_id

        # Delete collection and verify prompt handling
        client.delete(f"/collections/{collection_id}")

        # After fix, prompt should either be deleted or have collection_id=None
        all_prompts = client.get("/prompts").json()["prompts"]
        if all_prompts:
            assert all_prompts[0]["collection_id"] is None

    def test_search_functionality(self, client: TestClient):
        """Test search functionality across different fields"""
        # Create test data
        test_data = [
            {"title": "Python programming", "content": "Python is great"},
            {"title": "JavaScript basics", "content": "JavaScript tutorial"},
            {"title": "Python advanced", "content": "Advanced Python concepts"}
        ]

        for data in test_data:
            client.post("/prompts", json=data)

        # Test searching in title
        response = client.get("/prompts?search=Python")
        assert len(response.json()["prompts"]) == 2

        # Test searching in content
        response = client.get("/prompts?search=great")
        assert len(response.json()["prompts"]) == 1

        # Test case sensitivity
        response = client.get("/prompts?search=python")
        assert len(response.json()["prompts"]) == 2  # Should be case insensitive