"""Test for search field functionality fix.

This test verifies that the bug where selecting 'description', 'tags', or 'collection'
from the dropdown returns all prompt cards regardless of search query is fixed.
"""
import pytest
from fastapi.testclient import TestClient

def test_search_by_description_field(client: TestClient):
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
    response = client.get("/prompts?search=Python&search_field=description")
    prompts = response.json()["prompts"]

    # Should return only prompts with "Python" in description
    assert len(prompts) == 2
    assert all("Python" in p.get("description", "") for p in prompts)
    assert all("JavaScript" not in p.get("description", "") for p in prompts)

def test_search_by_tags_field(client: TestClient):
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
    response = client.get("/prompts?search=python&search_field=tags")
    prompts = response.json()["prompts"]

    # Should return only prompts with "python" in tags
    assert len(prompts) == 2
    assert all("python" in p.get("tags", []) for p in prompts)
    assert all("javascript" not in p.get("tags", []) for p in prompts)

def test_search_by_collection_field(client: TestClient):
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
    response = client.get("/prompts?search=Python&search_field=collection")
    prompts = response.json()["prompts"]

    # Should return only prompts in collections with "Python" in name
    assert len(prompts) == 2
    assert all(p.get("collection_id") == col1_id for p in prompts)
    assert all(p.get("collection_id") != col2_id for p in prompts)

def test_search_by_title_field(client: TestClient):
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
    response = client.get("/prompts?search=Python&search_field=title")
    prompts = response.json()["prompts"]

    # Should return only prompts with "Python" in title
    assert len(prompts) == 2
    assert all("Python" in p.get("title", "") for p in prompts)
    assert all("JavaScript" not in p.get("title", "") for p in prompts)

def test_search_all_fields(client: TestClient):
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
    response = client.get("/prompts?search=Guide&search_field=all")
    prompts = response.json()["prompts"]

    # Should return both prompts
    assert len(prompts) == 2

def test_empty_search_query_returns_all_prompts(client: TestClient):
    """Test that empty search query returns all prompts regardless of search field."""
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

    # Search with empty query and description field
    response = client.get("/prompts?search=&search_field=description")
    prompts = response.json()["prompts"]

    # Should return all prompts when search query is empty
    assert len(prompts) == 2