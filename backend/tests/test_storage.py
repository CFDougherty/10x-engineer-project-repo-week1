"""Comprehensive test suite for storage functionality.

This test suite aims to achieve 80%+ code coverage by testing:
- CRUD operations for prompts and collections
- Data persistence within session
- Edge cases and error conditions
"""

import pytest
from app.storage import Storage
from app.models import Prompt, Collection
from datetime import datetime
from uuid import uuid4

class TestStorageInitialization:
    """Test storage initialization and basic properties."""

    def test_storage_initialization(self):
        """Test that storage initializes with empty dictionaries."""
        storage = Storage()
        assert isinstance(storage._prompts, dict)
        assert isinstance(storage._collections, dict)
        assert len(storage._prompts) == 0
        assert len(storage._collections) == 0

    def test_clear_storage(self):
        """Test that clear() removes all data."""
        storage = Storage()

        # Add some data
        prompt = Prompt(title="Test", content="Content")
        collection = Collection(name="Test Collection")
        storage.create_prompt(prompt)
        storage.create_collection(collection)

        # Clear storage
        storage.clear()
        assert len(storage._prompts) == 0
        assert len(storage._collections) == 0

class TestPromptCRUD:
    """Test CRUD operations for prompts."""

    def test_create_prompt(self):
        """Test creating a prompt."""
        storage = Storage()
        prompt = Prompt(title="Test Prompt", content="Test content")

        result = storage.create_prompt(prompt)
        assert result.id == prompt.id
        assert storage.get_prompt(prompt.id) == prompt
        assert len(storage._prompts) == 1

    def test_create_prompt_overwrites_existing(self):
        """Test that creating a prompt with existing ID overwrites it."""
        storage = Storage()
        prompt1 = Prompt(title="Original", content="Original content")
        prompt2 = Prompt(id=prompt1.id, title="Updated", content="Updated content")

        storage.create_prompt(prompt1)
        storage.create_prompt(prompt2)

        retrieved = storage.get_prompt(prompt1.id)
        assert retrieved.title == "Updated"
        assert retrieved.content == "Updated content"

    def test_get_prompt_existing(self):
        """Test retrieving an existing prompt."""
        storage = Storage()
        prompt = Prompt(title="Test", content="Content")
        storage.create_prompt(prompt)

        result = storage.get_prompt(prompt.id)
        assert result == prompt
        assert isinstance(result, Prompt)

    def test_get_prompt_nonexistent(self):
        """Test retrieving a non-existent prompt returns None."""
        storage = Storage()
        result = storage.get_prompt("nonexistent-id")
        assert result is None

    def test_get_all_prompts_empty(self):
        """Test getting all prompts when none exist."""
        storage = Storage()
        result = storage.get_all_prompts()
        assert result == []
        assert isinstance(result, list)

    def test_get_all_prompts_with_data(self):
        """Test getting all prompts with existing data."""
        storage = Storage()
        prompt1 = Prompt(title="First", content="First content")
        prompt2 = Prompt(title="Second", content="Second content")

        storage.create_prompt(prompt1)
        storage.create_prompt(prompt2)

        result = storage.get_all_prompts()
        assert len(result) == 2
        assert prompt1 in result
        assert prompt2 in result

    def test_update_prompt_existing(self):
        """Test updating an existing prompt."""
        storage = Storage()
        original = Prompt(title="Original", content="Original content")
        updated = Prompt(title="Updated", content="Updated content")

        storage.create_prompt(original)
        result = storage.update_prompt(original.id, updated)

        assert result == updated
        assert storage.get_prompt(original.id) == updated

    def test_update_prompt_nonexistent(self):
        """Test updating a non-existent prompt returns None."""
        storage = Storage()
        prompt = Prompt(title="Test", content="Content")
        result = storage.update_prompt("nonexistent-id", prompt)
        assert result is None

    def test_delete_prompt_existing(self):
        """Test deleting an existing prompt."""
        storage = Storage()
        prompt = Prompt(title="Test", content="Content")
        storage.create_prompt(prompt)

        result = storage.delete_prompt(prompt.id)
        assert result is True
        assert storage.get_prompt(prompt.id) is None
        assert len(storage._prompts) == 0

    def test_delete_prompt_nonexistent(self):
        """Test deleting a non-existent prompt returns False."""
        storage = Storage()
        result = storage.delete_prompt("nonexistent-id")
        assert result is False

    def test_prompt_lifecycle(self):
        """Test the complete lifecycle of a prompt."""
        storage = Storage()

        # Create
        prompt = Prompt(title="Lifecycle Test", content="Original content")
        created = storage.create_prompt(prompt)
        assert storage.get_prompt(prompt.id) == prompt

        # Read
        retrieved = storage.get_prompt(prompt.id)
        assert retrieved == prompt

        # Update
        updated_prompt = Prompt(id=prompt.id, title="Updated", content="Updated content")
        storage.update_prompt(prompt.id, updated_prompt)
        assert storage.get_prompt(prompt.id).title == "Updated"

        # Delete
        storage.delete_prompt(prompt.id)
        assert storage.get_prompt(prompt.id) is None

