import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { getCollections, createCollection as apiCreateCollection, updateCollection as apiUpdateCollection, deleteCollection as apiDeleteCollection } from '../services/apiClient';
import type { Collection, CollectionCreate, CollectionUpdate } from '../types/collection';

interface CollectionsContextType {
  collections: Collection[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  create: (collectionData: CollectionCreate) => Promise<Collection>;
  update: (id: string, collectionData: CollectionUpdate) => Promise<Collection>;
  remove: (id: string) => Promise<void>;
}

const CollectionsContext = createContext<CollectionsContextType | undefined>(undefined);

export const CollectionsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
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

  const createCollection = useCallback(async (collectionData: CollectionCreate) => {
    try {
      const response = await apiCreateCollection(collectionData);
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
      const response = await apiUpdateCollection(id, collectionData);
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
      await apiDeleteCollection(id);
      setCollections(prev => prev.filter(collection => collection.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete collection');
      throw err;
    }
  }, []);

  useEffect(() => {
    fetchCollections();
  }, [fetchCollections]);

  return (
    <CollectionsContext.Provider
      value={{
        collections,
        loading,
        error,
        refetch: fetchCollections,
        create: createCollection,
        update: updateExistingCollection,
        remove: removeCollection,
      }}
    >
      {children}
    </CollectionsContext.Provider>
  );
};

export const useCollections = () => {
  const context = useContext(CollectionsContext);
  if (context === undefined) {
    throw new Error('useCollections must be used within a CollectionsProvider');
  }
  return context;
};