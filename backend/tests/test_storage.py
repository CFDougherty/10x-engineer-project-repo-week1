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
        """Storage initializes with empty dictionaries for prompts and collections."""
        storage = Storage()
        assert isinstance(storage._prompts, dict)
        assert isinstance(storage._collections, dict)
        assert len(storage._prompts) == 0
        assert len(storage._collections) == 0

    def test_clear_storage(self):
        """clear() removes all prompts and collections from storage."""
        storage = Storage()

        prompt = Prompt(title="Test", content="Content")
        collection = Collection(name="Test Collection")
        storage.create_prompt(prompt)
        storage.create_collection(collection)

        storage.clear()
        assert len(storage._prompts) == 0
        assert len(storage._collections) == 0

class TestPromptCRUD:
    """Test CRUD operations for prompts."""

    def test_create_prompt(self):
        """Creating a prompt stores it and makes it retrievable by its ID."""
        storage = Storage()
        prompt = Prompt(title="Test Prompt", content="Test content")

        result = storage.create_prompt(prompt)
        assert result.id == prompt.id
        assert storage.get_prompt(prompt.id) == prompt
        assert len(storage._prompts) == 1

    def test_create_prompt_overwrites_existing(self):
        """Creating a prompt with an existing ID overwrites the stored entry."""
        storage = Storage()
        prompt1 = Prompt(title="Original", content="Original content")
        prompt2 = Prompt(id=prompt1.id, title="Updated", content="Updated content")

        storage.create_prompt(prompt1)
        storage.create_prompt(prompt2)

        retrieved = storage.get_prompt(prompt1.id)
        assert retrieved.title == "Updated"
        assert retrieved.content == "Updated content"

    def test_get_prompt_existing(self):
        """Retrieving an existing prompt returns the correct Prompt instance."""
        storage = Storage()
        prompt = Prompt(title="Test", content="Content")
        storage.create_prompt(prompt)

        result = storage.get_prompt(prompt.id)
        assert result == prompt
        assert isinstance(result, Prompt)

    def test_get_prompt_nonexistent(self):
        """Retrieving a non-existent prompt returns None."""
        storage = Storage()
        result = storage.get_prompt("nonexistent-id")
        assert result is None

    def test_get_all_prompts_empty(self):
        """get_all_prompts returns an empty list when no prompts have been stored."""
        storage = Storage()
        result = storage.get_all_prompts()
        assert result == []
        assert isinstance(result, list)

    def test_get_all_prompts_with_data(self):
        """get_all_prompts returns all stored prompts."""
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
        """Updating an existing prompt replaces it and returns the updated instance."""
        storage = Storage()
        original = Prompt(title="Original", content="Original content")
        updated = Prompt(title="Updated", content="Updated content")

        storage.create_prompt(original)
        result = storage.update_prompt(original.id, updated)

        assert result == updated
        assert storage.get_prompt(original.id) == updated

    def test_update_prompt_nonexistent(self):
        """Updating a non-existent prompt returns None."""
        storage = Storage()
        prompt = Prompt(title="Test", content="Content")
        result = storage.update_prompt("nonexistent-id", prompt)
        assert result is None

    def test_delete_prompt_existing(self):
        """Deleting an existing prompt returns True and removes it from storage."""
        storage = Storage()
        prompt = Prompt(title="Test", content="Content")
        storage.create_prompt(prompt)

        result = storage.delete_prompt(prompt.id)
        assert result is True
        assert storage.get_prompt(prompt.id) is None
        assert len(storage._prompts) == 0

    def test_delete_prompt_nonexistent(self):
        """Deleting a non-existent prompt returns False."""
        storage = Storage()
        result = storage.delete_prompt("nonexistent-id")
        assert result is False

    def test_prompt_lifecycle(self):
        """Full create-read-update-delete lifecycle of a prompt behaves correctly."""
        storage = Storage()

        prompt = Prompt(title="Lifecycle Test", content="Original content")
        created = storage.create_prompt(prompt)
        assert storage.get_prompt(prompt.id) == prompt

        retrieved = storage.get_prompt(prompt.id)
        assert retrieved == prompt

        updated_prompt = Prompt(id=prompt.id, title="Updated", content="Updated content")
        storage.update_prompt(prompt.id, updated_prompt)
        assert storage.get_prompt(prompt.id).title == "Updated"

        storage.delete_prompt(prompt.id)
        assert storage.get_prompt(prompt.id) is None

