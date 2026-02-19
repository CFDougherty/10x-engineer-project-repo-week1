# Tagging System — Feature Specification

## Overview
PromptLab currently supports organizing prompts via `collections`, but collections are a single-parent grouping (a prompt has at most one `collection_id`). Users often want cross-cutting organization such as:

- “customer-support”, “marketing”, “legal-review”
- “draft”, “approved”, “experimental”
- “gpt-4o”, “claude”, “evaluation-needed”

This spec defines a **tagging system** allowing prompts to have **zero or many tags**.

## Goals
- Allow creating and managing tags.
- Allow assigning/removing tags on prompts.
- Allow filtering/searching prompts by tag(s).
- Keep tags lightweight (simple name + optional description).

## Non-goals
- No hierarchical tags (no parent/child) in this iteration.
- No tag synonyms/aliases.
- No RBAC/permissions.

## Definitions
- **Tag**: A reusable label.
- **Tagged prompt**: A prompt associated with one or more tags.

## User Stories
- As a user, I can add tags to a prompt so I can find it later.
- As a user, I can filter prompts to those tagged “approved”.
- As a user, I can see all tags and how many prompts use each tag.

## Data Model

### Tag
- `id` (uuid)
- `name` (string, unique case-insensitively)
- `description` (string | null)
- `created_at` (datetime)

### PromptTag (association)
Many-to-many relationship between prompts and tags.

For in-memory storage, maintain an index like:
- `prompt_tags: Dict[prompt_id, Set[tag_id]]`
- and optionally `tag_prompts: Dict[tag_id, Set[prompt_id]]` for faster reverse lookups.

### Prompt response shape changes (proposal)
Add a `tags` field to prompt responses:
- `tags: Tag[]` (expanded objects)

Alternative: return `tag_ids: string[]` and provide separate endpoints for tag details.

## API Changes

### New endpoints

#### POST `/tags`
Create a tag.

**Request body**
```json
{ "name": "approved", "description": "Reviewed and approved for use" }
```

**Response — 201**
```json
{ "id": "...", "name": "approved", "description": "...", "created_at": "..." }
```

**Validation / errors**
- `409 Conflict` if tag name already exists (case-insensitive)

#### GET `/tags`
List tags.

**Response — 200**
```json
{ "tags": [/* Tag[] */], "total": 0 }
```

(Optional enhancement)
- include `usage_count` for each tag.

#### GET `/tags/{tag_id}`
Fetch one tag.

#### DELETE `/tags/{tag_id}`
Delete a tag.

**Behavior**
- Removing a tag also removes all associations with prompts.

### Prompt tagging endpoints

#### POST `/prompts/{prompt_id}/tags/{tag_id}`
Assign tag to prompt (idempotent).

- Success: `204 No Content` (recommended) or return updated Prompt.
- Errors:
  - `404` if prompt not found
  - `404` if tag not found

#### DELETE `/prompts/{prompt_id}/tags/{tag_id}`
Remove tag from prompt (idempotent).

### Filtering prompts by tags

#### GET `/prompts?tag_id=<tag_id>`
Filter prompts that include a tag.

#### GET `/prompts?tag=<tag_name>`
Filter prompts by tag name (case-insensitive exact match).

#### Multiple tags
Decide semantics:
- AND semantics: prompt must include *all* tags
  - `GET /prompts?tag=approved&tag=marketing`
- OR semantics: prompt includes *any* of the tags
  - `GET /prompts?tags_any=approved,marketing`

**Recommendation (simple)**
- Implement AND semantics for repeated `tag` params first.

## Validation Rules
- Tag name:
  - 1–50 chars
  - lowercase normalization recommended for uniqueness (store original casing if desired)
  - allowed characters: letters, digits, hyphen, underscore (decide)
- Tag description max 500 chars

## Storage / Persistence (current in-memory)
- Add `Storage` methods:
  - `create_tag`, `get_tag`, `get_all_tags`, `delete_tag`
  - `add_tag_to_prompt`, `remove_tag_from_prompt`
  - `get_prompts_by_tag_id`

## Edge Cases
- Deleting a prompt should remove prompt→tag associations.
- Deleting a tag should remove all prompt associations.
- If prompt versioning is implemented:
  - Decide whether tags apply to the logical prompt or per-version.
  - Recommendation: tags apply to the logical prompt (not per-version) for simplicity.

## Testing Plan
- Create tag; cannot create duplicate (case-insensitive).
- Assign/remove tag to prompt.
- Filtering by tag returns only tagged prompts.
- Deleting a tag removes associations.

## Acceptance Criteria
- Tags can be created, listed, fetched, and deleted.
- Prompts can be tagged and untagged.
- Prompt listing supports filtering by at least one tag.
- API docs updated in `docs/API_REFERENCE.md`.

## Open Questions
- Should tags be unique by slugified name or exact name?
- Should prompt responses expand tags or return only IDs?
- Should we support usage counts in `GET /tags`?
