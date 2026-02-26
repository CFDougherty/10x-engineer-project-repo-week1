import { useState, useEffect, useCallback } from 'react';
import { getPrompts, createPrompt, updatePrompt, deletePrompt } from '../services/apiClient';
import type { Prompt, PromptCreate, PromptUpdate } from '../types/prompt';

export const usePrompts = () => {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPrompts = useCallback(async () => {
    try {
      setLoading(true);
      const response = await getPrompts();
      setPrompts(response.data);
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
      setPrompts(prev => [...prev, response.data]);
      return response.data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create prompt');
      throw err;
    }
  }, []);

  const updateExistingPrompt = useCallback(async (id: string, promptData: PromptUpdate) => {
    try {
      const response = await updatePrompt(id, promptData);
      setPrompts(prev => prev.map(prompt =>
        prompt.id === id ? response.data : prompt
      ));
      return response.data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update prompt');
      throw err;
    }
  }, []);

  const removePrompt = useCallback(async (id: string) => {
    try {
      await deletePrompt(id);
      setPrompts(prev => prev.filter(prompt => prompt.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete prompt');
      throw err;
    }
  }, []);

  useEffect(() => {
    fetchPrompts();
  }, [fetchPrompts]);

  return {
    prompts,
    loading,
    error,
    refetch: fetchPrompts,
    create: createNewPrompt,
    update: updateExistingPrompt,
    remove: removePrompt,
  };
};