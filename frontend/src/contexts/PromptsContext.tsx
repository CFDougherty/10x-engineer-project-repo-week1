import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { getPrompts, createPrompt, updatePrompt, deletePrompt } from '../services/apiClient';
import type { Prompt, PromptCreate, PromptUpdate } from '../types/prompt';

interface PromptsContextType {
  prompts: Prompt[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  create: (promptData: PromptCreate) => Promise<Prompt>;
  update: (id: string, promptData: PromptUpdate) => Promise<Prompt>;
  remove: (id: string) => Promise<void>;
}

const PromptsContext = createContext<PromptsContextType | undefined>(undefined);

export const PromptsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPrompts = useCallback(async () => {
    try {
      setLoading(true);
      const response = await getPrompts();
      setPrompts(response.data.prompts);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch prompts');
      console.error('Error fetching prompts:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const createNewPrompt = useCallback(async (promptData: PromptCreate) => {
    try {
      const response = await createPrompt(promptData);
      await fetchPrompts();
      return response.data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create prompt');
      throw err;
    }
  }, [fetchPrompts]);

  const updateExistingPrompt = useCallback(async (id: string, promptData: PromptUpdate) => {
    try {
      const response = await updatePrompt(id, promptData);
      await fetchPrompts();
      return response.data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update prompt');
      throw err;
    }
  }, [fetchPrompts]);

  const removePrompt = useCallback(async (id: string) => {
    try {
      await deletePrompt(id);
      await fetchPrompts();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete prompt');
      throw err;
    }
  }, [fetchPrompts]);

  useEffect(() => {
    fetchPrompts();
  }, [fetchPrompts]);

  return (
    <PromptsContext.Provider
      value={{
        prompts,
        loading,
        error,
        refetch: fetchPrompts,
        create: createNewPrompt,
        update: updateExistingPrompt,
        remove: removePrompt,
      }}
    >
      {children}
    </PromptsContext.Provider>
  );
};

export const usePrompts = () => {
  const context = useContext(PromptsContext);
  if (context === undefined) {
    throw new Error('usePrompts must be used within a PromptsProvider');
  }
  return context;
};
