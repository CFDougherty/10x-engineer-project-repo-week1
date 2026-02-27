import { useState, useEffect, useCallback } from 'react';
import { getCollections, createCollection, updateCollection, deleteCollection } from '../services/apiClient';
import type { Collection, CollectionCreate, CollectionUpdate } from '../types/collection';

export const useCollections = () => {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCollections = useCallback(async () => {
    try {
      setLoading(true);
      const response = await getCollections();
      setCollections(response.data.collections || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch collections');
      console.error('Error fetching collections:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const createNewCollection = useCallback(async (collectionData: CollectionCreate) => {
    try {
      const response = await createCollection(collectionData);
      // Refetch collections to ensure consistency
      await fetchCollections();
      return response.data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create collection');
      throw err;
    }
  }, [fetchCollections]);

  const updateExistingCollection = useCallback(async (id: string, collectionData: CollectionUpdate) => {
    try {
      const response = await updateCollection(id, collectionData);
      setCollections(prev => prev.map(collection =>
        collection.id === id ? response.data : collection
      ));
      return response.data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update collection');
      throw err;
    }
  }, []);

  const removeCollection = useCallback(async (id: string) => {
    try {
      await deleteCollection(id);
      setCollections(prev => prev.filter(collection => collection.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete collection');
      throw err;
    }
  }, []);

  useEffect(() => {
    fetchCollections();
  }, [fetchCollections]);

  return {
    collections,
    loading,
    error,
    refetch: fetchCollections,
    create: createNewCollection,
    update: updateExistingCollection,
    remove: removeCollection,
  };
};