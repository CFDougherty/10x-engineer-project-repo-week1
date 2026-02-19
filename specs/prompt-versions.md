# Prompt Versions — Feature Specification

## Overview
PromptLab currently stores prompts as single mutable resources. Updating a prompt overwrites its content, which makes it difficult to:

- track changes over time
- revert to a previous revision
- compare versions
- promote a “tested” version to production

This spec defines a **prompt versioning system** that preserves historical versions while keeping the API simple for common CRUD operations.

## Goals
- Preserve a complete history of prompt changes.
- Allow retrieving a prompt at a specific version.
- Allow listing version history for a prompt.
- Allow “promoting” an older version to become the latest version.
- Keep the default `/prompts` and `/prompts/{id}` behavior focused on “latest”.

## Non-goals
- No branching/merging (Git-like) workflows in this iteration.
- No diff viewer UI (API may provide enough data to build one later).
- No permissions/audit attribution beyond timestamps (no `updated_by` yet).

## Definitions
- **Prompt (logical prompt)**: The stable identifier users interact with (e.g., “Summarize content”).
- **Prompt Version**: An immutable snapshot of prompt fields (content, title, etc.) at a moment in time.
- **Latest Version**: The most recent version for a prompt.

## User Stories
- As a user, I can update a prompt but still view its past versions.
- As a user, I can fetch version `n` of a prompt to reproduce previous outputs.
- As a user, I can roll back to a previous version if a new version performs worse.

## Data Model

### Option A (recommended): Separate `Prompt` and `PromptVersion`
Introduce two entities:

#### Prompt
- `id` (uuid)
- `current_version` (int) — points to latest version number
- `created_at` (datetime)

#### PromptVersion
- `prompt_id` (uuid)
- `version` (int) — starts at 1 and increments by 1
- `title` (string)
- `content` (string)
- `description` (string | null)
- `collection_id` (uuid | null)
- `created_at` (datetime) — time the version snapshot was created

**Constraints**
- `(prompt_id, version)` is unique.
- Versions are immutable once created.

### Backward compatibility with existing `Prompt` model
Currently, `Prompt` includes mutable fields + `updated_at`. With versioning:
- `GET /prompts/{prompt_id}` returns the **latest** version fields plus metadata.
- `updated_at` can either:
  - represent the latest version timestamp, or
  - be removed from the “logical prompt” in favor of version timestamps.

## API Changes

### Existing endpoints (behavior changes)

#### POST `/prompts`
Creates a new logical prompt and version `1`.

**Request** (same as today): `PromptCreate`

**Response** (proposal): latest-version representation, including version metadata.

Example response:
```json
{
  "id": "<prompt_id>",
  "version": 1,
  "title": "Summarize content",
  "content": "Summarize: {{input}}",
  "description": null,
  "collection_id": null,
  "created_at": "...",
  "updated_at": "..."
}
```

#### PUT `/prompts/{prompt_id}`
Instead of overwriting in place, creates a **new version** (`current_version + 1`) with the provided fields.

#### PATCH `/prompts/{prompt_id}`
Also creates a **new version** containing the merged updates.

> Note: This preserves the mental model that updates change “the prompt”, while implementing immutability under the hood.

### New endpoints

#### GET `/prompts/{prompt_id}/versions`
List all versions (newest first).

**Response**
```json
{
  "prompt_id": "<prompt_id>",
  "versions": [
    {
      "version": 3,
      "created_at": "...",
      "title": "...",
      "description": "..."
    }
  ],
  "total": 3
}
```

#### GET `/prompts/{prompt_id}/versions/{version}`
Fetch a specific version snapshot.

**Response**
Same shape as “Prompt latest”, but pinned to `version`.

#### POST `/prompts/{prompt_id}/versions/{version}/promote`
Set an older version as the latest by creating a new version copying that snapshot.

**Rationale**: promotion remains append-only (history preserved).

## Storage / Persistence (current in-memory)
- Add internal indexes:
  - `prompts: Dict[prompt_id, PromptMeta]`
  - `prompt_versions: Dict[prompt_id, List[PromptVersion]]`
- Ensure version increments are atomic within the in-memory process.

## Edge Cases
- Deleting a prompt:
  - Decide whether it deletes all versions (likely yes).
- Collection deletion:
  - If a collection is deleted, decide what happens to `collection_id` in historical versions.
    - Recommended: preserve historical `collection_id` values even if the collection no longer exists, but treat it as a dangling reference.

## Validation Rules
- `title` length 1–200
- `description` max 500
- `content` min length 1
- `collection_id`, if provided, must refer to an existing collection at the time a new version is created (current behavior).

## Testing Plan
- Creating prompt creates version 1.
- Updating prompt creates version 2 and increments current_version.
- Fetching a specific version returns correct snapshot.
- Promoting version creates a new version identical to promoted snapshot.
- Listing versions returns correct ordering.

## Acceptance Criteria
- Version history is preserved across updates.
- API supports list + fetch-by-version.
- Default “prompt” endpoints return latest version.
- All new/changed endpoints are documented in `docs/API_REFERENCE.md`.

## Open Questions
- Should version numbers be strictly sequential integers or allow semantic versions?
- Should we expose both logical prompt metadata and version snapshot separately?
- Should PATCH always create a new version even if no fields changed?