class TestCollectionCRUD:
    """Test CRUD operations for collections."""

    def test_create_collection(self):
        """Creating a collection stores it and makes it retrievable by its ID."""
        storage = Storage()
        collection = Collection(name="Test Collection")

        result = storage.create_collection(collection)
        assert result.id == collection.id
        assert storage.get_collection(collection.id) == collection
        assert len(storage._collections) == 1

    def test_create_collection_overwrites_existing(self):
        """Creating a collection with an existing ID overwrites the stored entry."""
        storage = Storage()
        collection1 = Collection(name="Original")
        collection2 = Collection(id=collection1.id, name="Updated")

        storage.create_collection(collection1)
        storage.create_collection(collection2)

        retrieved = storage.get_collection(collection1.id)
        assert retrieved.name == "Updated"

    def test_get_collection_existing(self):
        """Retrieving an existing collection returns the correct Collection instance."""
        storage = Storage()
        collection = Collection(name="Test Collection")
        storage.create_collection(collection)

        result = storage.get_collection(collection.id)
        assert result == collection
        assert isinstance(result, Collection)

    def test_get_collection_nonexistent(self):
        """Retrieving a non-existent collection returns None."""
        storage = Storage()
        result = storage.get_collection("nonexistent-id")
        assert result is None

    def test_get_all_collections_empty(self):
        """get_all_collections returns an empty list when no collections exist."""
        storage = Storage()
        result = storage.get_all_collections()
        assert result == []
        assert isinstance(result, list)

    def test_get_all_collections_with_data(self):
        """get_all_collections returns all stored collections."""
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
        """Deleting an existing collection returns True and removes it from storage."""
        storage = Storage()
        collection = Collection(name="Test Collection")
        storage.create_collection(collection)

        result = storage.delete_collection(collection.id)
        assert result is True
        assert storage.get_collection(collection.id) is None
        assert len(storage._collections) == 0

    def test_delete_collection_nonexistent(self):
        """Deleting a non-existent collection returns False."""
        storage = Storage()
        result = storage.delete_collection("nonexistent-id")
        assert result is False

    def test_collection_lifecycle(self):
        """Full create-read-delete lifecycle of a collection behaves correctly."""
        storage = Storage()

        collection = Collection(name="Lifecycle Test")
        created = storage.create_collection(collection)
        assert storage.get_collection(collection.id) == collection

        retrieved = storage.get_collection(collection.id)
        assert retrieved == collection

        storage.delete_collection(collection.id)
        assert storage.get_collection(collection.id) is None

class TestPromptCollectionRelationship:
    """Test relationships and operations between prompts and collections."""

    def test_get_prompts_by_collection_empty(self):
        """get_prompts_by_collection returns an empty list when no prompts match."""
        storage = Storage()
        result = storage.get_prompts_by_collection("nonexistent-collection")
        assert result == []
        assert isinstance(result, list)

    def test_get_prompts_by_collection_with_data(self):
        """get_prompts_by_collection returns only prompts belonging to the given collection.

        Prompts with a different or missing collection_id are excluded from the result.
        """
        storage = Storage()
        collection = Collection(name="Test Collection")
        storage.create_collection(collection)

        prompt1 = Prompt(title="Prompt 1", content="Content 1", collection_id=collection.id)
        prompt2 = Prompt(title="Prompt 2", content="Content 2", collection_id=collection.id)
        prompt3 = Prompt(title="Prompt 3", content="Content 3")

        storage.create_prompt(prompt1)
        storage.create_prompt(prompt2)
        storage.create_prompt(prompt3)

        result = storage.get_prompts_by_collection(collection.id)
        assert len(result) == 2
        assert prompt1 in result
        assert prompt2 in result
        assert prompt3 not in result

    def test_delete_prompts_by_collection_id(self):
        """delete_prompts_by_collection_id removes all prompts for a given collection.

        Prompts without a matching collection_id are left untouched.
        """
        storage = Storage()
        collection = Collection(name="Test Collection")
        storage.create_collection(collection)

        prompt1 = Prompt(title="Prompt 1", content="Content 1", collection_id=collection.id)
        prompt2 = Prompt(title="Prompt 2", content="Content 2", collection_id=collection.id)
        prompt3 = Prompt(title="Prompt 3", content="Content 3")

        storage.create_prompt(prompt1)
        storage.create_prompt(prompt2)
        storage.create_prompt(prompt3)

        storage.delete_prompts_by_collection_id(collection.id)

        all_prompts = storage.get_all_prompts()
        assert len(all_prompts) == 1
        assert all_prompts[0].id == prompt3.id

    def test_delete_collection_with_prompts(self):
        """Deleting a collection and then its prompts leaves storage empty."""
        storage = Storage()
        collection = Collection(name="Test Collection")
        storage.create_collection(collection)

        prompt1 = Prompt(title="Prompt 1", content="Content 1", collection_id=collection.id)
        prompt2 = Prompt(title="Prompt 2", content="Content 2", collection_id=collection.id)

        storage.create_prompt(prompt1)
        storage.create_prompt(prompt2)

        storage.delete_collection(collection.id)
        storage.delete_prompts_by_collection_id(collection.id)

        assert storage.get_collection(collection.id) is None
        assert len(storage.get_all_prompts()) == 0

