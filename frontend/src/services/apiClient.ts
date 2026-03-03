import axios from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface PromptsResponse {
  prompts: any[];
  total: number;
  next_cursor: string | null;
}

// Prompt API endpoints
export const getPrompts = (params?: {
  limit?: number;
  cursor?: string;       // keyset pagination token (preferred over offset)
  offset?: number;       // legacy SQL offset
  collection_id?: string;
  search?: string;
  filter?: string;       // 'title' | 'description' | 'tags' | 'content' | 'collection' | 'all'
  fuzzy?: boolean;
  semantic?: boolean;
}) => apiClient.get<PromptsResponse>('/prompts', { params });

export const getPromptById = (id: string) => apiClient.get(`/prompts/${id}`);

export const createPrompt = (promptData: any) => apiClient.post('/prompts', promptData);

export const updatePrompt = (id: string, promptData: any) =>
  apiClient.put(`/prompts/${id}`, promptData);

export const patchPrompt = (id: string, promptData: any) =>
  apiClient.patch(`/prompts/${id}`, promptData);

export const deletePrompt = (id: string) => apiClient.delete(`/prompts/${id}`);

// Version history API endpoints
export const getPromptVersions = (promptId: string) =>
  apiClient.get(`/prompts/${promptId}/versions`);

export const getPromptVersion = (promptId: string, version: number) =>
  apiClient.get(`/prompts/${promptId}/versions/${version}`);

export const promotePromptVersion = (promptId: string, version: number) =>
  apiClient.post(`/prompts/${promptId}/versions/${version}/promote`);

// Collection API endpoints
export const getCollections = () => apiClient.get('/collections');

export const getCollectionById = (id: string) => apiClient.get(`/collections/${id}`);

export const createCollection = (collectionData: any) =>
  apiClient.post('/collections', collectionData);

export const updateCollection = (id: string, collectionData: any) =>
  apiClient.put(`/collections/${id}`, collectionData);

export const deleteCollection = (id: string) => apiClient.delete(`/collections/${id}`);

// Add prompt to collection
export const addPromptToCollection = (collectionId: string, promptId: string) =>
  apiClient.post(`/collections/${collectionId}/prompts`, { prompt_id: promptId });

// Remove prompt from collection
export const removePromptFromCollection = (collectionId: string, promptId: string) =>
  apiClient.delete(`/collections/${collectionId}/prompts/${promptId}`);

// Admin API endpoints
export interface PopulateConfig {
  num_prompts: number;
  num_collections: number;
  collection_chance: number;
  tags_per_prompt: number;
  random_seed?: number | null;
  tag_as_test_fill: boolean;
  append_mode: boolean;
}

export interface PopulateProgress {
  current: number;
  total: number;
  active: boolean;
  error: string | null;
}

export const populateTestData = (config: PopulateConfig) =>
  apiClient.post('/admin/populate-test-data', config);

export const getPopulateStatus = () =>
  apiClient.get<PopulateProgress>('/admin/populate-status');

export const clearTestData = () => apiClient.delete('/admin/clear-test-data');

export const clearAllData = () => apiClient.delete('/admin/clear-all-data');

export const getEmbeddingStatus = () =>
  apiClient.get<{ total: number; embedded: number; complete: boolean }>('/admin/embedding-status');

export const backfillEmbeddings = () => apiClient.post('/admin/backfill-embeddings');