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