class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_prompt_with_none_values(self):
        """Prompts with None for optional fields are stored and retrieved correctly."""
        storage = Storage()
        prompt = Prompt(title="Test", content="Content", description=None, collection_id=None)

        storage.create_prompt(prompt)
        retrieved = storage.get_prompt(prompt.id)

        assert retrieved.description is None
        assert retrieved.collection_id is None

    def test_collection_with_none_description(self):
        """Collections with None description are stored and retrieved correctly."""
        storage = Storage()
        collection = Collection(name="Test", description=None)

        storage.create_collection(collection)
        retrieved = storage.get_collection(collection.id)

        assert retrieved.description is None

    def test_multiple_prompts_same_collection(self):
        """Ten prompts assigned to the same collection are all retrievable together."""
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
        """Pydantic validation rejects empty title and content before storage is reached."""
        storage = Storage()
        with pytest.raises(Exception):
            prompt = Prompt(title="", content="")
            storage.create_prompt(prompt)

    def test_collection_with_empty_name(self):
        """Pydantic validation rejects an empty collection name before storage is reached."""
        storage = Storage()
        with pytest.raises(Exception):
            collection = Collection(name="")
            storage.create_collection(collection)

    def test_storage_isolation(self):
        """Different Storage instances are fully isolated from one another."""
        storage1 = Storage()
        storage2 = Storage()

        prompt = Prompt(title="Test", content="Content")
        storage1.create_prompt(prompt)

        assert storage1.get_prompt(prompt.id) == prompt
        assert storage2.get_prompt(prompt.id) is None

    def test_prompt_id_generation(self):
        """All auto-generated prompt IDs are unique across 100 prompts."""
        storage = Storage()
        prompts = []

        for i in range(100):
            prompt = Prompt(title=f"Prompt {i}", content=f"Content {i}")
            storage.create_prompt(prompt)
            prompts.append(prompt)

        prompt_ids = [p.id for p in prompts]
        assert len(prompt_ids) == len(set(prompt_ids))

    def test_collection_id_generation(self):
        """All auto-generated collection IDs are unique across 100 collections."""
        storage = Storage()
        collections = []

        for i in range(100):
            collection = Collection(name=f"Collection {i}")
            storage.create_collection(collection)
            collections.append(collection)

        collection_ids = [c.id for c in collections]
        assert len(collection_ids) == len(set(collection_ids))

    def test_prompt_updated_at_updates_on_modification(self):
        """updated_at timestamp on the stored prompt changes after an update call."""
        storage = Storage()
        original = Prompt(title="Original", content="Original content")
        storage.create_prompt(original)

        import time
        time.sleep(0.01)

        updated = Prompt(title="Updated", content="Updated content")
        storage.update_prompt(original.id, updated)

        retrieved = storage.get_prompt(original.id)
        assert retrieved.updated_at > original.updated_at

    def test_get_prompts_by_collection_id_method(self):
        """get_prompts_by_collection_id is equivalent to get_prompts_by_collection.

        Note:
            Two methods exist for this lookup: get_prompts_by_collection and
            get_prompts_by_collection_id. Both return identical results.
        """
        storage = Storage()
        collection = Collection(name="Test Collection")
        storage.create_collection(collection)

        prompt1 = Prompt(title="Prompt 1", content="Content 1", collection_id=collection.id)
        prompt2 = Prompt(title="Prompt 2", content="Content 2", collection_id=collection.id)
        prompt3 = Prompt(title="Prompt 3", content="Content 3")

        storage.create_prompt(prompt1)
        storage.create_prompt(prompt2)
        storage.create_prompt(prompt3)

        result = storage.get_prompts_by_collection_id(collection.id)
        assert len(result) == 2
        assert prompt1 in result
        assert prompt2 in result
        assert prompt3 not in result

    def test_prompt_validation_fails_with_empty_title(self):
        """Pydantic validation rejects empty title."""
        with pytest.raises(Exception):
            Prompt(title="", content="Valid content")

    def test_prompt_validation_fails_with_empty_content(self):
        """Pydantic validation rejects empty content."""
        with pytest.raises(Exception):
            Prompt(title="Valid title", content="")

    def test_collection_validation_fails_with_empty_name(self):
        """Pydantic validation rejects empty collection name."""
        with pytest.raises(Exception):
            Collection(name="")

    def test_prompt_validation_fails_with_whitespace_only_title(self):
        """Pydantic validation rejects whitespace-only title."""
        with pytest.raises(Exception):
            Prompt(title="   ", content="Valid content")

    def test_prompt_validation_fails_with_whitespace_only_content(self):
        """Pydantic validation rejects whitespace-only content."""
        with pytest.raises(Exception):
            Prompt(title="Valid title", content="   ")

    def test_prompt_validation_fails_with_too_long_title(self):
        """Pydantic validation rejects title exceeding the 200-character maximum."""
        with pytest.raises(Exception):
            Prompt(title="A" * 201, content="Valid content")

    def test_prompt_validation_fails_with_too_long_description(self):
        """Pydantic validation rejects description exceeding the 500-character maximum."""
        with pytest.raises(Exception):
            Prompt(title="Valid title", content="Valid content", description="A" * 501)

    def test_collection_validation_fails_with_too_long_name(self):
        """Pydantic validation rejects collection name exceeding the 100-character maximum."""
        with pytest.raises(Exception):
            Collection(name="A" * 101)

    def test_collection_validation_fails_with_too_long_description(self):
        """Pydantic validation rejects collection description exceeding the 500-character maximum."""
        with pytest.raises(Exception):
            Collection(name="Valid name", description="A" * 501)

    def test_prompt_with_maximum_valid_lengths(self):
        """Prompt creation succeeds with fields at their maximum valid lengths.

        Note:
            Title max: 200 characters. Description max: 500 characters.
        """
        prompt = Prompt(
            title="A" * 200,
            content="A",
            description="A" * 500
        )
        assert len(prompt.title) == 200
        assert len(prompt.description) == 500

    def test_collection_with_maximum_valid_lengths(self):
        """Collection creation succeeds with fields at their maximum valid lengths.

        Note:
            Name max: 100 characters. Description max: 500 characters.
        """
        collection = Collection(
            name="A" * 100,
            description="A" * 500
        )
        assert len(collection.name) == 100
        assert len(collection.description) == 500

    def test_prompt_update_preserves_id(self):
        """update_prompt stores the updated prompt under the original ID key.

        Note:
            update_prompt uses the provided prompt_id as the storage key.
            The retrieved prompt's id field reflects the updated prompt object's id.
        """
        storage = Storage()
        original = Prompt(title="Original", content="Original content")
        storage.create_prompt(original)

        updated = Prompt(title="Updated", content="Updated content")
        storage.update_prompt(original.id, updated)

        retrieved = storage.get_prompt(original.id)
        assert retrieved.id == updated.id
        assert retrieved.title == "Updated"

    def test_delete_nonexistent_prompt_returns_false(self):
        """Deleting a non-existent prompt returns False."""
        storage = Storage()
        result = storage.delete_prompt("nonexistent-id")
        assert result is False

    def test_delete_nonexistent_collection_returns_false(self):
        """Deleting a non-existent collection returns False."""
        storage = Storage()
        result = storage.delete_collection("nonexistent-id")
        assert result is False

    def test_get_all_prompts_returns_list(self):
        """get_all_prompts always returns a list."""
        storage = Storage()
        result = storage.get_all_prompts()
        assert isinstance(result, list)

    def test_get_all_collections_returns_list(self):
        """get_all_collections always returns a list."""
        storage = Storage()
        result = storage.get_all_collections()
        assert isinstance(result, list)

    def test_get_prompts_by_collection_returns_list(self):
        """get_prompts_by_collection always returns a list."""
        storage = Storage()
        result = storage.get_prompts_by_collection("nonexistent-id")
        assert isinstance(result, list)

    def test_get_prompts_by_collection_id_returns_list(self):
        """get_prompts_by_collection_id always returns a list."""
        storage = Storage()
        result = storage.get_prompts_by_collection_id("nonexistent-id")
        assert isinstance(result, list)

    def test_storage_clear_returns_none(self):
        """clear() returns None."""
        storage = Storage()
        result = storage.clear()
        assert result is None

    def test_prompt_created_at_is_set(self):
        """created_at is automatically populated when a Prompt is instantiated."""
        prompt = Prompt(title="Test", content="Content")
        assert prompt.created_at is not None
        assert isinstance(prompt.created_at, datetime)

    def test_collection_created_at_is_set(self):
        """created_at is automatically populated when a Collection is instantiated."""
        collection = Collection(name="Test")
        assert collection.created_at is not None
        assert isinstance(collection.created_at, datetime)

    def test_prompt_id_is_generated(self):
        """Prompt ID is automatically generated as a UUID4 string (36 characters)."""
        prompt = Prompt(title="Test", content="Content")
        assert prompt.id is not None
        assert len(prompt.id) == 36

    def test_collection_id_is_generated(self):
        """Collection ID is automatically generated as a UUID4 string (36 characters)."""
        collection = Collection(name="Test")
        assert collection.id is not None
        assert len(collection.id) == 36

    def test_prompt_equality(self):
        """Prompt equality comparison."""
        prompt1 = Prompt(title="Test", content="Content")
        prompt2 = Prompt(id=prompt1.id, title="Test", content="Content")
        assert prompt1 == prompt2

    def test_collection_equality(self):
        """Collection equality comparison."""
        collection1 = Collection(name="Test")
        collection2 = Collection(id=collection1.id, name="Test")
        assert collection1 == collection2

    def test_prompt_with_custom_id(self):
        """Creating a Prompt with an explicit UUID uses that ID verbatim."""
        custom_id = str(uuid4())
        prompt = Prompt(id=custom_id, title="Test", content="Content")
        assert prompt.id == custom_id

    def test_collection_with_custom_id(self):
        """Creating a Collection with an explicit ID uses that ID verbatim."""
        custom_id = "custom-id-456"
        collection = Collection(id=custom_id, name="Test")
        assert collection.id == custom_id

    def test_prompt_update_with_different_id(self):
        """update_prompt stores the new prompt under the original key.

        Note:
            update_prompt uses prompt_id as the dict key, not new_prompt.id.
            After the call, get_prompt(original.id) returns the new prompt object
            whose own .id field is the new prompt's UUID (not the original's).
        """
        storage = Storage()
        original = Prompt(title="Original", content="Original content")
        storage.create_prompt(original)

        new_prompt = Prompt(id=str(uuid4()), title="New", content="New content")
        storage.update_prompt(original.id, new_prompt)

        retrieved = storage.get_prompt(original.id)
        assert retrieved.id == new_prompt.id

    def test_create_prompt_returns_same_instance(self):
        """create_prompt returns the exact same object that was passed in."""
        storage = Storage()
        prompt = Prompt(title="Test", content="Content")
        result = storage.create_prompt(prompt)
        assert result is prompt

    def test_create_collection_returns_same_instance(self):
        """create_collection returns the exact same object that was passed in."""
        storage = Storage()
        collection = Collection(name="Test")
        result = storage.create_collection(collection)
        assert result is collection

    def test_update_prompt_returns_updated_instance(self):
        """update_prompt returns the updated prompt instance."""
        storage = Storage()
        original = Prompt(title="Original", content="Original content")
        storage.create_prompt(original)

        updated = Prompt(title="Updated", content="Updated content")
        result = storage.update_prompt(original.id, updated)
        assert result == updated

    def test_delete_prompts_by_collection_id_with_no_matches(self):
        """delete_prompts_by_collection_id leaves all prompts intact when none match."""
        storage = Storage()
        prompt1 = Prompt(title="Prompt 1", content="Content 1", collection_id="other-id")
        prompt2 = Prompt(title="Prompt 2", content="Content 2")
        storage.create_prompt(prompt1)
        storage.create_prompt(prompt2)

        storage.delete_prompts_by_collection_id("nonexistent-id")

        all_prompts = storage.get_all_prompts()
        assert len(all_prompts) == 2
        assert prompt1 in all_prompts
        assert prompt2 in all_prompts

    def test_delete_prompts_by_collection_id_removes_only_matching(self):
        """delete_prompts_by_collection_id removes only prompts whose collection_id matches.

        Prompts assigned to other collections or to no collection are untouched.
        """
        storage = Storage()
        collection1 = Collection(name="Collection 1")
        collection2 = Collection(name="Collection 2")
        storage.create_collection(collection1)
        storage.create_collection(collection2)

        prompt1 = Prompt(title="Prompt 1", content="Content 1", collection_id=collection1.id)
        prompt2 = Prompt(title="Prompt 2", content="Content 2", collection_id=collection2.id)
        prompt3 = Prompt(title="Prompt 3", content="Content 3")
        storage.create_prompt(prompt1)
        storage.create_prompt(prompt2)
        storage.create_prompt(prompt3)

        storage.delete_prompts_by_collection_id(collection1.id)

        all_prompts = storage.get_all_prompts()
        assert len(all_prompts) == 2
        assert prompt1 not in all_prompts
        assert prompt2 in all_prompts
        assert prompt3 in all_prompts

