"""Search functionality tests for PromptLab API.

These tests verify search functionality across different fields and edge cases.
"""

import pytest
from fastapi.testclient import TestClient

class TestSearchPrompts:
    """Tests for the search field functionality covering title, description, tags, and collection filters.

    These tests verify that selecting a specific search field from the dropdown correctly
    filters results to only prompts that match the query in that field, rather than returning
    all prompts regardless of the search query.
    """

    def test_search_by_description_field(self, client: TestClient):
        """Only prompts whose description contains the query are returned when filter=description.

        Args:
            client: TestClient instance for making API requests.
        """
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

        response = client.get("/prompts?search=Python&filter=description")
        prompts = response.json()["prompts"]

        assert len(prompts) == 2
        assert all("Python" in p.get("description", "") for p in prompts)
        assert all("JavaScript" not in p.get("description", "") for p in prompts)

    def test_search_by_tags_field(self, client: TestClient):
        """Only prompts whose tags list contains the query term are returned when filter=tags.

        Args:
            client: TestClient instance for making API requests.
        """
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

        response = client.get("/prompts?search=python&filter=tags")
        prompts = response.json()["prompts"]

        assert len(prompts) == 2
        assert all("python" in p.get("tags", []) for p in prompts)
        assert all("javascript" not in p.get("tags", []) for p in prompts)

    def test_search_by_collection_field(self, client: TestClient):
        """Only prompts belonging to collections whose name matches the query are returned when filter=collection.

        Args:
            client: TestClient instance for making API requests.
        """
        col1 = client.post("/collections", json={"name": "Python Scripts"})
        col1_id = col1.json()["id"]

        col2 = client.post("/collections", json={"name": "JavaScript Code"})
        col2_id = col2.json()["id"]

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

        response = client.get("/prompts?search=Python&filter=collection")
        prompts = response.json()["prompts"]

        assert len(prompts) == 2
        assert all(p.get("collection_id") == col1_id for p in prompts)
        assert all(p.get("collection_id") != col2_id for p in prompts)

    def test_search_by_title_field(self, client: TestClient):
        """Only prompts whose title contains the query are returned when filter=title.

        Args:
            client: TestClient instance for making API requests.
        """
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

        response = client.get("/prompts?search=Python&filter=title")
        prompts = response.json()["prompts"]

        assert len(prompts) == 2
        assert all("Python" in p.get("title", "") for p in prompts)
        assert all("JavaScript" not in p.get("title", "") for p in prompts)

    def test_search_all_fields(self, client: TestClient):
        """Searching with filter=all returns prompts matching the query in any field.

        Args:
            client: TestClient instance for making API requests.
        """
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

        response = client.get("/prompts?search=Guide&filter=all")
        prompts = response.json()["prompts"]

        assert len(prompts) == 2

    def test_search_without_filter_returns_all_fields(self, client: TestClient):
        """Searching without a filter parameter searches all fields by default.

        Args:
            client: TestClient instance for making API requests.
        """
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

        response = client.get("/prompts?search=Guide")
        prompts = response.json()["prompts"]

        assert len(prompts) == 2

    def test_empty_search_query_returns_all_prompts(self, client: TestClient):
        """An empty search query returns all prompts regardless of which filter is specified.

        Args:
            client: TestClient instance for making API requests.
        """
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

        response = client.get("/prompts?search=&filter=description")
        prompts = response.json()["prompts"]

        assert len(prompts) == 2

