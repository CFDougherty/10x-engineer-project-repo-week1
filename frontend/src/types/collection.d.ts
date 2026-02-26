export interface Collection {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  prompt_ids?: string[];
}

export interface CollectionCreate {
  name: string;
  description?: string;
  prompt_ids?: string[];
}

export interface CollectionUpdate {
  name?: string;
  description?: string;
  prompt_ids?: string[];
}