class TestDataPersistence:
    """Test data persistence within session."""

    def test_data_persists_within_session(self):
        """Data created in a Storage instance persists for the lifetime of that instance."""
        storage = Storage()

        prompt = Prompt(title="Test", content="Content")
        collection = Collection(name="Test Collection")
        storage.create_prompt(prompt)
        storage.create_collection(collection)

        assert storage.get_prompt(prompt.id) == prompt
        assert storage.get_collection(collection.id) == collection

    def test_data_isolation_between_sessions(self):
        """Data from one Storage instance is not visible in a separately created instance."""
        storage1 = Storage()
        prompt = Prompt(title="Test", content="Content")
        storage1.create_prompt(prompt)

        storage2 = Storage()
        assert storage2.get_prompt(prompt.id) is None

    def test_clear_removes_all_data(self):
        """clear() removes all prompts and collections completely."""
        storage = Storage()

        for i in range(10):
            prompt = Prompt(title=f"Prompt {i}", content=f"Content {i}")
            collection = Collection(name=f"Collection {i}")
            storage.create_prompt(prompt)
            storage.create_collection(collection)

        storage.clear()

        assert len(storage._prompts) == 0
        assert len(storage._collections) == 0
        assert storage.get_all_prompts() == []
        assert storage.get_all_collections() == []

