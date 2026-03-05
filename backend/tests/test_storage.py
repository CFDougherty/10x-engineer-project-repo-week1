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

    async def test_storage_initialization(self):
        """Storage initializes with no prompts or collections."""
        storage = Storage()
        prompts = await storage.get_all_prompts()
        collections = await storage.get_all_collections()
        assert prompts == []
        assert collections == []

    async def test_clear_storage(self):
        """clear() removes all prompts and collections from storage."""
        storage = Storage()

        prompt = Prompt(title="Test", content="Content")
        collection = Collection(name="Test Collection")
        await storage.create_prompt(prompt)
        await storage.create_collection(collection)

        await storage.clear()
        assert len(await storage.get_all_prompts()) == 0
        assert len(await storage.get_all_collections()) == 0

class TestPromptCRUD:
    """Test CRUD operations for prompts."""

    async def test_create_prompt(self):
        """Creating a prompt stores it and makes it retrievable by its ID."""
        storage = Storage()
        prompt = Prompt(title="Test Prompt", content="Test content")

        result = await storage.create_prompt(prompt)
        assert result.id == prompt.id
        assert (await storage.get_prompt(prompt.id)) == prompt
        assert len(await storage.get_all_prompts()) == 1

    async def test_create_prompt_overwrites_existing(self):
        """Updating an existing prompt by its ID replaces the stored entry."""
        storage = Storage()
        prompt1 = Prompt(title="Original", content="Original content")

        await storage.create_prompt(prompt1)
        updated = Prompt(id=prompt1.id, title="Updated", content="Updated content")
        await storage.update_prompt(prompt1.id, updated)

        retrieved = await storage.get_prompt(prompt1.id)
        assert retrieved.title == "Updated"
        assert retrieved.content == "Updated content"

    async def test_get_prompt_existing(self):
        """Retrieving an existing prompt returns the correct Prompt instance."""
        storage = Storage()
        prompt = Prompt(title="Test", content="Content")
        await storage.create_prompt(prompt)

        result = await storage.get_prompt(prompt.id)
        assert result == prompt
        assert isinstance(result, Prompt)

    async def test_get_prompt_nonexistent(self):
        """Retrieving a non-existent prompt returns None."""
        storage = Storage()
        result = await storage.get_prompt("nonexistent-id")
        assert result is None

    async def test_get_all_prompts_empty(self):
        """get_all_prompts returns an empty list when no prompts have been stored."""
        storage = Storage()
        result = await storage.get_all_prompts()
        assert result == []
        assert isinstance(result, list)

    async def test_get_all_prompts_with_data(self):
        """get_all_prompts returns all stored prompts."""
        storage = Storage()
        prompt1 = Prompt(title="First", content="First content")
        prompt2 = Prompt(title="Second", content="Second content")

        await storage.create_prompt(prompt1)
        await storage.create_prompt(prompt2)

        result = await storage.get_all_prompts()
        assert len(result) == 2
        assert prompt1 in result
        assert prompt2 in result

    async def test_update_prompt_existing(self):
        """Updating an existing prompt replaces its fields and returns the updated instance."""
        storage = Storage()
        original = Prompt(title="Original", content="Original content")
        updated = Prompt(title="Updated", content="Updated content")

        await storage.create_prompt(original)
        result = await storage.update_prompt(original.id, updated)

        assert result is not None
        assert result.id == original.id
        assert result.title == "Updated"
        assert result.content == "Updated content"
        retrieved = await storage.get_prompt(original.id)
        assert retrieved.title == "Updated"
        assert retrieved.content == "Updated content"

    async def test_update_prompt_nonexistent(self):
        """Updating a non-existent prompt returns None."""
        storage = Storage()
        prompt = Prompt(title="Test", content="Content")
        result = await storage.update_prompt("nonexistent-id", prompt)
        assert result is None

    async def test_delete_prompt_existing(self):
        """Deleting an existing prompt returns True and removes it from storage."""
        storage = Storage()
        prompt = Prompt(title="Test", content="Content")
        await storage.create_prompt(prompt)

        result = await storage.delete_prompt(prompt.id)
        assert result is True
        assert await storage.get_prompt(prompt.id) is None
        assert len(await storage.get_all_prompts()) == 0

    async def test_delete_prompt_nonexistent(self):
        """Deleting a non-existent prompt returns False."""
        storage = Storage()
        result = await storage.delete_prompt("nonexistent-id")
        assert result is False

    async def test_prompt_lifecycle(self):
        """Full create-read-update-delete lifecycle of a prompt behaves correctly."""
        storage = Storage()

        prompt = Prompt(title="Lifecycle Test", content="Original content")
        await storage.create_prompt(prompt)
        assert await storage.get_prompt(prompt.id) == prompt

        retrieved = await storage.get_prompt(prompt.id)
        assert retrieved == prompt

        updated_prompt = Prompt(id=prompt.id, title="Updated", content="Updated content")
        await storage.update_prompt(prompt.id, updated_prompt)
        assert (await storage.get_prompt(prompt.id)).title == "Updated"

        await storage.delete_prompt(prompt.id)
        assert await storage.get_prompt(prompt.id) is None

