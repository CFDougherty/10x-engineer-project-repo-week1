"""In-memory storage for PromptLab

This module provides simple in-memory storage for prompts and collections.
In a production environment, this would be replaced with a database.
"""

from typing import Dict, List, Optional
from app.models import Prompt, Collection


class Storage:
    def __init__(self):
        """Initialize an in-memory storage container for prompts and collections.

        This constructor sets up internal dictionaries keyed by each entity's
        unique identifier. Prompts and collections are modeled by
        :class:`app.models.Prompt` and :class:`app.models.Collection`, respectively.

        The storage is intended for lightweight, ephemeral use (e.g., local
        development/testing). Data is not persisted across process restarts.

        Args:
            None

        Returns:
            None
        """
        self._prompts: Dict[str, Prompt] = {}
        self._collections: Dict[str, Collection] = {}
    
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

        Args:
            None

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

        Args:
            None

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
    # ============== Utility ==============
    
    def clear(self):
        """Remove all prompts and collections from in-memory storage.

        This method clears the internal dictionaries used by :class:`Storage`:
        ``self._prompts`` (mapping prompt IDs to :class:`app.models.Prompt`) and
        ``self._collections`` (mapping collection IDs to :class:`app.models.Collection`).

        This is a destructive, in-memory-only operation intended for scenarios like
        tests or resetting ephemeral development state. It does not affect any
        external persistence layer (this module implements only in-memory storage).

        Args:
            None

        Returns:
            None
        """
        self._prompts.clear()
        self._collections.clear()


# Global storage instance
storage = Storage()