class TestGlobalStorageInstance:
    """Test the global storage instance."""

    def test_global_storage_instance_exists(self):
        """The module-level storage singleton is a Storage instance."""
        from app.storage import storage
        assert isinstance(storage, Storage)

    def test_global_storage_operations(self):
        """CRUD operations work correctly on the global storage singleton."""
        from app.storage import storage

        storage.clear()

        prompt = Prompt(title="Global Test", content="Global content")
        storage.create_prompt(prompt)
        assert storage.get_prompt(prompt.id) == prompt

        collection = Collection(name="Global Collection")
        storage.create_collection(collection)
        assert storage.get_collection(collection.id) == collection

        storage.clear()


class TestVersioningStorage:
    """Priority 6 storage-layer versioning edge cases."""

    def test_create_prompt_version_sets_version_on_prompt_object(self):
        """create_prompt_version updates prompt.version on the prompt object itself."""
        storage = Storage()
        prompt = Prompt(title="Test", content="Content")
        storage.create_prompt(prompt)

        storage.create_prompt_version(prompt.id, prompt)

        assert prompt.version == 1

    def test_create_prompt_version_increments_sequentially(self):
        """Calling create_prompt_version multiple times increments the version number."""
        storage = Storage()
        prompt = Prompt(title="Test", content="Content")
        storage.create_prompt(prompt)

        v1 = storage.create_prompt_version(prompt.id, prompt)
        assert v1.version == 1

        prompt.title = "Updated"
        v2 = storage.create_prompt_version(prompt.id, prompt)
        assert v2.version == 2

    def test_clear_resets_version_metadata(self):
        """storage.clear() wipes version metadata and version snapshots.

        After a clear(), get_all_prompt_versions returns an empty list even
        for a prompt ID that had versions before the clear.
        """
        storage = Storage()
        prompt = Prompt(title="Test", content="Content")
        storage.create_prompt(prompt)
        storage.create_prompt_version(prompt.id, prompt)

        storage.clear()

        versions = storage.get_all_prompt_versions(prompt.id)
        assert versions == []

    def test_get_prompts_by_collection_and_by_collection_id_are_equivalent(self):
        """Both get_prompts_by_collection and get_prompts_by_collection_id return the same data.

        Note:
            Two equivalent methods exist for this query. This test documents and
            verifies that their results are identical.
        """
        storage = Storage()
        collection = Collection(name="Test")
        storage.create_collection(collection)

        p1 = Prompt(title="P1", content="c", collection_id=collection.id)
        p2 = Prompt(title="P2", content="c", collection_id=collection.id)
        storage.create_prompt(p1)
        storage.create_prompt(p2)

        result_a = storage.get_prompts_by_collection(collection.id)
        result_b = storage.get_prompts_by_collection_id(collection.id)

        assert set(p.id for p in result_a) == set(p.id for p in result_b)
        assert len(result_a) == len(result_b) == 2

    def test_update_prompt_overwrites_id_on_input_object(self):
        """update_prompt sets prompt.id = prompt_id on the passed object as a side-effect.

        Note:
            update_prompt mutates the input prompt object, setting its .id field
            to the prompt_id argument. This means the caller's object is modified
            in place and its original id is overwritten.
        """
        storage = Storage()
        original = Prompt(title="Original", content="Content")
        storage.create_prompt(original)

        different_id_prompt = Prompt(title="Updated", content="Updated content")
        original_different_id = different_id_prompt.id

        storage.update_prompt(original.id, different_id_prompt)

        assert different_id_prompt.id == original.id
        assert different_id_prompt.id != original_different_id

    def test_update_prompt_preserves_created_at_on_input_object(self):
        """update_prompt sets prompt.created_at = original.created_at on the input object.

        Note:
            update_prompt preserves the original prompt's creation timestamp by
            mutating the new prompt's .created_at field before storing it.
        """
        from datetime import datetime, timedelta, timezone
        storage = Storage()
        past_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=5)
        original = Prompt(title="Original", content="Content", created_at=past_time)
        storage.create_prompt(original)

        new_prompt = Prompt(title="Updated", content="Updated content")

        storage.update_prompt(original.id, new_prompt)

        assert new_prompt.created_at == past_time

    def test_get_all_prompt_versions_sorted_newest_first(self):
        """get_all_prompt_versions returns versions sorted by version number descending."""
        storage = Storage()
        prompt = Prompt(title="Test", content="Content")
        storage.create_prompt(prompt)

        storage.create_prompt_version(prompt.id, prompt)
        prompt.title = "V2"
        storage.create_prompt_version(prompt.id, prompt)
        prompt.title = "V3"
        storage.create_prompt_version(prompt.id, prompt)

        versions = storage.get_all_prompt_versions(prompt.id)
        version_nums = [v.version for v in versions]
        assert version_nums == sorted(version_nums, reverse=True)

    def test_update_prompt_returns_none_for_missing_id(self):
        """update_prompt must return None when the prompt_id is not in storage."""
        s = Storage()
        placeholder = Prompt(title="Ghost", content="Nowhere")
        result = s.update_prompt("nonexistent-id", placeholder)
        assert result is None

    def test_get_prompt_version_returns_none_when_prompt_has_no_versions(self):
        """get_prompt_version must return None when the prompt has no version history."""
        s = Storage()
        prompt = Prompt(title="Unversioned", content="Content")
        s.create_prompt(prompt)
        # Never called create_prompt_version, so prompt_id not in _prompt_versions
        result = s.get_prompt_version(prompt.id, 1)
        assert result is None