class TestCollectionCRUD:
    """Test CRUD operations for collections."""

    async def test_create_collection(self):
        """Creating a collection stores it and makes it retrievable by its ID."""
        storage = Storage()
        collection = Collection(name="Test Collection")

        result = await storage.create_collection(collection)
        assert result.id == collection.id
        assert await storage.get_collection(collection.id) == collection
        assert len(await storage.get_all_collections()) == 1

    async def test_create_collection_overwrites_existing(self):
        """Updating a collection with an existing ID replaces the stored entry."""
        storage = Storage()
        collection1 = Collection(name="Original")
        collection2 = Collection(id=collection1.id, name="Updated")

        await storage.create_collection(collection1)
        await storage.update_collection(collection1.id, collection2)

        retrieved = await storage.get_collection(collection1.id)
        assert retrieved.name == "Updated"

    async def test_get_collection_existing(self):
        """Retrieving an existing collection returns the correct Collection instance."""
        storage = Storage()
        collection = Collection(name="Test Collection")
        await storage.create_collection(collection)

        result = await storage.get_collection(collection.id)
        assert result == collection
        assert isinstance(result, Collection)

    async def test_get_collection_nonexistent(self):
        """Retrieving a non-existent collection returns None."""
        storage = Storage()
        result = await storage.get_collection("nonexistent-id")
        assert result is None

    async def test_get_all_collections_empty(self):
        """get_all_collections returns an empty list when no collections exist."""
        storage = Storage()
        result = await storage.get_all_collections()
        assert result == []
        assert isinstance(result, list)

    async def test_get_all_collections_with_data(self):
        """get_all_collections returns all stored collections."""
        storage = Storage()
        collection1 = Collection(name="First")
        collection2 = Collection(name="Second")

        await storage.create_collection(collection1)
        await storage.create_collection(collection2)

        result = await storage.get_all_collections()
        assert len(result) == 2
        assert collection1 in result
        assert collection2 in result

    async def test_delete_collection_existing(self):
        """Deleting an existing collection returns True and removes it from storage."""
        storage = Storage()
        collection = Collection(name="Test Collection")
        await storage.create_collection(collection)

        result = await storage.delete_collection(collection.id)
        assert result is True
        assert await storage.get_collection(collection.id) is None
        assert len(await storage.get_all_collections()) == 0

    async def test_delete_collection_nonexistent(self):
        """Deleting a non-existent collection returns False."""
        storage = Storage()
        result = await storage.delete_collection("nonexistent-id")
        assert result is False

    async def test_collection_lifecycle(self):
        """Full create-read-delete lifecycle of a collection behaves correctly."""
        storage = Storage()

        collection = Collection(name="Lifecycle Test")
        await storage.create_collection(collection)
        assert await storage.get_collection(collection.id) == collection

        retrieved = await storage.get_collection(collection.id)
        assert retrieved == collection

        await storage.delete_collection(collection.id)
        assert await storage.get_collection(collection.id) is None

class TestPromptCollectionRelationship:
    """Test relationships and operations between prompts and collections."""

    async def test_get_prompts_by_collection_empty(self):
        """get_prompts_by_collection returns an empty list when no prompts match."""
        storage = Storage()
        result = await storage.get_prompts_by_collection("nonexistent-collection")
        assert result == []
        assert isinstance(result, list)

    async def test_get_prompts_by_collection_with_data(self):
        """get_prompts_by_collection returns only prompts belonging to the given collection.

        Prompts with a different or missing collection_id are excluded from the result.
        """
        storage = Storage()
        collection = Collection(name="Test Collection")
        await storage.create_collection(collection)

        prompt1 = Prompt(title="Prompt 1", content="Content 1", collection_id=collection.id)
        prompt2 = Prompt(title="Prompt 2", content="Content 2", collection_id=collection.id)
        prompt3 = Prompt(title="Prompt 3", content="Content 3")

        await storage.create_prompt(prompt1)
        await storage.create_prompt(prompt2)
        await storage.create_prompt(prompt3)

        result = await storage.get_prompts_by_collection(collection.id)
        assert len(result) == 2
        assert prompt1 in result
        assert prompt2 in result
        assert prompt3 not in result

    async def test_delete_prompts_by_collection_id(self):
        """delete_prompts_by_collection_id removes all prompts for a given collection.

        Prompts without a matching collection_id are left untouched.
        """
        storage = Storage()
        collection = Collection(name="Test Collection")
        await storage.create_collection(collection)

        prompt1 = Prompt(title="Prompt 1", content="Content 1", collection_id=collection.id)
        prompt2 = Prompt(title="Prompt 2", content="Content 2", collection_id=collection.id)
        prompt3 = Prompt(title="Prompt 3", content="Content 3")

        await storage.create_prompt(prompt1)
        await storage.create_prompt(prompt2)
        await storage.create_prompt(prompt3)

        await storage.delete_prompts_by_collection_id(collection.id)

        all_prompts = await storage.get_all_prompts()
        assert len(all_prompts) == 1
        assert all_prompts[0].id == prompt3.id

    async def test_delete_collection_with_prompts(self):
        """Deleting a collection's prompts first, then the collection, leaves storage empty."""
        storage = Storage()
        collection = Collection(name="Test Collection")
        await storage.create_collection(collection)

        prompt1 = Prompt(title="Prompt 1", content="Content 1", collection_id=collection.id)
        prompt2 = Prompt(title="Prompt 2", content="Content 2", collection_id=collection.id)

        await storage.create_prompt(prompt1)
        await storage.create_prompt(prompt2)

        # Delete prompts before collection to avoid FK SET NULL making them unfindable
        await storage.delete_prompts_by_collection_id(collection.id)
        await storage.delete_collection(collection.id)

        assert await storage.get_collection(collection.id) is None
        assert len(await storage.get_all_prompts()) == 0

