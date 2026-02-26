export interface Prompt {
  id: string;
  title: string;
  content: string;
  tags: string[];
  created_at: string;
  updated_at: string;
  version?: string;
  collection_id?: string;
}

export interface PromptCreate {
  title: string;
  content: string;
  tags?: string[];
  version?: string;
  collection_id?: string;
}

export interface PromptUpdate {
  title?: string;
  content?: string;
  tags?: string[];
  version?: string;
  collection_id?: string;
}
