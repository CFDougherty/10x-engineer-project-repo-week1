/**
 * PromptsContext — TanStack Query-backed mutations for prompts.
 *
 * The heavy lifting (paginated list, infinite scroll) lives directly in
 * PromptsPage via useInfiniteQuery.  This context/hook exposes the mutating
 * operations (create / update / remove) and a refetch helper so that
 * non-page components (e.g. Layout SSE handler) can invalidate the cache
 * without importing the full page query setup.
 */
import { useQueryClient, useMutation, useQuery } from '@tanstack/react-query';
import { createPrompt, updatePrompt, deletePrompt, getPrompts } from '../services/apiClient';
import type { PromptCreate, PromptUpdate } from '../types/prompt';

export const PROMPTS_QUERY_KEY = ['prompts'] as const;

export const usePrompts = () => {
  const queryClient = useQueryClient();

  const { data, isLoading: loading } = useQuery({
    queryKey: PROMPTS_QUERY_KEY,
    queryFn: () => getPrompts({ limit: 1000 }).then((r) => r.data.prompts),
  });

  const prompts = data ?? [];

  const refetch = () =>
    queryClient.invalidateQueries({ queryKey: PROMPTS_QUERY_KEY });

  const createMutation = useMutation({
    mutationFn: (data: PromptCreate) => createPrompt(data).then((r) => r.data),
    onSuccess: () => refetch(),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: PromptUpdate }) =>
      updatePrompt(id, data).then((r) => r.data),
    onSuccess: () => refetch(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deletePrompt(id),
    onSuccess: () => refetch(),
  });

  return {
    prompts,
    loading,
    refetch,
    create: (data: PromptCreate) => createMutation.mutateAsync(data),
    update: (id: string, data: PromptUpdate) =>
      updateMutation.mutateAsync({ id, data }),
    remove: (id: string) => deleteMutation.mutateAsync(id),
  };
};