class TestEdgeCases:
    """Test edge cases and error conditions."""

    async def test_prompt_with_none_values(self):
        """Prompts with None for optional fields are stored and retrieved correctly."""
        storage = Storage()
        prompt = Prompt(title="Test", content="Content", description=None, collection_id=None)

        await storage.create_prompt(prompt)
        retrieved = await storage.get_prompt(prompt.id)

        assert retrieved.description is None
        assert retrieved.collection_id is None

    async def test_collection_with_none_description(self):
        """Collections with None description are stored and retrieved correctly."""
        storage = Storage()
        collection = Collection(name="Test", description=None)

        await storage.create_collection(collection)
        retrieved = await storage.get_collection(collection.id)

        assert retrieved.description is None

    async def test_multiple_prompts_same_collection(self):
        """Ten prompts assigned to the same collection are all retrievable together."""
        storage = Storage()
        collection = Collection(name="Test Collection")
        await storage.create_collection(collection)

        prompts = []
        for i in range(10):
            prompt = Prompt(title=f"Prompt {i}", content=f"Content {i}", collection_id=collection.id)
            await storage.create_prompt(prompt)
            prompts.append(prompt)

        result = await storage.get_prompts_by_collection(collection.id)
        assert len(result) == 10
        assert all(p in result for p in prompts)

    def test_prompt_with_empty_strings(self):
        """Pydantic validation rejects empty title and content before storage is reached."""
        with pytest.raises(Exception):
            Prompt(title="", content="")

    def test_collection_with_empty_name(self):
        """Pydantic validation rejects an empty collection name before storage is reached."""
        with pytest.raises(Exception):
            Collection(name="")

    async def test_storage_instances_share_database(self):
        """Multiple Storage instances share the same underlying database.

        Note:
            Unlike the previous in-memory implementation, two Storage instances
            are NOT isolated from each other — they both read from and write to
            the same PostgreSQL database.
        """
        storage1 = Storage()
        storage2 = Storage()

        prompt = Prompt(title="Test", content="Content")
        await storage1.create_prompt(prompt)

        # Both instances share the DB — storage2 can see storage1's data
        assert await storage1.get_prompt(prompt.id) == prompt
        assert await storage2.get_prompt(prompt.id) == prompt

    async def test_prompt_id_generation(self):
        """All auto-generated prompt IDs are unique across 100 prompts."""
        storage = Storage()
        prompts = []

        for i in range(100):
            prompt = Prompt(title=f"Prompt {i}", content=f"Content {i}")
            await storage.create_prompt(prompt)
            prompts.append(prompt)

        prompt_ids = [p.id for p in prompts]
        assert len(prompt_ids) == len(set(prompt_ids))

    async def test_collection_id_generation(self):
        """All auto-generated collection IDs are unique across 100 collections."""
        storage = Storage()
        collections = []

        for i in range(100):
            collection = Collection(name=f"Collection {i}")
            await storage.create_collection(collection)
            collections.append(collection)

        collection_ids = [c.id for c in collections]
        assert len(collection_ids) == len(set(collection_ids))

    async def test_prompt_updated_at_updates_on_modification(self):
        """updated_at timestamp on the stored prompt changes after an update call."""
        storage = Storage()
        original = Prompt(title="Original", content="Original content")
        await storage.create_prompt(original)

        import time
        time.sleep(0.01)

        updated = Prompt(title="Updated", content="Updated content")
        await storage.update_prompt(original.id, updated)

        retrieved = await storage.get_prompt(original.id)
        assert retrieved.updated_at > original.updated_at

    async def test_get_prompts_by_collection_id_method(self):
        """get_prompts_by_collection_id is equivalent to get_prompts_by_collection.

        Note:
            Two methods exist for this lookup: get_prompts_by_collection and
            get_prompts_by_collection_id. Both return identical results.
        """
        storage = Storage()
        collection = Collection(name="Test Collection")
        await storage.create_collection(collection)

        prompt1 = Prompt(title="Prompt 1", content="Content 1", collection_id=collection.id)
        prompt2 = Prompt(title="Prompt 2", content="Content 2", collection_id=collection.id)
        prompt3 = Prompt(title="Prompt 3", content="Content 3")

        await storage.create_prompt(prompt1)
        await storage.create_prompt(prompt2)
        await storage.create_prompt(prompt3)

        result = await storage.get_prompts_by_collection_id(collection.id)
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

    async def test_prompt_update_preserves_id(self):
        """update_prompt returns a prompt whose id matches the original stored id.

        Note:
            The database row's primary key (the original prompt_id) is never
            overwritten by update_prompt — the id field in the returned Prompt
            always equals prompt_id.
        """
        storage = Storage()
        original = Prompt(title="Original", content="Original content")
        await storage.create_prompt(original)

        updated = Prompt(title="Updated", content="Updated content")
        result = await storage.update_prompt(original.id, updated)

        retrieved = await storage.get_prompt(original.id)
        assert retrieved.id == original.id
        assert retrieved.title == "Updated"
        assert result.id == original.id

    async def test_delete_nonexistent_prompt_returns_false(self):
        """Deleting a non-existent prompt returns False."""
        storage = Storage()
        result = await storage.delete_prompt("nonexistent-id")
        assert result is False

    async def test_delete_nonexistent_collection_returns_false(self):
        """Deleting a non-existent collection returns False."""
        storage = Storage()
        result = await storage.delete_collection("nonexistent-id")
        assert result is False

    async def test_get_all_prompts_returns_list(self):
        """get_all_prompts always returns a list."""
        storage = Storage()
        result = await storage.get_all_prompts()
        assert isinstance(result, list)

    async def test_get_all_collections_returns_list(self):
        """get_all_collections always returns a list."""
        storage = Storage()
        result = await storage.get_all_collections()
        assert isinstance(result, list)

    async def test_get_prompts_by_collection_returns_list(self):
        """get_prompts_by_collection always returns a list."""
        storage = Storage()
        result = await storage.get_prompts_by_collection("nonexistent-id")
        assert isinstance(result, list)

    async def test_get_prompts_by_collection_id_returns_list(self):
        """get_prompts_by_collection_id always returns a list."""
        storage = Storage()
        result = await storage.get_prompts_by_collection_id("nonexistent-id")
        assert isinstance(result, list)

    async def test_storage_clear_returns_none(self):
        """clear() returns None."""
        storage = Storage()
        result = await storage.clear()
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

    async def test_update_prompt_does_not_change_stored_id(self):
        """update_prompt preserves the original row's id regardless of the input prompt's id.

        Note:
            The DB row's primary key is never overwritten. The returned Prompt
            always has id == prompt_id (the key), not the input object's original id.
        """
        storage = Storage()
        original = Prompt(title="Original", content="Original content")
        await storage.create_prompt(original)

        new_prompt = Prompt(id=str(uuid4()), title="New", content="New content")
        original_new_id = new_prompt.id

        result = await storage.update_prompt(original.id, new_prompt)

        # Returned prompt has the original id (DB row key), not new_prompt's id
        assert result.id == original.id
        # The input object is NOT mutated
        assert new_prompt.id == original_new_id

    async def test_create_prompt_returns_equivalent_prompt(self):
        """create_prompt returns a Prompt equal to the one passed in."""
        storage = Storage()
        prompt = Prompt(title="Test", content="Content")
        result = await storage.create_prompt(prompt)
        assert result == prompt

    async def test_create_collection_returns_equivalent_collection(self):
        """create_collection returns a Collection equal to the one passed in."""
        storage = Storage()
        collection = Collection(name="Test")
        result = await storage.create_collection(collection)
        assert result == collection

    async def test_update_prompt_returns_updated_instance(self):
        """update_prompt returns the updated prompt with the original ID."""
        storage = Storage()
        original = Prompt(title="Original", content="Original content")
        await storage.create_prompt(original)

        updated = Prompt(title="Updated", content="Updated content")
        result = await storage.update_prompt(original.id, updated)
        assert result is not None
        assert result.id == original.id
        assert result.title == "Updated"
        assert result.content == "Updated content"

    async def test_delete_prompts_by_collection_id_with_no_matches(self):
        """delete_prompts_by_collection_id leaves all prompts intact when none match."""
        storage = Storage()
        # Use a real collection so FK constraint is satisfied
        other_collection = Collection(name="Other Collection")
        await storage.create_collection(other_collection)
        prompt1 = Prompt(title="Prompt 1", content="Content 1", collection_id=other_collection.id)
        prompt2 = Prompt(title="Prompt 2", content="Content 2")
        await storage.create_prompt(prompt1)
        await storage.create_prompt(prompt2)

        await storage.delete_prompts_by_collection_id("nonexistent-id")

        all_prompts = await storage.get_all_prompts()
        assert len(all_prompts) == 2

    async def test_delete_prompts_by_collection_id_removes_only_matching(self):
        """delete_prompts_by_collection_id removes only prompts whose collection_id matches.

        Prompts assigned to other collections or to no collection are untouched.
        """
        storage = Storage()
        collection1 = Collection(name="Collection 1")
        collection2 = Collection(name="Collection 2")
        await storage.create_collection(collection1)
        await storage.create_collection(collection2)

        prompt1 = Prompt(title="Prompt 1", content="Content 1", collection_id=collection1.id)
        prompt2 = Prompt(title="Prompt 2", content="Content 2", collection_id=collection2.id)
        prompt3 = Prompt(title="Prompt 3", content="Content 3")
        await storage.create_prompt(prompt1)
        await storage.create_prompt(prompt2)
        await storage.create_prompt(prompt3)

        await storage.delete_prompts_by_collection_id(collection1.id)

        all_prompts = await storage.get_all_prompts()
        assert len(all_prompts) == 2
        assert prompt1 not in all_prompts
        assert prompt2 in all_prompts
        assert prompt3 in all_prompts