class TestCollectionCRUD:
    """Test CRUD operations for collections."""

    def test_create_collection(self):
        """Test creating a collection."""
        storage = Storage()
        collection = Collection(name="Test Collection")

        result = storage.create_collection(collection)
        assert result.id == collection.id
        assert storage.get_collection(collection.id) == collection
        assert len(storage._collections) == 1

    def test_create_collection_overwrites_existing(self):
        """Test that creating a collection with existing ID overwrites it."""
        storage = Storage()
        collection1 = Collection(name="Original")
        collection2 = Collection(id=collection1.id, name="Updated")

        storage.create_collection(collection1)
        storage.create_collection(collection2)

        retrieved = storage.get_collection(collection1.id)
        assert retrieved.name == "Updated"

    def test_get_collection_existing(self):
        """Test retrieving an existing collection."""
        storage = Storage()
        collection = Collection(name="Test Collection")
        storage.create_collection(collection)

        result = storage.get_collection(collection.id)
        assert result == collection
        assert isinstance(result, Collection)

    def test_get_collection_nonexistent(self):
        """Test retrieving a non-existent collection returns None."""
        storage = Storage()
        result = storage.get_collection("nonexistent-id")
        assert result is None

    def test_get_all_collections_empty(self):
        """Test getting all collections when none exist."""
        storage = Storage()
        result = storage.get_all_collections()
        assert result == []
        assert isinstance(result, list)

    def test_get_all_collections_with_data(self):
        """Test getting all collections with existing data."""
        storage = Storage()
        collection1 = Collection(name="First")
        collection2 = Collection(name="Second")

        storage.create_collection(collection1)
        storage.create_collection(collection2)

        result = storage.get_all_collections()
        assert len(result) == 2
        assert collection1 in result
        assert collection2 in result

    def test_delete_collection_existing(self):
        """Test deleting an existing collection."""
        storage = Storage()
        collection = Collection(name="Test Collection")
        storage.create_collection(collection)

        result = storage.delete_collection(collection.id)
        assert result is True
        assert storage.get_collection(collection.id) is None
        assert len(storage._collections) == 0

    def test_delete_collection_nonexistent(self):
        """Test deleting a non-existent collection returns False."""
        storage = Storage()
        result = storage.delete_collection("nonexistent-id")
        assert result is False

    def test_collection_lifecycle(self):
        """Test the complete lifecycle of a collection."""
        storage = Storage()

        # Create
        collection = Collection(name="Lifecycle Test")
        created = storage.create_collection(collection)
        assert storage.get_collection(collection.id) == collection

        # Read
        retrieved = storage.get_collection(collection.id)
        assert retrieved == collection

        # Delete
        storage.delete_collection(collection.id)
        assert storage.get_collection(collection.id) is None

