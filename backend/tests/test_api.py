"""API tests for PromptLab

These tests verify the API endpoints work correctly.
Students should expand these tests significantly in Week 3.
"""
# Add imports for new tests
import time
from datetime import datetime
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


class TestPrompts:
    """Tests for prompt endpoints."""
    
    def test_create_prompt(self, client: TestClient, sample_prompt_data):
        """Test the creation of a prompt using the client.

        Args:
            client: The TestClient used to send the request.
            sample_prompt_data: The data of the prompt to be created.
        """
        response = client.post("/prompts", json=sample_prompt_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_prompt_data["title"]
        assert data["content"] == sample_prompt_data["content"]
        assert "id" in data
        assert "created_at" in data
    
    def test_create_prompt_with_empty_strings(self, client: TestClient):
        """Test creating a prompt with empty title and content."""
        response = client.post("/prompts", json={"title": "", "content": ""})
        assert response.status_code == 400
    
    def test_create_prompt_with_very_long_strings(self, client: TestClient):
        """Test creating a prompt with very long title and content."""
        long_string = "A" * 10000
        response = client.post("/prompts", json={"title": long_string, "content": long_string})
        assert response.status_code in [201, 400]  # Should either succeed or return 400
    
    def test_create_prompt_with_special_characters(self, client: TestClient):
        """Test creating a prompt with special characters and Unicode."""
        special_data = {
            "title": "Test with émojis 🎉 and <script>alert('xss')</script>",
            "content": "Special chars: \n\t\r, quotes '\"",
            "description": "Unicode: 日本語, 中文, 한국어"
        }
        response = client.post("/prompts", json=special_data)
        assert response.status_code == 201
    
    def test_create_prompt_missing_required_field(self, client: TestClient):
        """Test creating a prompt without a title."""
        response = client.post("/prompts", json={"content": "Some content"})
        assert response.status_code == 400
    
    def test_create_prompt_with_null_values(self, client: TestClient):
        """Test creating a prompt with null values for required fields."""
        response = client.post("/prompts", json={"title": None, "content": None})
        assert response.status_code == 400
    
    def test_create_prompt_with_invalid_collection_id(self, client: TestClient):
        """Test creating a prompt with an invalid collection ID."""
        response = client.post("/prompts", json={
            "title": "Test",
            "content": "Content",
            "collection_id": "invalid-collection-id"
        })
        assert response.status_code == 400
    
    def test_list_prompts_empty(self, client: TestClient):
        """
        Test that the '/prompts' endpoint returns an empty list when no prompts exist.

        Args:
            client: The test client used to simulate HTTP requests.
        """
        response = client.get("/prompts")
        assert response.status_code == 200
        data = response.json()
        assert data["prompts"] == []
        assert data["total"] == 0
    
    def test_list_prompts_with_data(self, client: TestClient, sample_prompt_data):
        """Test listing prompts with existing data."""

        # Create a prompt first
        client.post("/prompts", json=sample_prompt_data)
        
        response = client.get("/prompts")
        assert response.status_code == 200
        data = response.json()
        assert len(data["prompts"]) == 1
        assert data["total"] == 1
    
    def test_list_prompts_with_sorting(self, client: TestClient):
        """Test sorting prompts by different fields."""
        prompt1 = {"title": "Zebra", "content": "Content for Zebra"}
        prompt2 = {"title": "Apple", "content": "Content for Apple"}

        client.post("/prompts", json=prompt1)
        time.sleep(0.1)
        client.post("/prompts", json=prompt2)

        # Test sorting by title
        response = client.get("/prompts?sort_by=title")
        prompts = response.json()["prompts"]
        assert prompts[0]["title"] == "Apple"
        assert prompts[1]["title"] == "Zebra"
    
    def test_list_prompts_with_filtering(self, client: TestClient):
        """Test filtering prompts by title."""
        prompt1 = {"title": "Apple", "content": "Fruit content"}
        prompt2 = {"title": "Banana", "content": "Another fruit"}

        client.post("/prompts", json=prompt1)
        time.sleep(0.1)
        client.post("/prompts", json=prompt2)

        response = client.get("/prompts?title=Apple")
        prompts = response.json()["prompts"]
        assert len(prompts) == 1
        assert prompts[0]["title"] == "Apple"
    
    def test_list_prompts_with_pagination(self, client: TestClient):
        """Test pagination of prompts."""
        for i in range(5):
            client.post("/prompts", json={"title": f"Prompt {i}", "content": f"Content {i}"})

        response = client.get("/prompts?limit=2&offset=0")
        data = response.json()
        assert len(data["prompts"]) == 2
        assert data["total"] >= 5
    
    def test_get_prompt_success(self, client: TestClient, sample_prompt_data):
        """Test retrieving a prompt by ID."""

        # Create a prompt first
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]
        
        response = client.get(f"/prompts/{prompt_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == prompt_id
    
    def test_get_prompt_not_found(self, client: TestClient):
        """
        Test retrieving a non-existent prompt returns a 404 status code.

        Args:
            client: A TestClient instance for sending test requests.
        """
        response = client.get("/prompts/nonexistent-id")
        assert response.status_code == 404  
    
    def test_get_prompt_with_special_id(self, client: TestClient):
        """Test retrieving a prompt with special characters in ID."""
        response = client.get("/prompts/!@#$%^&*()_+-=[]{}|;:',.<>?`~\\")
        assert response.status_code == 404
    
    def test_delete_prompt(self, client: TestClient, sample_prompt_data):
        """Test deleting a prompt and verifying its removal.

        Args:
            client: TestClient instance to make API requests.
            sample_prompt_data: Data used to create a sample prompt.
        """
        # Create a prompt first
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]
        
        # Delete it
        response = client.delete(f"/prompts/{prompt_id}")
        assert response.status_code == 204
        
        # Verify it's gone
        get_response = client.get(f"/prompts/{prompt_id}")
        assert get_response.status_code in [404, 500]  
    
    def test_delete_prompt_twice(self, client: TestClient, sample_prompt_data):
        """Test deleting a prompt twice."""
        # Create a prompt first
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]
        
        # Delete it once
        response1 = client.delete(f"/prompts/{prompt_id}")
        assert response1.status_code == 204
        
        # Try to delete it again
        response2 = client.delete(f"/prompts/{prompt_id}")
        assert response2.status_code in [204, 404]
    
    def test_update_prompt(self, client: TestClient, sample_prompt_data):
        """
        Test updating an existing prompt and verify the title and updated_at changes.

        Args:
            client: The test client used to make requests to the API.
            sample_prompt_data: JSON data to create the initial prompt.
        """
        # Create a prompt first
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]
        original_updated_at = create_response.json()["updated_at"]
        
        # Update it
        updated_data = {
            "title": "Updated Title",
            "content": "Updated content for the prompt",
            "description": "Updated description"
        }
        
        time.sleep(0.1)  # Small delay to ensure timestamp would change
        
        response = client.put(f"/prompts/{prompt_id}", json=updated_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        
        assert data["updated_at"] != original_updated_at
    
    def test_update_prompt_with_invalid_data(self, client: TestClient, sample_prompt_data):
        """Test updating a prompt with invalid data."""
        # Create a prompt first
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]
        
        # Try to update with empty title
        response = client.put(f"/prompts/{prompt_id}", json={"title": ""})
        assert response.status_code == 400
    
    def test_update_prompt_with_special_characters(self, client: TestClient, sample_prompt_data):
        """Test updating a prompt with special characters."""
        # Create a prompt first
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]
        
        updated_data = {
            "title": "Test <script>alert('xss')</script>",
            "content": "Special chars: \n\t\r",
            "description": "Unicode: 日本語"
        }
        
        response = client.put(f"/prompts/{prompt_id}", json=updated_data)
        assert response.status_code == 200
    
    def test_sorting_order(self, client: TestClient):
        """Test that prompts are sorted newest first.
        
        Args:
            client: TestClient used to post and get prompts.

        NOTE: This test might fail due to Bug #3!
        """
        
        # Create prompts with delay
        prompt1 = {"title": "First", "content": "First prompt content"}
        prompt2 = {"title": "Second", "content": "Second prompt content"}
        
        client.post("/prompts", json=prompt1)
        time.sleep(0.1)
        client.post("/prompts", json=prompt2)
        
        response = client.get("/prompts")
        prompts = response.json()["prompts"]
        
        # Newest (Second) should be first
        assert prompts[0]["title"] == "Second" 
    
    def test_prompt_lifecycle(self, client: TestClient):
        """Test the full lifecycle of a prompt (create, read, update, delete)."""
        # Create
        create_data = {"title": "Lifecycle Test", "content": "Original content"}
        create_response = client.post("/prompts", json=create_data)
        assert create_response.status_code == 201
        prompt_id = create_response.json()["id"]

        # Read
        get_response = client.get(f"/prompts/{prompt_id}")
        assert get_response.status_code == 200

        # Update
        update_data = {"title": "Updated Title", "content": "Updated content"}
        update_response = client.put(f"/prompts/{prompt_id}", json=update_data)
        assert update_response.status_code == 200

        # Delete
        delete_response = client.delete(f"/prompts/{prompt_id}")
        assert delete_response.status_code == 204

        # Verify deletion
        verify_response = client.get(f"/prompts/{prompt_id}")
        assert verify_response.status_code == 404