class TestDataPersistence:
    """Test data persistence within session."""

    async def test_data_persists_within_session(self):
        """Data created in a Storage instance persists for the lifetime of that instance."""
        storage = Storage()

        prompt = Prompt(title="Test", content="Content")
        collection = Collection(name="Test Collection")
        await storage.create_prompt(prompt)
        await storage.create_collection(collection)

        assert await storage.get_prompt(prompt.id) == prompt
        assert await storage.get_collection(collection.id) == collection

    async def test_data_shared_between_storage_instances(self):
        """Data written via one Storage instance is visible through another.

        Note:
            With PostgreSQL backing, all Storage instances share the same
            database — data is visible across instances (unlike the previous
            in-memory implementation).
        """
        storage1 = Storage()
        storage2 = Storage()
        prompt = Prompt(title="Test", content="Content")
        await storage1.create_prompt(prompt)

        assert await storage2.get_prompt(prompt.id) == prompt

    async def test_clear_removes_all_data(self):
        """clear() removes all prompts and collections completely."""
        storage = Storage()

        for i in range(10):
            prompt = Prompt(title=f"Prompt {i}", content=f"Content {i}")
            collection = Collection(name=f"Collection {i}")
            await storage.create_prompt(prompt)
            await storage.create_collection(collection)

        await storage.clear()

        assert await storage.get_all_prompts() == []
        assert await storage.get_all_collections() == []