class TestSearchBugs:
    """Regression tests for three reported search bugs.

    Note:
        Bug 1: Tags search with partial match (e.g. "convers" should match "Conversational AI").
        Bug 2: The content filter does not return results when it should.
        Bug 3: The "all" filter does not search the content field properly.
    """

    def test_bug1_partial_tag_search(self, client: TestClient):
        """Partial tag query "convers" matches prompts tagged "Conversational AI" (Bug 1 regression).

        Note:
            This test verifies the fix for Bug 1, where a partial match against a tag value
            was not returning the expected prompts.

        Args:
            client: TestClient instance for making API requests.
        """
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

        response = client.get("/prompts?search=convers&filter=tags")
        prompts = response.json()["prompts"]

        assert len(prompts) == 2
        assert all("Conversational AI" in p.get("tags", []) for p in prompts)
        assert all("data" not in p.get("tags", []) for p in prompts)

    def test_bug1_partial_tag_search_with_fuzzy(self, client: TestClient):
        """Partial tag query with fuzzy=true finds prompts tagged "Conversational AI" (Bug 1 fuzzy variant).

        Note:
            Fuzzy matching is enabled by default. This test verifies that Bug 1's partial match
            issue is also resolved when fuzzy matching is explicitly enabled.

        Args:
            client: TestClient instance for making API requests.
        """
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

        response = client.get("/prompts?search=convers&filter=tags&fuzzy=true")
        prompts = response.json()["prompts"]

        assert len(prompts) >= 1
        assert any("Conversational AI" in p.get("tags", []) for p in prompts)

    def test_bug2_content_filter_search(self, client: TestClient):
        """filter=content correctly restricts results to prompts with matching content (Bug 2 regression).

        Note:
            This test verifies the fix for Bug 2, where the content filter was returning all
            prompts instead of only those with matching content.

        Args:
            client: TestClient instance for making API requests.
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

        response = client.get("/prompts?search=content generation&filter=content")
        prompts = response.json()["prompts"]

        assert len(prompts) == 2
        assert all("content generation" in p.get("content", "").lower() for p in prompts)
        assert all("data analysis" not in p.get("content", "").lower() for p in prompts)

    def test_bug3_all_filter_searches_content(self, client: TestClient):
        """filter=all returns prompts matching the query in any field including content (Bug 3 regression).

        Note:
            This test verifies the fix for Bug 3, where the "all" filter was not searching
            the content field, causing prompts that only matched via content to be excluded.

        Args:
            client: TestClient instance for making API requests.
        """
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

        response = client.get("/prompts?search=content generation&filter=all")
        prompts = response.json()["prompts"]

        assert len(prompts) == 3

        prompt_titles = [p["title"] for p in prompts]
        assert "Content Gen Guide" in prompt_titles
        assert "Data Analysis Guide" in prompt_titles
        assert "More Content" in prompt_titles

    def test_bug3_all_filter_with_collection(self, client: TestClient):
        """filter=all combined with collection_id returns only matching prompts from that collection (Bug 3 variant).

        Note:
            This test verifies that the Bug 3 fix does not break the combination of the "all"
            filter with a collection_id constraint.

        Args:
            client: TestClient instance for making API requests.
        """
        col1 = client.post("/collections", json={"name": "Content Generation"})
        col1_id = col1.json()["id"]

        col2 = client.post("/collections", json={"name": "Data Analysis"})
        col2_id = col2.json()["id"]

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

        response = client.get("/prompts?search=content&filter=all&collection_id=" + col1_id)
        prompts = response.json()["prompts"]

        assert len(prompts) == 2
        assert all(p["collection_id"] == col1_id for p in prompts)
        assert all("content" in p.get("content", "").lower() for p in prompts)

    def test_search_with_exact_matching(self, client: TestClient):
        """fuzzy=false restricts results to prompts containing the query as a substring.

        Args:
            client: TestClient instance for making API requests.
        """
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

        response = client.get("/prompts?search=exact match&filter=content&fuzzy=false")
        prompts = response.json()["prompts"]

        assert len(prompts) == 1
        assert prompts[0]["title"] == "Exact Match"

    def test_empty_search_returns_all(self, client: TestClient):
        """An empty search query returns all prompts regardless of which filter is active.

        Args:
            client: TestClient instance for making API requests.
        """
        prompt1 = {"title": "Prompt 1", "content": "Content 1"}
        prompt2 = {"title": "Prompt 2", "content": "Content 2"}

        client.post("/prompts", json=prompt1)
        client.post("/prompts", json=prompt2)

        response = client.get("/prompts?search=&filter=content")
        prompts = response.json()["prompts"]

        assert len(prompts) == 2


class TestSearchEdgeCases:
    """Additional search edge cases covering whitespace queries and boundary behaviors."""

    def test_search_whitespace_only_returns_all_prompts(self, client: TestClient):
        """A query consisting only of spaces is treated as empty and returns all prompts.

        Args:
            client: TestClient instance for making API requests.
        """
        client.post("/prompts", json={"title": "Prompt 1", "content": "Content 1"})
        client.post("/prompts", json={"title": "Prompt 2", "content": "Content 2"})

        resp = client.get("/prompts?search=   ")
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_search_tab_only_query_returns_all_prompts(self, client: TestClient):
        """A URL-encoded tab character as the query is treated as empty and returns all prompts.

        Args:
            client: TestClient instance for making API requests.
        """
        client.post("/prompts", json={"title": "Prompt 1", "content": "Content 1"})
        client.post("/prompts", json={"title": "Prompt 2", "content": "Content 2"})

        resp = client.get("/prompts?search=%09")
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_search_by_collection_field_no_match_returns_empty(self, client: TestClient):
        """Searching by collection name with no matching collection returns an empty result set.

        Args:
            client: TestClient instance for making API requests.
        """
        col = client.post("/collections", json={"name": "Marketing"})
        col_id = col.json()["id"]
        client.post("/prompts", json={"title": "P1", "content": "Content", "collection_id": col_id})

        resp = client.get("/prompts?search=NonExistentCollectionName&filter=collection")
        assert resp.status_code == 200
        assert resp.json()["prompts"] == []

    def test_search_by_collection_field_matches_collection_name(self, client: TestClient):
        """filter=collection with fuzzy=false matches prompts by their collection's name as a substring.

        Args:
            client: TestClient instance for making API requests.
        """
        col = client.post("/collections", json={"name": "Marketing Campaigns"})
        col_id = col.json()["id"]
        col2 = client.post("/collections", json={"name": "Engineering"})
        col2_id = col2.json()["id"]

        client.post("/prompts", json={"title": "P1", "content": "Content", "collection_id": col_id})
        client.post("/prompts", json={"title": "P2", "content": "Content", "collection_id": col2_id})

        resp = client.get("/prompts?search=Marketing&filter=collection&fuzzy=false")
        assert resp.status_code == 200
        prompts = resp.json()["prompts"]
        assert len(prompts) == 1
        assert prompts[0]["collection_id"] == col_id

    def test_search_case_insensitive_across_title_and_description(self, client: TestClient):
        """Search is case-insensitive for title and description fields.

        Args:
            client: TestClient instance for making API requests.
        """
        client.post("/prompts", json={
            "title": "PYTHON Guide",
            "content": "some content",
            "description": "A guide to PYTHON programming",
        })

        resp = client.get("/prompts?search=python&fuzzy=false")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_fuzzy_false_does_not_match_partial_word_in_isolated_field(self, client: TestClient):
        """Exact search (fuzzy=false) does not match when the query is not a substring of the field.

        Args:
            client: TestClient instance for making API requests.
        """
        client.post("/prompts", json={"title": "Advanced JavaScript", "content": "js content"})

        resp = client.get("/prompts?search=xyz&filter=title&fuzzy=false")
        assert resp.status_code == 200
        assert resp.json()["prompts"] == []
