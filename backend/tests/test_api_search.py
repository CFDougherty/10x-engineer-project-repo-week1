"""Search functionality tests for PromptLab API.

These tests verify search functionality across different fields and edge cases.
"""

import pytest
from fastapi.testclient import TestClient

class TestSearchPrompts:
    """Test for search field functionality fix.

    This test verifies that the bug where selecting 'description', 'tags', or 'collection'
    from the dropdown returns all prompt cards regardless of search query is fixed.
    """

    def test_search_by_description_field(self, client: TestClient):
        """Test searching by description field returns correct results."""
        # Create test data with different descriptions
        prompt1 = {
            "title": "Prompt 1",
            "content": "Content 1",
            "description": "This is about Python programming"
        }
        prompt2 = {
            "title": "Prompt 2",
            "content": "Content 2",
            "description": "This is about JavaScript programming"
        }
        prompt3 = {
            "title": "Prompt 3",
            "content": "Content 3",
            "description": "Another Python example"
        }

        client.post("/prompts", json=prompt1)
        client.post("/prompts", json=prompt2)
        client.post("/prompts", json=prompt3)

        # Search for "Python" in description field
        response = client.get("/prompts?search=Python&filter=description")
        prompts = response.json()["prompts"]

        # Should return only prompts with "Python" in description
        assert len(prompts) == 2
        assert all("Python" in p.get("description", "") for p in prompts)
        assert all("JavaScript" not in p.get("description", "") for p in prompts)

    def test_search_by_tags_field(self, client: TestClient):
        """Test searching by tags field returns correct results."""
        # Create test data with different tags
        prompt1 = {
            "title": "Prompt 1",
            "content": "Content 1",
            "tags": ["python", "programming", "coding"]
        }
        prompt2 = {
            "title": "Prompt 2",
            "content": "Content 2",
            "tags": ["javascript", "web", "frontend"]
        }
        prompt3 = {
            "title": "Prompt 3",
            "content": "Content 3",
            "tags": ["python", "data", "analysis"]
        }

        client.post("/prompts", json=prompt1)
        client.post("/prompts", json=prompt2)
        client.post("/prompts", json=prompt3)

        # Search for "python" in tags field
        response = client.get("/prompts?search=python&filter=tags")
        prompts = response.json()["prompts"]

        # Should return only prompts with "python" in tags
        assert len(prompts) == 2
        assert all("python" in p.get("tags", []) for p in prompts)
        assert all("javascript" not in p.get("tags", []) for p in prompts)

    def test_search_by_collection_field(self, client: TestClient):
        """Test searching by collection name field returns correct results."""
        # Create collections
        col1 = client.post("/collections", json={"name": "Python Scripts"})
        col1_id = col1.json()["id"]

        col2 = client.post("/collections", json={"name": "JavaScript Code"})
        col2_id = col2.json()["id"]

        # Create prompts in different collections
        prompt1 = {
            "title": "Prompt 1",
            "content": "Content 1",
            "collection_id": col1_id
        }
        prompt2 = {
            "title": "Prompt 2",
            "content": "Content 2",
            "collection_id": col2_id
        }
        prompt3 = {
            "title": "Prompt 3",
            "content": "Content 3",
            "collection_id": col1_id
        }

        client.post("/prompts", json=prompt1)
        client.post("/prompts", json=prompt2)
        client.post("/prompts", json=prompt3)

        # Search for "Python" in collection field
        response = client.get("/prompts?search=Python&filter=collection")
        prompts = response.json()["prompts"]

        # Should return only prompts in collections with "Python" in name
        assert len(prompts) == 2
        assert all(p.get("collection_id") == col1_id for p in prompts)
        assert all(p.get("collection_id") != col2_id for p in prompts)

    def test_search_by_title_field(self, client: TestClient):
        """Test searching by title field returns correct results."""
        # Create test data with different titles
        prompt1 = {
            "title": "Python Programming Guide",
            "content": "Content 1"
        }
        prompt2 = {
            "title": "JavaScript Basics",
            "content": "Content 2"
        }
        prompt3 = {
            "title": "Advanced Python Techniques",
            "content": "Content 3"
        }

        client.post("/prompts", json=prompt1)
        client.post("/prompts", json=prompt2)
        client.post("/prompts", json=prompt3)

        # Search for "Python" in title field
        response = client.get("/prompts?search=Python&filter=title")
        prompts = response.json()["prompts"]

        # Should return only prompts with "Python" in title
        assert len(prompts) == 2
        assert all("Python" in p.get("title", "") for p in prompts)
        assert all("JavaScript" not in p.get("title", "") for p in prompts)

    def test_search_all_fields(self, client: TestClient):
        """Test searching across all fields returns correct results."""
        # Create test data
        prompt1 = {
            "title": "Python Guide",
            "content": "About Python programming",
            "description": "Python tutorial"
        }
        prompt2 = {
            "title": "JavaScript Guide",
            "content": "About JavaScript programming",
            "description": "JavaScript tutorial"
        }

        client.post("/prompts", json=prompt1)
        client.post("/prompts", json=prompt2)

        # Search for "Guide" across all fields
        response = client.get("/prompts?search=Guide&filter=all")
        prompts = response.json()["prompts"]

        # Should return both prompts
        assert len(prompts) == 2

    def test_search_without_filter_returns_all_fields(self, client: TestClient):
        """Test that searching without filter parameter searches all fields."""
        # Create test data
        prompt1 = {
            "title": "Python Guide",
            "content": "About Python programming",
            "description": "Python tutorial"
        }
        prompt2 = {
            "title": "JavaScript Guide",
            "content": "About JavaScript programming",
            "description": "JavaScript tutorial"
        }

        client.post("/prompts", json=prompt1)
        client.post("/prompts", json=prompt2)

        # Search for "Guide" without filter parameter
        response = client.get("/prompts?search=Guide")
        prompts = response.json()["prompts"]

        # Should return both prompts (default behavior)
        assert len(prompts) == 2

    def test_empty_search_query_returns_all_prompts(self, client: TestClient):
        """Test that empty search query returns all prompts regardless of filter."""
        # Create test data
        prompt1 = {
            "title": "Prompt 1",
            "content": "Content 1",
            "description": "Description 1"
        }
        prompt2 = {
            "title": "Prompt 2",
            "content": "Content 2",
            "description": "Description 2"
        }

        client.post("/prompts", json=prompt1)
        client.post("/prompts", json=prompt2)

        # Search with empty query and description filter
        response = client.get("/prompts?search=&filter=description")
        prompts = response.json()["prompts"]

        # Should return all prompts when search query is empty
        assert len(prompts) == 2