class TestGlobalStorageInstance:
    """Test the global storage instance."""

    def test_global_storage_instance_exists(self):
        """The module-level storage singleton is a Storage instance."""
        from app.storage import storage
        assert isinstance(storage, Storage)

    async def test_global_storage_operations(self):
        """CRUD operations work correctly on the global storage singleton."""
        from app.storage import storage

        await storage.clear()

        prompt = Prompt(title="Global Test", content="Global content")
        await storage.create_prompt(prompt)
        assert await storage.get_prompt(prompt.id) == prompt

        collection = Collection(name="Global Collection")
        await storage.create_collection(collection)
        assert await storage.get_collection(collection.id) == collection

        await storage.clear()


class TestVersioningStorage:
    """Priority 6 storage-layer versioning edge cases."""

    async def test_create_prompt_version_sets_version_number(self):
        """create_prompt_version returns a PromptVersion with version=1 and updates the stored prompt."""
        storage = Storage()
        prompt = Prompt(title="Test", content="Content")
        await storage.create_prompt(prompt)

        version = await storage.create_prompt_version(prompt.id, prompt)

        assert version.version == 1
        retrieved = await storage.get_prompt(prompt.id)
        assert retrieved.version == 1

    async def test_create_prompt_version_increments_sequentially(self):
        """Calling create_prompt_version multiple times increments the version number."""
        storage = Storage()
        prompt = Prompt(title="Test", content="Content")
        await storage.create_prompt(prompt)

        v1 = await storage.create_prompt_version(prompt.id, prompt)
        assert v1.version == 1

        prompt.title = "Updated"
        v2 = await storage.create_prompt_version(prompt.id, prompt)
        assert v2.version == 2

    async def test_clear_resets_version_metadata(self):
        """storage.clear() wipes version metadata and version snapshots.

        After a clear(), get_all_prompt_versions returns an empty list even
        for a prompt ID that had versions before the clear.
        """
        storage = Storage()
        prompt = Prompt(title="Test", content="Content")
        await storage.create_prompt(prompt)
        await storage.create_prompt_version(prompt.id, prompt)

        await storage.clear()

        versions = await storage.get_all_prompt_versions(prompt.id)
        assert versions == []

    async def test_get_prompts_by_collection_and_by_collection_id_are_equivalent(self):
        """Both get_prompts_by_collection and get_prompts_by_collection_id return the same data.

        Note:
            Two equivalent methods exist for this query. This test documents and
            verifies that their results are identical.
        """
        storage = Storage()
        collection = Collection(name="Test")
        await storage.create_collection(collection)

        p1 = Prompt(title="P1", content="c", collection_id=collection.id)
        p2 = Prompt(title="P2", content="c", collection_id=collection.id)
        await storage.create_prompt(p1)
        await storage.create_prompt(p2)

        result_a = await storage.get_prompts_by_collection(collection.id)
        result_b = await storage.get_prompts_by_collection_id(collection.id)

        assert set(p.id for p in result_a) == set(p.id for p in result_b)
        assert len(result_a) == len(result_b) == 2

    async def test_update_prompt_returns_prompt_with_original_id(self):
        """update_prompt returns a Prompt whose id equals the original prompt_id key.

        Note:
            The database row's primary key is never changed by update_prompt.
            The returned Prompt always has id == prompt_id regardless of the
            id field on the input prompt object.
        """
        storage = Storage()
        original = Prompt(title="Original", content="Content")
        await storage.create_prompt(original)

        different_id_prompt = Prompt(title="Updated", content="Updated content")
        original_different_id = different_id_prompt.id

        result = await storage.update_prompt(original.id, different_id_prompt)

        assert result.id == original.id
        # Input object is NOT mutated
        assert different_id_prompt.id == original_different_id

    async def test_update_prompt_preserves_created_at_in_returned_prompt(self):
        """update_prompt preserves the original created_at in the returned Prompt.

        Note:
            The returned Prompt's created_at equals the original prompt's
            created_at, not the input prompt's created_at. The input object
            is NOT mutated.
        """
        from datetime import datetime, timedelta, timezone
        storage = Storage()
        past_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=5)
        original = Prompt(title="Original", content="Content", created_at=past_time)
        await storage.create_prompt(original)

        new_prompt = Prompt(title="Updated", content="Updated content")
        original_new_created_at = new_prompt.created_at

        result = await storage.update_prompt(original.id, new_prompt)

        # Returned prompt has the original created_at
        assert result.created_at == past_time
        # Input object is NOT mutated
        assert new_prompt.created_at == original_new_created_at

    async def test_get_all_prompt_versions_sorted_newest_first(self):
        """get_all_prompt_versions returns versions sorted by version number descending."""
        storage = Storage()
        prompt = Prompt(title="Test", content="Content")
        await storage.create_prompt(prompt)

        await storage.create_prompt_version(prompt.id, prompt)
        prompt.title = "V2"
        await storage.create_prompt_version(prompt.id, prompt)
        prompt.title = "V3"
        await storage.create_prompt_version(prompt.id, prompt)

        versions = await storage.get_all_prompt_versions(prompt.id)
        version_nums = [v.version for v in versions]
        assert version_nums == sorted(version_nums, reverse=True)

    async def test_update_prompt_returns_none_for_missing_id(self):
        """update_prompt must return None when the prompt_id is not in storage."""
        s = Storage()
        placeholder = Prompt(title="Ghost", content="Nowhere")
        result = await s.update_prompt("nonexistent-id", placeholder)
        assert result is None

    async def test_get_prompt_version_returns_none_when_prompt_has_no_versions(self):
        """get_prompt_version must return None when the prompt has no version history."""
        s = Storage()
        prompt = Prompt(title="Unversioned", content="Content")
        await s.create_prompt(prompt)
        # Never called create_prompt_version
        result = await s.get_prompt_version(prompt.id, 1)
        assert result is None


