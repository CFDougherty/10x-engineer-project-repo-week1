import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Prompt API endpoints
export const getPrompts = (params?: {
  page?: number;
  limit?: number;
  collection?: string;
  search?: string;
  sort?: string;
}) => apiClient.get('/prompts', { params });

export const getPromptById = (id: string) => apiClient.get(`/prompts/${id}`);

export const createPrompt = (promptData: any) => apiClient.post('/prompts', promptData);

export const updatePrompt = (id: string, promptData: any) =>
  apiClient.put(`/prompts/${id}`, promptData);

export const patchPrompt = (id: string, promptData: any) =>
  apiClient.patch(`/prompts/${id}`, promptData);

export const deletePrompt = (id: string) => apiClient.delete(`/prompts/${id}`);

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