class TestPromptCollectionRelationship:
    """Test relationships and operations between prompts and collections."""

    def test_get_prompts_by_collection_empty(self):
        """Test getting prompts by collection when none exist."""
        storage = Storage()
        result = storage.get_prompts_by_collection("nonexistent-collection")
        assert result == []
        assert isinstance(result, list)

    def test_get_prompts_by_collection_with_data(self):
        """Test getting prompts by collection with existing data."""
        storage = Storage()
        collection = Collection(name="Test Collection")
        storage.create_collection(collection)

        prompt1 = Prompt(title="Prompt 1", content="Content 1", collection_id=collection.id)
        prompt2 = Prompt(title="Prompt 2", content="Content 2", collection_id=collection.id)
        prompt3 = Prompt(title="Prompt 3", content="Content 3")  # No collection

        storage.create_prompt(prompt1)
        storage.create_prompt(prompt2)
        storage.create_prompt(prompt3)

        result = storage.get_prompts_by_collection(collection.id)
        assert len(result) == 2
        assert prompt1 in result
        assert prompt2 in result
        assert prompt3 not in result

    def test_delete_prompts_by_collection_id(self):
        """Test deleting all prompts associated with a collection."""
        storage = Storage()
        collection = Collection(name="Test Collection")
        storage.create_collection(collection)

        prompt1 = Prompt(title="Prompt 1", content="Content 1", collection_id=collection.id)
        prompt2 = Prompt(title="Prompt 2", content="Content 2", collection_id=collection.id)
        prompt3 = Prompt(title="Prompt 3", content="Content 3")  # Different collection

        storage.create_prompt(prompt1)
        storage.create_prompt(prompt2)
        storage.create_prompt(prompt3)

        storage.delete_prompts_by_collection_id(collection.id)

        all_prompts = storage.get_all_prompts()
        assert len(all_prompts) == 1
        assert all_prompts[0].id == prompt3.id

    def test_delete_collection_with_prompts(self):
        """Test deleting a collection and its associated prompts."""
        storage = Storage()
        collection = Collection(name="Test Collection")
        storage.create_collection(collection)

        prompt1 = Prompt(title="Prompt 1", content="Content 1", collection_id=collection.id)
        prompt2 = Prompt(title="Prompt 2", content="Content 2", collection_id=collection.id)

        storage.create_prompt(prompt1)
        storage.create_prompt(prompt2)

        # Delete collection and prompts
        storage.delete_collection(collection.id)
        storage.delete_prompts_by_collection_id(collection.id)

        assert storage.get_collection(collection.id) is None
        assert len(storage.get_all_prompts()) == 0