class TestBatchOperations:
    """Tests for batch storage operations."""

    async def test_batch_create_prompts_empty_list_is_noop(self):
        """batch_create_prompts([]) must return None without touching the database."""
        s = Storage()
        result = await s.batch_create_prompts([])
        assert result is None
        assert len(await s.get_all_prompts()) == 0

    async def test_batch_update_collection_ids_empty_list_is_noop(self):
        """batch_update_collection_ids([]) must return without error."""
        s = Storage()
        result = await s.batch_update_collection_ids([])
        assert result is None

    async def test_batch_set_embeddings_empty_list_is_noop(self):
        """batch_set_embeddings([]) must return without error."""
        s = Storage()
        result = await s.batch_set_embeddings([])
        assert result is None

    async def test_batch_create_prompts_inserts_all(self):
        """batch_create_prompts must insert every prompt in one transaction."""
        s = Storage()
        prompts = [Prompt(title=f"P{i}", content="c") for i in range(3)]
        await s.batch_create_prompts(prompts)
        all_prompts = await s.get_all_prompts()
        assert len(all_prompts) == 3

    async def test_count_embedded_prompts_with_collection_filter(self):
        """count_embedded_prompts must count only prompts in the given collection."""
        from app.models import Collection
        from unittest.mock import patch
        s = Storage()

        col = Collection(name="Col1")
        await s.create_collection(col)

        p1 = Prompt(title="In Col", content="c", collection_id=col.id)
        p2 = Prompt(title="No Col", content="c")
        with patch("app.embeddings.agenerate_embedding", side_effect=RuntimeError("disabled")):
            await s.create_prompt(p1)
            await s.create_prompt(p2)

        count_all = await s.count_embedded_prompts()
        count_col = await s.count_embedded_prompts(collection_id=col.id)
        assert count_all == 0
        assert count_col == 0


class TestCursorHelpers:
    """Tests for _encode_cursor / _decode_cursor helpers."""

    def test_decode_cursor_invalid_base64_raises_value_error(self):
        """_decode_cursor must raise ValueError for non-base64 input."""
        from app.storage import _decode_cursor
        with pytest.raises(ValueError, match="Invalid pagination cursor"):
            _decode_cursor("!!!not-base64!!!")

    def test_decode_cursor_valid_base64_but_invalid_json_raises_value_error(self):
        """_decode_cursor must raise ValueError when base64 decodes to non-JSON."""
        import base64
        from app.storage import _decode_cursor
        bad = base64.urlsafe_b64encode(b"not json at all").decode()
        with pytest.raises(ValueError, match="Invalid pagination cursor"):
            _decode_cursor(bad)

    def test_decode_cursor_valid_json_missing_keys_raises_value_error(self):
        """_decode_cursor must raise ValueError when JSON is missing 't' or 'id' keys."""
        import base64, json
        from app.storage import _decode_cursor
        payload = base64.urlsafe_b64encode(json.dumps({"x": 1}).encode()).decode()
        with pytest.raises(ValueError, match="Invalid pagination cursor"):
            _decode_cursor(payload)

    def test_roundtrip_encode_decode(self):
        """_encode_cursor / _decode_cursor must round-trip correctly."""
        from datetime import datetime, timezone
        from app.storage import _encode_cursor, _decode_cursor
        import uuid
        ts = datetime.now(timezone.utc).replace(tzinfo=None)
        pid = str(uuid.uuid4())
        cursor = _encode_cursor(ts, pid)
        decoded_ts, decoded_id = _decode_cursor(cursor)
        assert decoded_id == pid
        assert abs((decoded_ts - ts).total_seconds()) < 1


