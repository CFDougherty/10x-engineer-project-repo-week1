"""In-memory storage for PromptLab.

This module provides simple in-memory storage for prompts and collections.
In a production environment, this would be replaced with a database.
"""

from typing import Dict, List, Optional
from app.models import Prompt, Collection, PromptVersion, PromptMeta, VersionSummary


class Storage:
    def __init__(self):
        """Initialize an in-memory storage container for prompts and collections.

        This constructor sets up internal dictionaries keyed by each entity's
        unique identifier. Prompts and collections are modeled by
        :class:`app.models.Prompt` and :class:`app.models.Collection`, respectively.

        The storage is intended for lightweight, ephemeral use (e.g., local
        development/testing). Data is not persisted across process restarts.

        Returns:
            None
        """
        self._prompts: Dict[str, Prompt] = {}
        self._collections: Dict[str, Collection] = {}
        self._prompt_meta: Dict[str, PromptMeta] = {}
        self._prompt_versions: Dict[str, List[PromptVersion]] = {}
    
    # ============== Prompt Operations ==============
    
    def create_prompt(self, prompt: Prompt) -> Prompt:
        """Create (store) a prompt in the in-memory storage.

        Persists the given :class:`app.models.Prompt` instance in this storage
        container by inserting it into the internal ``_prompts`` dictionary keyed
        by ``prompt.id``. If a prompt with the same ID already exists, it will be
        overwritten. This is in-memory only and is not persisted across process
        restarts.

        Args:
            prompt: The prompt to store. Must have a valid ``id`` attribute.

        Returns:
            The same ``Prompt`` instance that was stored.
        """
        self._prompts[prompt.id] = prompt
        return prompt
    
    def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        """Retrieve a stored prompt by its unique identifier.

        Performs an in-memory lookup in this storage instance's internal prompt
        index (``self._prompts``), which is keyed by :attr:`app.models.Prompt.id`.

        Args:
            prompt_id: The unique ID of the prompt to retrieve.

        Returns:
            The corresponding :class:`app.models.Prompt` if a prompt with the given
            ID exists in storage; otherwise, ``None``.
        """
        return self._prompts.get(prompt_id)
    
    def get_all_prompts(self) -> List[Prompt]:
        """Return all prompts currently stored in memory.

        This method reads from the storage instance's internal prompt index
        (``self._prompts``), which maps prompt IDs to :class:`app.models.Prompt`
        objects, and returns the values as a list.

        Note:
            The ordering of returned prompts follows the iteration order of
            ``self._prompts.values()`` (i.e., the dictionary's insertion order for
            this process), and should not be relied upon as a stable sort order
            across runs.

        Returns:
            A list of :class:`app.models.Prompt` objects currently stored in this
            :class:`Storage` instance.
        """
        return list(self._prompts.values())
    
    def update_prompt(self, prompt_id: str, prompt: Prompt) -> Optional[Prompt]:
        """Update an existing prompt in in-memory storage.

        Replaces the prompt stored under ``prompt_id`` in ``self._prompts`` with the
        provided :class:`app.models.Prompt` instance. If no prompt exists for the
        given ID, no change is made.

        Note:
            This method updates the entry keyed by ``prompt_id`` (not necessarily
            ``prompt.id``). Callers should ensure these identifiers match to avoid
            storing a prompt under an unexpected key.

        Args:
            prompt_id: The unique identifier of the prompt to update.
            prompt: The new prompt object to store for the given ID.

        Returns:
            The updated :class:`app.models.Prompt` if ``prompt_id`` exists in storage;
            otherwise, ``None``.
        """
        if prompt_id not in self._prompts:
            return None
        # Preserve the original created_at timestamp but use the prompt's ID
        original_prompt = self._prompts[prompt_id]
        # Create a new prompt with the prompt's ID and original created_at
        updated_prompt = Prompt(
            id=prompt.id,
            title=prompt.title,
            content=prompt.content,
            description=prompt.description,
            collection_id=prompt.collection_id,
            tags=prompt.tags,
            created_at=original_prompt.created_at,
            updated_at=prompt.updated_at,
            version=prompt.version
        )
        self._prompts[prompt_id] = updated_prompt
        return updated_prompt

    def patch_prompt(self, prompt_id: str, prompt: Prompt) -> Optional[Prompt]:
        """Partially update an existing prompt in in-memory storage.

        This method is similar to :meth:`update_prompt`, but is designed for partial
        updates where only specific fields may have changed. It simply replaces the
        prompt stored under ``prompt_id`` with the provided prompt instance.

        Args:
            prompt_id: The unique identifier of the prompt to update.
            prompt: The new prompt object to store for the given ID.

        Returns:
            The updated :class:`app.models.Prompt` if ``prompt_id`` exists in storage;
            otherwise, ``None``.
        """
        if prompt_id not in self._prompts:
            return None
        # Preserve the original ID and created_at timestamp, but update updated_at
        original_prompt = self._prompts[prompt_id]
        prompt.id = original_prompt.id
        prompt.created_at = original_prompt.created_at
        self._prompts[prompt_id] = prompt
        return prompt
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a stored prompt by its unique identifier.

        Removes the prompt keyed by ``prompt_id`` from this storage instance's internal
        prompt index (``self._prompts``). If no prompt exists for the given ID, the
        storage remains unchanged.

        Args:
            prompt_id: The unique ID of the prompt to delete.

        Returns:
            ``True`` if a prompt with the given ID existed in storage and was removed;
            otherwise, ``False``.
        """
        if prompt_id in self._prompts:
            del self._prompts[prompt_id]
            return True
        return False
    
    # ============== Collection Operations ==============
    def create_collection(self, collection: Collection) -> Collection:
        """Create (store) a collection in the in-memory storage.

        Stores the provided :class:`app.models.Collection` instance in this storage
        container by inserting it into the internal ``_collections`` dictionary,
        keyed by ``collection.id``. If a collection with the same ID already exists,
        it will be overwritten. Storage is in-memory only and is not persisted
        across process restarts.

        Args:
            collection: The collection to store. Must have a valid ``id`` attribute.

        Returns:
            The same ``Collection`` instance that was stored.
        """
        self._collections[collection.id] = collection
        return collection
    
    def get_collection(self, collection_id: str) -> Optional[Collection]:
        """Retrieve a stored collection by its unique identifier.

        Performs an in-memory lookup in this storage instance's internal collection
        index (``self._collections``), which is keyed by :attr:`app.models.Collection.id`.

        Args:
            collection_id: The unique ID of the collection to retrieve.

        Returns:
            The corresponding :class:`app.models.Collection` if a collection with the
            given ID exists in storage; otherwise, ``None``.
        """
        return self._collections.get(collection_id)
    
    def get_all_collections(self) -> List[Collection]:
        """Return all collections currently stored in memory.

        This method reads from the storage instance's internal collection index
        (``self._collections``), which maps collection IDs to
        :class:`app.models.Collection` objects, and returns the values as a list.

        Note:
            The ordering of returned collections follows the iteration order of
            ``self._collections.values()`` (i.e., the dictionary's insertion order for
            this process), and should not be relied upon as a stable sort order across
            runs.

        Returns:
            A list of :class:`app.models.Collection` objects currently stored in this
            :class:`Storage` instance.
        """
        return list(self._collections.values())
    
    def delete_collection(self, collection_id: str) -> bool:
        """Delete a stored collection by its unique identifier.

        Removes the collection keyed by ``collection_id`` from this storage instance's
        internal collection index (``self._collections``). If no collection exists for
        the given ID, the storage remains unchanged.

        Note:
            This method only deletes the :class:`app.models.Collection` record. Any
            prompts associated with the collection are stored separately in
            ``self._prompts`` and are *not* removed. To delete those as well, call
            :meth:`delete_prompts_by_collection_id`.

        Args:
            collection_id: The unique ID of the collection to delete.

        Returns:
            ``True`` if a collection with the given ID existed in storage and was
            removed; otherwise, ``False``.
        """
        if collection_id in self._collections:
            del self._collections[collection_id]
            return True
        return False
    
    def delete_prompts_by_collection_id(self, collection_id: str) -> None:
        """Delete all prompts associated with a given collection ID.

        This method removes any entries from the in-memory prompt index
        (``self._prompts``) whose :attr:`app.models.Prompt.collection_id` matches the
        provided ``collection_id``. It is useful for cleanup when removing a
        collection (see :meth:`delete_collection`), since collections and prompts are
        stored separately in this :class:`Storage` implementation.

        To avoid mutating the underlying dictionary while iterating, the method
        first collects the prompt IDs to delete and then deletes them in a second
        pass.

        Args:
            collection_id: The collection identifier to match against each prompt's
                ``collection_id`` field.

        Returns:
            None. This method performs an in-place mutation of ``self._prompts``. If
            no prompts match the given ``collection_id``, no changes are made.
        """
        # Collect IDs of prompts to delete
        prompt_ids_to_delete = [prompt_id for prompt_id, prompt in self._prompts.items() if prompt.collection_id == collection_id]
        
        # Delete the prompts
        for prompt_id in prompt_ids_to_delete:
            del self._prompts[prompt_id]
    
    def get_prompts_by_collection(self, collection_id: str) -> List[Prompt]:
        """Return all prompts that belong to the given collection.

        This method performs an in-memory filter over the prompts stored in
        ``self._prompts`` and returns those whose :attr:`app.models.Prompt.collection_id`
        matches ``collection_id`` exactly.

        Args:
            collection_id: The collection ID to match against each prompt's
                ``collection_id`` field.

        Returns:
            A list of :class:`app.models.Prompt` instances associated with the given
            collection. If no prompts match, an empty list is returned.
        """
        return [p for p in self._prompts.values() if p.collection_id == collection_id]

    def get_prompts_by_collection_id(self, collection_id: str) -> List[Prompt]:
        """Return all prompts that belong to the given collection.

        This performs an in-memory filter over the prompts currently stored in
        ``self._prompts`` and returns those whose ``Prompt.collection_id`` matches
        the provided ``collection_id`` exactly.

        Args:
            collection_id: The collection ID to match against each prompt's
                ``collection_id`` field.

        Returns:
            A list of :class:`app.models.Prompt` instances associated with the given
            collection. If no prompts match, an empty list is returned.
        """
        return [prompt for prompt in self._prompts.values() if prompt.collection_id == collection_id]

    # ============== Versioning Operations ==============

    def create_prompt_version(self, prompt_id: str, prompt: Prompt) -> PromptVersion:
        """Create a new version of a prompt.

        Creates a new version snapshot of the prompt and updates the prompt metadata.
        If this is the first version, creates the prompt metadata as well.

        Args:
            prompt_id: The unique identifier of the prompt.
            prompt: The prompt data to store as a version.

        Returns:
            The created PromptVersion instance.
        """
        # Get current version number
        current_version = 1
        if prompt_id in self._prompt_meta:
            meta = self._prompt_meta[prompt_id]
            current_version = meta.current_version + 1

        # Create version snapshot
        version = PromptVersion(
            prompt_id=prompt_id,
            version=current_version,
            title=prompt.title,
            content=prompt.content,
            description=prompt.description,
            collection_id=prompt.collection_id,
            tags=prompt.tags
        )

        # Initialize versions list if needed
        if prompt_id not in self._prompt_versions:
            self._prompt_versions[prompt_id] = []

        # Add the version
        self._prompt_versions[prompt_id].append(version)

        # Update or create metadata
        if prompt_id in self._prompt_meta:
            meta = self._prompt_meta[prompt_id]
            meta.current_version = current_version
        else:
            meta = PromptMeta(
                id=prompt_id,
                current_version=current_version
            )
            self._prompt_meta[prompt_id] = meta

        # Update the prompt in storage with version number
        prompt.version = current_version
        self._prompts[prompt_id] = prompt

        return version

    def get_prompt_version(self, prompt_id: str, version: int) -> Optional[PromptVersion]:
        """Retrieve a specific version of a prompt.

        Args:
            prompt_id: The unique identifier of the prompt.
            version: The version number to retrieve.

        Returns:
            The PromptVersion if it exists, otherwise None.
        """
        if prompt_id not in self._prompt_versions:
            return None

        versions = self._prompt_versions[prompt_id]
        for v in versions:
            if v.version == version:
                return v
        return None

    def get_all_prompt_versions(self, prompt_id: str) -> List[PromptVersion]:
        """Retrieve all versions of a prompt.

        Args:
            prompt_id: The unique identifier of the prompt.

        Returns:
            A list of PromptVersion instances, sorted by version number (newest first).
        """
        if prompt_id not in self._prompt_versions:
            return []

        versions = self._prompt_versions[prompt_id]
        return sorted(versions, key=lambda v: v.version, reverse=True)

    def promote_prompt_version(self, prompt_id: str, version: int) -> Optional[Prompt]:
        """Promote an old version to become the new latest version.

        Creates a new version that is a copy of the specified old version.

        Args:
            prompt_id: The unique identifier of the prompt.
            version: The version number to promote.

        Returns:
            The new Prompt instance created from the promoted version, or None if
            the version doesn't exist.
        """
        old_version = self.get_prompt_version(prompt_id, version)
        if not old_version:
            return None

        # Create new version with incremented version number
        new_version_num = self._prompt_meta[prompt_id].current_version + 1

        # Create new prompt from the old version
        new_prompt = Prompt(
            id=prompt_id,
            title=old_version.title,
            content=old_version.content,
            description=old_version.description,
            collection_id=old_version.collection_id,
            tags=old_version.tags
        )

        # Create the new version
        self.create_prompt_version(prompt_id, new_prompt)

        # Return the updated prompt
        return self.get_prompt(prompt_id)
    # ============== Utility ==============
    
    def clear(self):
        """Remove all prompts and collections from in-memory storage.

        This method clears the internal dictionaries used by :class:`Storage`:
        ``self._prompts`` (mapping prompt IDs to :class:`app.models.Prompt`),
        ``self._collections`` (mapping collection IDs to :class:`app.models.Collection`),
        ``self._prompt_meta`` (prompt metadata), and ``self._prompt_versions``
        (version history).

        This is a destructive, in-memory-only operation intended for scenarios like
        tests or resetting ephemeral development state. It does not affect any
        external persistence layer (this module implements only in-memory storage).

        Returns:
            None
        """
        self._prompts.clear()
        self._collections.clear()
        self._prompt_meta.clear()
        self._prompt_versions.clear()


# Global storage instance
storage = Storage()