class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_prompt_with_none_values(self):
        """Test handling of None values in prompt fields."""
        storage = Storage()
        prompt = Prompt(title="Test", content="Content", description=None, collection_id=None)

        storage.create_prompt(prompt)
        retrieved = storage.get_prompt(prompt.id)

        assert retrieved.description is None
        assert retrieved.collection_id is None

    def test_collection_with_none_description(self):
        """Test handling of None description in collection."""
        storage = Storage()
        collection = Collection(name="Test", description=None)

        storage.create_collection(collection)
        retrieved = storage.get_collection(collection.id)

        assert retrieved.description is None

    def test_multiple_prompts_same_collection(self):
        """Test multiple prompts in the same collection."""
        storage = Storage()
        collection = Collection(name="Test Collection")
        storage.create_collection(collection)

        prompts = []
        for i in range(10):
            prompt = Prompt(title=f"Prompt {i}", content=f"Content {i}", collection_id=collection.id)
            storage.create_prompt(prompt)
            prompts.append(prompt)

        result = storage.get_prompts_by_collection(collection.id)
        assert len(result) == 10
        assert all(p in result for p in prompts)

    def test_prompt_with_empty_strings(self):
        """Test prompt creation with empty strings (should be handled by Pydantic)."""
        storage = Storage()
        # This should fail validation at the model level, not storage level
        with pytest.raises(Exception):  # Pydantic validation error
            prompt = Prompt(title="", content="")
            storage.create_prompt(prompt)

    def test_collection_with_empty_name(self):
        """Test collection creation with empty name (should fail validation)."""
        storage = Storage()
        with pytest.raises(Exception):  # Pydantic validation error
            collection = Collection(name="")
            storage.create_collection(collection)

    def test_storage_isolation(self):
        """Test that different storage instances are isolated."""
        storage1 = Storage()
        storage2 = Storage()

        prompt = Prompt(title="Test", content="Content")
        storage1.create_prompt(prompt)

        assert storage1.get_prompt(prompt.id) == prompt
        assert storage2.get_prompt(prompt.id) is None

    def test_prompt_id_generation(self):
        """Test that prompt IDs are unique."""
        storage = Storage()
        prompts = []

        for i in range(100):
            prompt = Prompt(title=f"Prompt {i}", content=f"Content {i}")
            storage.create_prompt(prompt)
            prompts.append(prompt)

        # Check all IDs are unique
        prompt_ids = [p.id for p in prompts]
        assert len(prompt_ids) == len(set(prompt_ids))

    def test_collection_id_generation(self):
        """Test that collection IDs are unique."""
        storage = Storage()
        collections = []

        for i in range(100):
            collection = Collection(name=f"Collection {i}")
            storage.create_collection(collection)
            collections.append(collection)

        # Check all IDs are unique
        collection_ids = [c.id for c in collections]
        assert len(collection_ids) == len(set(collection_ids))

    def test_prompt_updated_at_updates_on_modification(self):
        """Test that updated_at timestamp changes when prompt is updated."""
        storage = Storage()
        original = Prompt(title="Original", content="Original content")
        storage.create_prompt(original)

        # Wait a tiny bit to ensure different timestamp
        import time
        time.sleep(0.01)

        updated = Prompt(title="Updated", content="Updated content")
        storage.update_prompt(original.id, updated)

        retrieved = storage.get_prompt(original.id)
        assert retrieved.updated_at > original.updated_at

    def test_get_prompts_by_collection_id_method(self):
        """Test the get_prompts_by_collection_id method (duplicate of get_prompts_by_collection)."""
        storage = Storage()
        collection = Collection(name="Test Collection")
        storage.create_collection(collection)

        prompt1 = Prompt(title="Prompt 1", content="Content 1", collection_id=collection.id)
        prompt2 = Prompt(title="Prompt 2", content="Content 2", collection_id=collection.id)
        prompt3 = Prompt(title="Prompt 3", content="Content 3")  # No collection

        storage.create_prompt(prompt1)
        storage.create_prompt(prompt2)
        storage.create_prompt(prompt3)

        result = storage.get_prompts_by_collection_id(collection.id)
        assert len(result) == 2
        assert prompt1 in result
        assert prompt2 in result
        assert prompt3 not in result

    def test_prompt_validation_fails_with_empty_title(self):
        """Test that Pydantic validation rejects empty title."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            Prompt(title="", content="Valid content")

    def test_prompt_validation_fails_with_empty_content(self):
        """Test that Pydantic validation rejects empty content."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            Prompt(title="Valid title", content="")

    def test_collection_validation_fails_with_empty_name(self):
        """Test that Pydantic validation rejects empty collection name."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            Collection(name="")

    def test_prompt_validation_fails_with_whitespace_only_title(self):
        """Test that Pydantic validation rejects whitespace-only title."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            Prompt(title="   ", content="Valid content")

    def test_prompt_validation_fails_with_whitespace_only_content(self):
        """Test that Pydantic validation rejects whitespace-only content."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            Prompt(title="Valid title", content="   ")

    def test_prompt_validation_fails_with_too_long_title(self):
        """Test that Pydantic validation rejects title exceeding max length."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            Prompt(title="A" * 201, content="Valid content")

    def test_prompt_validation_fails_with_too_long_description(self):
        """Test that Pydantic validation rejects description exceeding max length."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            Prompt(title="Valid title", content="Valid content", description="A" * 501)

    def test_collection_validation_fails_with_too_long_name(self):
        """Test that Pydantic validation rejects collection name exceeding max length."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            Collection(name="A" * 101)

    def test_collection_validation_fails_with_too_long_description(self):
        """Test that Pydantic validation rejects collection description exceeding max length."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            Collection(name="Valid name", description="A" * 501)

    def test_prompt_with_maximum_valid_lengths(self):
        """Test prompt creation with maximum valid field lengths."""
        # Should not raise an exception
        prompt = Prompt(
            title="A" * 200,  # max length
            content="A",  # min length
            description="A" * 500  # max length
        )
        assert len(prompt.title) == 200
        assert len(prompt.description) == 500

    def test_collection_with_maximum_valid_lengths(self):
        """Test collection creation with maximum valid field lengths."""
        # Should not raise an exception
        collection = Collection(
            name="A" * 100,  # max length
            description="A" * 500  # max length
        )
        assert len(collection.name) == 100
        assert len(collection.description) == 500

    def test_prompt_update_preserves_id(self):
        """Test that updating a prompt uses the provided prompt's ID field."""
        storage = Storage()
        original = Prompt(title="Original", content="Original content")
        storage.create_prompt(original)

        updated = Prompt(title="Updated", content="Updated content")
        storage.update_prompt(original.id, updated)

        retrieved = storage.get_prompt(original.id)
        # The retrieved prompt should have the ID from the updated prompt
        assert retrieved.id == updated.id
        assert retrieved.title == "Updated"

    def test_delete_nonexistent_prompt_returns_false(self):
        """Test that deleting a non-existent prompt returns False."""
        storage = Storage()
        result = storage.delete_prompt("nonexistent-id")
        assert result is False

    def test_delete_nonexistent_collection_returns_false(self):
        """Test that deleting a non-existent collection returns False."""
        storage = Storage()
        result = storage.delete_collection("nonexistent-id")
        assert result is False

    def test_get_all_prompts_returns_list(self):
        """Test that get_all_prompts returns a list."""
        storage = Storage()
        result = storage.get_all_prompts()
        assert isinstance(result, list)

    def test_get_all_collections_returns_list(self):
        """Test that get_all_collections returns a list."""
        storage = Storage()
        result = storage.get_all_collections()
        assert isinstance(result, list)

    def test_get_prompts_by_collection_returns_list(self):
        """Test that get_prompts_by_collection returns a list."""
        storage = Storage()
        result = storage.get_prompts_by_collection("nonexistent-id")
        assert isinstance(result, list)

    def test_get_prompts_by_collection_id_returns_list(self):
        """Test that get_prompts_by_collection_id returns a list."""
        storage = Storage()
        result = storage.get_prompts_by_collection_id("nonexistent-id")
        assert isinstance(result, list)

    def test_storage_clear_returns_none(self):
        """Test that clear method returns None."""
        storage = Storage()
        result = storage.clear()
        assert result is None

    def test_prompt_created_at_is_set(self):
        """Test that created_at is automatically set when prompt is created."""
        prompt = Prompt(title="Test", content="Content")
        assert prompt.created_at is not None
        assert isinstance(prompt.created_at, datetime)

    def test_collection_created_at_is_set(self):
        """Test that created_at is automatically set when collection is created."""
        collection = Collection(name="Test")
        assert collection.created_at is not None
        assert isinstance(collection.created_at, datetime)

    def test_prompt_id_is_generated(self):
        """Test that prompt ID is automatically generated."""
        prompt = Prompt(title="Test", content="Content")
        assert prompt.id is not None
        assert len(prompt.id) == 36  # UUID4 string length

    def test_collection_id_is_generated(self):
        """Test that collection ID is automatically generated."""
        collection = Collection(name="Test")
        assert collection.id is not None
        assert len(collection.id) == 36  # UUID4 string length

    def test_prompt_equality(self):
        """Test prompt equality comparison."""
        prompt1 = Prompt(title="Test", content="Content")
        prompt2 = Prompt(id=prompt1.id, title="Test", content="Content")
        assert prompt1 == prompt2

    def test_collection_equality(self):
        """Test collection equality comparison."""
        collection1 = Collection(name="Test")
        collection2 = Collection(id=collection1.id, name="Test")
        assert collection1 == collection2

    def test_prompt_with_custom_id(self):
        """Test creating a prompt with a custom ID."""
        custom_id = "custom-id-123"
        prompt = Prompt(id=custom_id, title="Test", content="Content")
        assert prompt.id == custom_id

    def test_collection_with_custom_id(self):
        """Test creating a collection with a custom ID."""
        custom_id = "custom-id-456"
        collection = Collection(id=custom_id, name="Test")
        assert collection.id == custom_id

    def test_prompt_update_with_different_id(self):
        """Test that update_prompt uses the provided prompt_id, not prompt.id."""
        storage = Storage()
        original = Prompt(title="Original", content="Original content")
        storage.create_prompt(original)

        # Create a new prompt with a different ID
        new_prompt = Prompt(id="different-id", title="New", content="New content")
        storage.update_prompt(original.id, new_prompt)

        # The original ID should still be used as the key
        retrieved = storage.get_prompt(original.id)
        assert retrieved.id == "different-id"  # But the prompt's ID is now different

    def test_create_prompt_returns_same_instance(self):
        """Test that create_prompt returns the same instance that was passed in."""
        storage = Storage()
        prompt = Prompt(title="Test", content="Content")
        result = storage.create_prompt(prompt)
        assert result is prompt

    def test_create_collection_returns_same_instance(self):
        """Test that create_collection returns the same instance that was passed in."""
        storage = Storage()
        collection = Collection(name="Test")
        result = storage.create_collection(collection)
        assert result is collection

    def test_update_prompt_returns_updated_instance(self):
        """Test that update_prompt returns the updated instance."""
        storage = Storage()
        original = Prompt(title="Original", content="Original content")
        storage.create_prompt(original)

        updated = Prompt(title="Updated", content="Updated content")
        result = storage.update_prompt(original.id, updated)
        assert result == updated

    def test_delete_prompts_by_collection_id_with_no_matches(self):
        """Test delete_prompts_by_collection_id when no prompts match."""
        storage = Storage()
        # Create prompts with different collection IDs
        prompt1 = Prompt(title="Prompt 1", content="Content 1", collection_id="other-id")
        prompt2 = Prompt(title="Prompt 2", content="Content 2")  # No collection
        storage.create_prompt(prompt1)
        storage.create_prompt(prompt2)

        # Delete prompts for non-existent collection
        storage.delete_prompts_by_collection_id("nonexistent-id")

        # All prompts should still exist
        all_prompts = storage.get_all_prompts()
        assert len(all_prompts) == 2
        assert prompt1 in all_prompts
        assert prompt2 in all_prompts

    def test_delete_prompts_by_collection_id_removes_only_matching(self):
        """Test that delete_prompts_by_collection_id only removes prompts with matching collection_id."""
        storage = Storage()
        collection1 = Collection(name="Collection 1")
        collection2 = Collection(name="Collection 2")
        storage.create_collection(collection1)
        storage.create_collection(collection2)

        prompt1 = Prompt(title="Prompt 1", content="Content 1", collection_id=collection1.id)
        prompt2 = Prompt(title="Prompt 2", content="Content 2", collection_id=collection2.id)
        prompt3 = Prompt(title="Prompt 3", content="Content 3")  # No collection
        storage.create_prompt(prompt1)
        storage.create_prompt(prompt2)
        storage.create_prompt(prompt3)

        # Delete prompts for collection1
        storage.delete_prompts_by_collection_id(collection1.id)

        # Only prompt1 should be deleted
        all_prompts = storage.get_all_prompts()
        assert len(all_prompts) == 2
        assert prompt1 not in all_prompts
        assert prompt2 in all_prompts
        assert prompt3 in all_prompts