class TestBackfillEmbeddings:
    """Tests for storage.backfill_embeddings()."""

    async def test_backfill_returns_zero_when_no_prompts(self):
        """backfill_embeddings must return 0 when no prompts exist."""
        s = Storage()
        count = await s.backfill_embeddings(generate_fn=lambda *_: [0.0] * 384)
        assert count == 0

    async def test_backfill_batch_failure_falls_back_to_per_item(self):
        """backfill_embeddings must fall back to per-item when generate_embeddings_batch raises."""
        from unittest.mock import patch
        s = Storage()

        p = Prompt(title="Need Embed", content="content")
        with patch("app.embeddings.agenerate_embedding", side_effect=RuntimeError("disabled")):
            await s.create_prompt(p)

        fake_vec = [0.1] * 384

        def per_item_fn(*_):
            return fake_vec

        with patch("app.embeddings.generate_embeddings_batch", side_effect=RuntimeError("batch unavailable")):
            count = await s.backfill_embeddings(generate_fn=per_item_fn)

        assert count == 1

    async def test_backfill_batch_success_path(self):
        """backfill_embeddings success path — batch function returns vectors (line 672)."""
        from unittest.mock import patch
        s = Storage()

        p = Prompt(title="Batchable", content="some content")
        with patch("app.embeddings.agenerate_embedding", side_effect=RuntimeError("disabled")):
            await s.create_prompt(p)

        fake_vec = [0.2] * 384

        with patch("app.embeddings.generate_embeddings_batch", return_value=[fake_vec]):
            count = await s.backfill_embeddings(generate_fn=lambda *_: fake_vec)

        assert count == 1


class TestGetPromptsPage:
    """Direct tests for storage.get_prompts_page() to cover the fetch/pagination body."""

    async def test_first_page_empty_db(self):
        """get_prompts_page on an empty DB returns empty list with no cursor."""
        storage = Storage()
        prompts, cursor, total = await storage.get_prompts_page(limit=10)
        assert prompts == []
        assert cursor is None
        assert total == 0

    async def test_first_page_returns_prompts(self):
        """get_prompts_page first page returns available prompts."""
        storage = Storage()
        p1 = Prompt(title="Alpha", content="c")
        p2 = Prompt(title="Beta", content="c")
        await storage.create_prompt(p1)
        await storage.create_prompt(p2)

        prompts, _, total = await storage.get_prompts_page(limit=10)
        assert total == 2
        assert len(prompts) == 2

    async def test_first_page_generates_next_cursor_when_more_results(self):
        """get_prompts_page emits a next_cursor when results exceed the limit."""
        storage = Storage()
        for i in range(5):
            await storage.create_prompt(Prompt(title=f"P{i}", content="c"))

        prompts, cursor, total = await storage.get_prompts_page(limit=3)
        assert len(prompts) == 3
        assert cursor is not None
        assert total == 5

    async def test_keyset_cursor_pagination(self):
        """get_prompts_page with a cursor returns the next page."""
        storage = Storage()
        for i in range(5):
            await storage.create_prompt(Prompt(title=f"P{i}", content="c"))

        page1, cursor, _ = await storage.get_prompts_page(limit=3)
        assert cursor is not None
        assert len(page1) == 3

        page2, cursor2, _ = await storage.get_prompts_page(limit=3, cursor=cursor)
        assert len(page2) == 2
        assert cursor2 is None

        # All prompts are distinct across pages
        ids1 = {p.id for p in page1}
        ids2 = {p.id for p in page2}
        assert ids1.isdisjoint(ids2)

    async def test_keyset_cursor_with_more_pages_emits_next_cursor(self):
        """get_prompts_page with a cursor emits a next_cursor when further pages remain."""
        storage = Storage()
        for i in range(7):
            await storage.create_prompt(Prompt(title=f"P{i}", content="c"))

        # Page 1 → cursor for page 2
        _, cursor1, _ = await storage.get_prompts_page(limit=3)
        assert cursor1 is not None

        # Page 2 (cursor branch) → more items remain, so cursor2 must be set
        page2, cursor2, _ = await storage.get_prompts_page(limit=3, cursor=cursor1)
        assert len(page2) == 3
        assert cursor2 is not None  # lines 304, 306-307 exercised

        # Page 3 → no more items
        page3, cursor3, _ = await storage.get_prompts_page(limit=3, cursor=cursor2)
        assert len(page3) == 1
        assert cursor3 is None

    async def test_offset_pagination(self):
        """get_prompts_page with offset skips the first N results."""
        storage = Storage()
        for i in range(4):
            await storage.create_prompt(Prompt(title=f"P{i}", content="c"))

        all_prompts, _, _ = await storage.get_prompts_page(limit=10)
        page2, _, _ = await storage.get_prompts_page(limit=10, offset=2)
        assert len(page2) == 2
        assert all_prompts[2].id == page2[0].id

    async def test_search_filter(self):
        """get_prompts_page with search returns only matching prompts."""
        storage = Storage()
        await storage.create_prompt(Prompt(title="Python Tutorial", content="c"))
        await storage.create_prompt(Prompt(title="Java Guide", content="c"))

        prompts, _, total = await storage.get_prompts_page(limit=10, search="Python", fuzzy=False)
        assert total == 1
        assert prompts[0].title == "Python Tutorial"

    async def test_collection_id_filter(self):
        """get_prompts_page with collection_id filters by collection."""
        storage = Storage()
        from app.models import Collection
        col = Collection(name="MyCol")
        await storage.create_collection(col)

        p_in = Prompt(title="In", content="c", collection_id=col.id)
        p_out = Prompt(title="Out", content="c")
        await storage.create_prompt(p_in)
        await storage.create_prompt(p_out)

        prompts, _, total = await storage.get_prompts_page(limit=10, collection_id=col.id)
        assert total == 1
        assert prompts[0].title == "In"

    async def test_collection_search_field(self):
        """get_prompts_page with search_field='collection' searches by collection name."""
        storage = Storage()
        from app.models import Collection
        col = Collection(name="UniqueColSearchName")
        await storage.create_collection(col)

        p = Prompt(title="Prompt", content="c", collection_id=col.id)
        await storage.create_prompt(p)
        await storage.create_prompt(Prompt(title="Other", content="c"))

        prompts, _, total = await storage.get_prompts_page(
            limit=10, search="UniqueColSearch", search_field="collection", fuzzy=False
        )
        assert total == 1
        assert prompts[0].title == "Prompt"

    async def test_update_collection_not_found_returns_none(self):
        """update_collection must return None when the collection_id does not exist."""
        storage = Storage()
        from app.models import Collection
        result = await storage.update_collection("nonexistent-id", Collection(name="X"))
        assert result is None

    async def test_batch_update_collection_ids_actual_assignments(self):
        """batch_update_collection_ids must set collection_id for each (prompt_id, col_id) pair."""
        storage = Storage()
        from app.models import Collection
        col = Collection(name="Batch Col")
        await storage.create_collection(col)

        p = Prompt(title="Assignable", content="c")
        await storage.create_prompt(p)

        await storage.batch_update_collection_ids([(p.id, col.id)])

        updated = await storage.get_prompt(p.id)
        assert updated.collection_id == col.id