class TestCollections:
    """Tests for collection endpoints."""
    
    def test_create_collection(self, client: TestClient, sample_collection_data):
        """Test the creation of a new collection."""

        response = client.post("/collections", json=sample_collection_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_collection_data["name"]
        assert "id" in data
    
    def test_list_collections(self, client: TestClient, sample_collection_data):
        """Test listing collections by creating and retrieving a collection.

        Args:
            client: A test client for sending HTTP requests.
            sample_collection_data: Sample data to be used for creating a collection.
        """
        client.post("/collections", json=sample_collection_data)
        
        response = client.get("/collections")
        assert response.status_code == 200
        data = response.json()
        assert len(data["collections"]) == 1
    
    def test_get_collection_not_found(self, client: TestClient):
        # The following function tests that retrieving a non-existent collection
        # returns a 404 status code.

        """
        Test that retrieving a non-existent collection returns a 404 status code.

        Args:
            client: TestClient used to send requests to the API.
        """
        response = client.get("/collections/nonexistent-id")
        assert response.status_code == 404
    
    def test_delete_collection_with_prompts(self, client: TestClient, sample_collection_data, sample_prompt_data):
        """Test the deletion of a collection with associated prompts.
            
        Args:
        client: The test client used to perform API requests.
        sample_collection_data: The data for creating a sample collection.
        sample_prompt_data: The data for creating a sample prompt.

        NOTE: Bug #4 - prompts become orphaned after collection deletion.
        This test documents the current (buggy) behavior.
        After fixing, update the test to verify correct behavior.
        """
        # Create collection
        col_response = client.post("/collections", json=sample_collection_data)
        collection_id = col_response.json()["id"]
        
        # Create prompt in collection
        prompt_data = {**sample_prompt_data, "collection_id": collection_id}
        prompt_response = client.post("/prompts", json=prompt_data)
        prompt_id = prompt_response.json()["id"]
        
        # Delete collection
        client.delete(f"/collections/{collection_id}")
        
        # The prompt still exists but has invalid collection_id
        # This is Bug #4 - should be handled properly
        prompts = client.get("/prompts").json()["prompts"]
        if prompts:
            # Prompt exists with orphaned collection_id
            assert prompts[0]["collection_id"] == collection_id
            # After fix, collection_id should be None or prompt should be deleted
            
    def test_delete_collection_also_deletes_prompts(self, client: TestClient, sample_collection_data, sample_prompt_data):
        """Verify prompts are deleted when a collection is deleted.

        Args:
            client: TestClient instance for API requests.
            sample_collection_data: Data used to create a test collection.
            sample_prompt_data: Data used to create a test prompt.
        """
        # Create collection
        col_response = client.post("/collections", json=sample_collection_data)
        collection_id = col_response.json()["id"]

        # Create prompt in collection
        prompt_data = {**sample_prompt_data, "collection_id": collection_id}
        client.post("/prompts", json=prompt_data)

        # Delete collection
        client.delete(f"/collections/{collection_id}")

        # Verify all prompts are deleted
        response = client.get("/prompts")
        assert response.json()["prompts"] == []

    def test_delete_collection_sets_prompt_collection_id_to_none(self, client: TestClient, sample_collection_data, sample_prompt_data):
        """Test collection deletion sets prompts' collection_id to None.

        Args:
            client: A test client instance for making HTTP requests.
            sample_collection_data: Sample data for creating a collection.
            sample_prompt_data: Sample data for creating a prompt.
        """
        # Create collection
        col_response = client.post("/collections", json=sample_collection_data)
        collection_id = col_response.json()["id"]

        # Create prompt in collection
        prompt_data = {**sample_prompt_data, "collection_id": collection_id}
        client.post("/prompts", json=prompt_data)

        # Delete collection
        client.delete(f"/collections/{collection_id}")

        # Verify prompts collection_id is None
        response = client.get("/prompts")
        for prompt in response.json()["prompts"]:
            assert prompt["collection_id"] is None
            
    def test_patch_prompt_partial_update(self, client: TestClient, sample_prompt_data):
        """
        Test partially updating a prompt's title using a PATCH request.

        Args:
            client: Test client for making API requests.
            sample_prompt_data: Data for creating the initial prompt.
        """
        # Create a prompt first
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]
        original_data = create_response.json()

        # Partially update
        partial_update_data = {
            "title": "Partially Updated Title"
        }

        response = client.patch(f"/prompts/{prompt_id}", json=partial_update_data)
        assert response.status_code == 200
        updated_data = response.json()
        
        # Verify updated fields
        assert updated_data["title"] == partial_update_data["title"]
        
        # Verify unchanged fields
        assert updated_data["content"] == original_data["content"]
        assert updated_data["description"] == original_data["description"]

    def test_patch_prompt_non_existent(self, client: TestClient):
        """Test patching a non-existent prompt returns a 404 status code.

        Args:
            client: TestClient instance for sending requests.
        """
        response = client.patch("/prompts/nonexistent-id", json={"title": "New Title"})
        assert response.status_code == 404

    def test_patch_prompt_invalid_collection(self, client: TestClient, sample_prompt_data):
        """Test partial update of a prompt with an invalid collection ID.

        Args:
            client: The test client used to make requests.
            sample_prompt_data: Sample data for creating a prompt.
        """
        # Create a prompt first
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]

        # Partially update with invalid collection_id
        response = client.patch(f"/prompts/{prompt_id}", json={"collection_id": "invalid-collection-id"})
        assert response.status_code == 400

    def test_patch_prompt_empty_payload(self, client: TestClient, sample_prompt_data):
        """Test patch request with empty payload keeps the prompt unchanged.

        Args:
            client: Test client for making HTTP requests.
            sample_prompt_data: Sample data to create the initial prompt.
        """
        # Create a prompt first
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]
        original_data = create_response.json()

        # Patch with empty payload
        response = client.patch(f"/prompts/{prompt_id}", json={})
        assert response.status_code == 200
        unchanged_data = response.json()
        
        # Verify the data remains unchanged
        assert unchanged_data == original_data
        
    def test_patch_prompt_updates_timestamp(self, client: TestClient, sample_prompt_data):
        """Ensure the 'updated_at' timestamp changes after a prompt is patched.

        Args:
            client: TestClient instance for making HTTP requests.
            sample_prompt_data: Dictionary containing sample data for creating a prompt.
        """
        # Create a prompt first
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]
        original_updated_at = create_response.json()["updated_at"]

        # Small delay to ensure timestamp can change
        time.sleep(0.1)

        # Partially update the prompt by changing the title
        partial_update_data = {
            "title": "Updated Title"
        }

        response = client.patch(f"/prompts/{prompt_id}", json=partial_update_data)
        assert response.status_code == 200
        updated_data = response.json()

        # Verify the updated_at timestamp has changed
        assert updated_data["updated_at"] != original_updated_at