class TestSearchBugs:
    """Test cases for the three reported search bugs.

    Bug #1: Tags search with partial match ("convers" vs "conversa")
    Bug #2: Content filter doesn't work
    Bug #3: "All" filter doesn't search content field properly
    """

    def test_bug1_partial_tag_search(self, client: TestClient):
        """Test Bug #1: Partial tag matching should work.

        When searching for "convers" with tags filter, prompts with "Conversational AI" tag should appear.
        """
        # Create prompts with different tags
        prompt1 = {
            "title": "AI Assistant",
            "content": "Content 1",
            "tags": ["Conversational AI", "chatbot", "NLP"]
        }
        prompt2 = {
            "title": "Data Analysis",
            "content": "Content 2",
            "tags": ["data", "analysis", "python"]
        }
        prompt3 = {
            "title": "Another AI",
            "content": "Content 3",
            "tags": ["Conversational AI", "machine learning"]
        }

        client.post("/prompts", json=prompt1)
        client.post("/prompts", json=prompt2)
        client.post("/prompts", json=prompt3)

        # Search for partial tag name "convers"
        response = client.get("/prompts?search=convers&filter=tags")
        prompts = response.json()["prompts"]

        # Should return prompts with "Conversational AI" tag
        assert len(prompts) == 2
        assert all("Conversational AI" in p.get("tags", []) for p in prompts)
        assert all("data" not in p.get("tags", []) for p in prompts)

    def test_bug1_partial_tag_search_with_fuzzy(self, client: TestClient):
        """Test Bug #1 with fuzzy matching enabled (default)."""
        prompt1 = {
            "title": "AI Prompt",
            "content": "Content 1",
            "tags": ["Conversational AI"]
        }
        prompt2 = {
            "title": "Python Prompt",
            "content": "Content 2",
            "tags": ["python"]
        }

        client.post("/prompts", json=prompt1)
        client.post("/prompts", json=prompt2)

        # Search with fuzzy matching (default)
        response = client.get("/prompts?search=convers&filter=tags&fuzzy=true")
        prompts = response.json()["prompts"]

        # Should find the prompt with "Conversational AI" tag
        assert len(prompts) >= 1
        assert any("Conversational AI" in p.get("tags", []) for p in prompts)

    def test_bug2_content_filter_search(self, client: TestClient):
        """Test Bug #2: Content filter should work.

        When searching with content filter, only prompts with matching content should appear.
        """
        prompt1 = {
            "title": "Prompt 1",
            "content": "This is about content generation and AI"
        }
        prompt2 = {
            "title": "Prompt 2",
            "content": "This is about data analysis"
        }
        prompt3 = {
            "title": "Prompt 3",
            "content": "More about content generation techniques"
        }

        client.post("/prompts", json=prompt1)
        client.post("/prompts", json=prompt2)
        client.post("/prompts", json=prompt3)

        # Search for "content generation" in content field
        response = client.get("/prompts?search=content generation&filter=content")
        prompts = response.json()["prompts"]

        # Should return only prompts with "content generation" in content
        assert len(prompts) == 2
        assert all("content generation" in p.get("content", "").lower() for p in prompts)
        assert all("data analysis" not in p.get("content", "").lower() for p in prompts)

    def test_bug3_all_filter_searches_content(self, client: TestClient):
        """Test Bug #3: "All" filter should search content field.

        When searching with "all" filter, prompts with matching content should appear.
        """
        # Create a collection first
        collection = client.post("/collections", json={"name": "Content Generation"})
        collection_id = collection.json()["id"]

        prompt1 = {
            "title": "Content Gen Guide",
            "content": "This is about content generation and AI",
            "description": "A guide to content generation",
            "tags": ["content", "generation"],
            "collection_id": collection_id
        }
        prompt2 = {
            "title": "Data Analysis Guide",
            "content": "This is about data analysis",
            "description": "A guide to data analysis",
            "tags": ["data", "analysis"],
            "collection_id": collection_id
        }
        prompt3 = {
            "title": "More Content",
            "content": "Additional content generation tips",
            "description": "More content tips",
            "tags": ["tips", "content"],
            "collection_id": collection_id
        }

        client.post("/prompts", json=prompt1)
        client.post("/prompts", json=prompt2)
        client.post("/prompts", json=prompt3)

        # Search for "content generation" with "all" filter
        response = client.get("/prompts?search=content generation&filter=all")
        prompts = response.json()["prompts"]

        # Should return all 3 prompts (all have "content generation" in some field)
        assert len(prompts) == 3

        # Verify all prompts are returned
        prompt_titles = [p["title"] for p in prompts]
        assert "Content Gen Guide" in prompt_titles
        assert "Data Analysis Guide" in prompt_titles
        assert "More Content" in prompt_titles

    def test_bug3_all_filter_with_collection(self, client: TestClient):
        """Test Bug #3: "All" filter with collection filtering."""
        # Create two collections
        col1 = client.post("/collections", json={"name": "Content Generation"})
        col1_id = col1.json()["id"]

        col2 = client.post("/collections", json={"name": "Data Analysis"})
        col2_id = col2.json()["id"]

        # Create prompts in different collections
        prompt1 = {
            "title": "Content Gen 1",
            "content": "About content generation",
            "collection_id": col1_id
        }
        prompt2 = {
            "title": "Content Gen 2",
            "content": "More content generation",
            "collection_id": col1_id
        }
        prompt3 = {
            "title": "Data Analysis 1",
            "content": "About data analysis",
            "collection_id": col2_id
        }

        client.post("/prompts", json=prompt1)
        client.post("/prompts", json=prompt2)
        client.post("/prompts", json=prompt3)

        # Search for "content" with "all" filter and collection filter
        response = client.get("/prompts?search=content&filter=all&collection_id=" + col1_id)
        prompts = response.json()["prompts"]

        # Should return only prompts from col1 that match "content"
        assert len(prompts) == 2
        assert all(p["collection_id"] == col1_id for p in prompts)
        assert all("content" in p.get("content", "").lower() for p in prompts)

    def test_search_with_exact_matching(self, client: TestClient):
        """Test search with exact matching disabled (fuzzy=false)."""
        prompt1 = {
            "title": "Exact Match",
            "content": "This is an exact match test"
        }
        prompt2 = {
            "title": "Close Match",
            "content": "This is a close match test"
        }

        client.post("/prompts", json=prompt1)
        client.post("/prompts", json=prompt2)

        # Search with exact matching
        response = client.get("/prompts?search=exact match&filter=content&fuzzy=false")
        prompts = response.json()["prompts"]

        # Should return only exact match
        assert len(prompts) == 1
        assert prompts[0]["title"] == "Exact Match"

    def test_empty_search_returns_all(self, client: TestClient):
        """Test that empty search query returns all prompts regardless of filter."""
        prompt1 = {"title": "Prompt 1", "content": "Content 1"}
        prompt2 = {"title": "Prompt 2", "content": "Content 2"}

        client.post("/prompts", json=prompt1)
        client.post("/prompts", json=prompt2)

        # Empty search with content filter
        response = client.get("/prompts?search=&filter=content")
        prompts = response.json()["prompts"]

        # Should return all prompts
        assert len(prompts) == 2