class TestSemanticSearch:
    """Tests for storage.semantic_search() and count_semantic_results()."""

    async def test_semantic_search_no_embeddings_returns_empty(self):
        """semantic_search returns empty list when no prompts have embeddings."""
        storage = Storage()
        await storage.create_prompt(Prompt(title="No Embed", content="c"))
        query_vec = [0.1] * 384
        results = await storage.semantic_search(query_embedding=query_vec, limit=10)
        assert results == []

    async def test_semantic_search_finds_similar_prompt(self):
        """semantic_search returns prompts whose embeddings are close to the query."""
        storage = Storage()
        p = Prompt(title="Embedded", content="c")
        await storage.create_prompt(p)

        # Give it an embedding identical to the query (cosine distance = 0)
        vec = [1.0] + [0.0] * 383
        await storage.batch_set_embeddings([(p.id, vec)])

        results = await storage.semantic_search(query_embedding=vec, limit=10)
        assert len(results) == 1
        assert results[0].id == p.id

    async def test_count_semantic_results_with_embeddings(self):
        """count_semantic_results returns correct count of matching prompts."""
        storage = Storage()
        p = Prompt(title="Countable", content="c")
        await storage.create_prompt(p)

        vec = [1.0] + [0.0] * 383
        await storage.batch_set_embeddings([(p.id, vec)])

        count = await storage.count_semantic_results(query_embedding=vec)
        assert count == 1

    async def test_count_semantic_results_no_embeddings(self):
        """count_semantic_results returns 0 when no prompts have embeddings."""
        storage = Storage()
        await storage.create_prompt(Prompt(title="No vec", content="c"))
        count = await storage.count_semantic_results(query_embedding=[0.1] * 384)
        assert count == 0

    async def test_semantic_search_with_collection_id_filter(self):
        """semantic_search with collection_id returns only prompts in that collection."""
        storage = Storage()
        col = Collection(name="Filtered Col")
        await storage.create_collection(col)

        p_in = Prompt(title="In col", content="c", collection_id=col.id)
        p_out = Prompt(title="Out col", content="c")
        await storage.create_prompt(p_in)
        await storage.create_prompt(p_out)

        vec = [1.0] + [0.0] * 383
        await storage.batch_set_embeddings([(p_in.id, vec), (p_out.id, vec)])

        results = await storage.semantic_search(query_embedding=vec, limit=10, collection_id=col.id)
        assert len(results) == 1
        assert results[0].id == p_in.id

    async def test_count_semantic_results_with_collection_id_filter(self):
        """count_semantic_results with collection_id counts only prompts in that collection."""
        storage = Storage()
        col = Collection(name="Count Col")
        await storage.create_collection(col)

        p_in = Prompt(title="In col", content="c", collection_id=col.id)
        p_out = Prompt(title="Out col", content="c")
        await storage.create_prompt(p_in)
        await storage.create_prompt(p_out)

        vec = [1.0] + [0.0] * 383
        await storage.batch_set_embeddings([(p_in.id, vec), (p_out.id, vec)])

        count = await storage.count_semantic_results(query_embedding=vec, collection_id=col.id)
        assert count == 1
