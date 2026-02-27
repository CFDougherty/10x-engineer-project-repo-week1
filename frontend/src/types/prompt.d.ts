export interface Prompt {
  id: string;
  title: string;
  content: string;
  description?: string;
  tags: string[];
  created_at: string;
  updated_at: string;
  version?: string;
  collection_id?: string;
}

export interface PromptCreate {
  title: string;
  content: string;
  description?: string;
  tags?: string[];
  version?: string;
  collection_id?: string;
}

export interface PromptUpdate {
  title?: string;
  content?: string;
  description?: string;
  tags?: string[];
  version?: string;
  collection_id?: string;
}

export interface VersionSummary {
  version: number;
  created_at: string;
  title: string;
  description?: string;
}

export interface PromptVersion {
  prompt_id: string;
  version: number;
  title: string;
  content: string;
  description?: string;
  collection_id?: string;
  tags?: string[];
  created_at: string;
}

export interface VersionList {
  prompt_id: string;
  versions: VersionSummary[];
  total: number;
}