class TestDataPersistence:
    """Test data persistence within session."""

    def test_data_persists_within_session(self):
        """Test that data persists within the same storage instance."""
        storage = Storage()

        # Create data
        prompt = Prompt(title="Test", content="Content")
        collection = Collection(name="Test Collection")
        storage.create_prompt(prompt)
        storage.create_collection(collection)

        # Verify persistence
        assert storage.get_prompt(prompt.id) == prompt
        assert storage.get_collection(collection.id) == collection

    def test_data_isolation_between_sessions(self):
        """Test that data doesn't persist between different storage instances."""
        storage1 = Storage()
        prompt = Prompt(title="Test", content="Content")
        storage1.create_prompt(prompt)

        storage2 = Storage()
        assert storage2.get_prompt(prompt.id) is None

    def test_clear_removes_all_data(self):
        """Test that clear() removes all data completely."""
        storage = Storage()

        # Add multiple prompts and collections
        for i in range(10):
            prompt = Prompt(title=f"Prompt {i}", content=f"Content {i}")
            collection = Collection(name=f"Collection {i}")
            storage.create_prompt(prompt)
            storage.create_collection(collection)

        # Clear storage
        storage.clear()

        # Verify everything is gone
        assert len(storage._prompts) == 0
        assert len(storage._collections) == 0
        assert storage.get_all_prompts() == []
        assert storage.get_all_collections() == []

class TestGlobalStorageInstance:
    """Test the global storage instance."""

    def test_global_storage_instance_exists(self):
        """Test that the global storage instance exists."""
        from app.storage import storage
        assert isinstance(storage, Storage)

    def test_global_storage_operations(self):
        """Test operations on the global storage instance."""
        from app.storage import storage

        # Clear first to ensure clean state
        storage.clear()

        # Test prompt operations
        prompt = Prompt(title="Global Test", content="Global content")
        storage.create_prompt(prompt)
        assert storage.get_prompt(prompt.id) == prompt

        # Test collection operations
        collection = Collection(name="Global Collection")
        storage.create_collection(collection)
        assert storage.get_collection(collection.id) == collection

        # Clean up
        storage.clear()
