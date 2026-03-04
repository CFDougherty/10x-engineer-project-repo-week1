# PromptLab API Reference

Base URL (local): `http://localhost:8000`

- Swagger UI: `GET /docs`
- OpenAPI JSON: `GET /openapi.json`
- Content type: JSON (`Content-Type: application/json`)
- Auth: none
- Storage: PostgreSQL (data persists across restarts)

---

## Conventions

### IDs
All resource IDs (`prompt_id`, `collection_id`) are server-generated UUIDv4 strings.

### Timestamps
Timestamps are generated with `datetime.utcnow()` and serialized as ISO-8601 strings **without** a timezone offset (treat them as UTC), e.g.:

- `2026-02-18T18:24:20.454842`

---

## Error handling

PromptLab uses two error formats:

### 1) Application errors (`HTTPException`)
Used for domain errors like “not found” or “invalid collection”.

**Format**

```json
{ "detail": "<message>" }
```

**Examples**

- `404 Not Found`

```json
{ "detail": "Prompt not found" }
```

- `400 Bad Request`

```json
{ "detail": "Collection not found" }
```

### 2) Validation errors (FastAPI / Pydantic)
Used when request bodies or parameters fail schema validation.

- Status code: `400 Bad Request`
- Typical causes:
  - missing required fields (`title`, `content`, `name`)
  - field length constraints (e.g., `title` max 200)

**Format**

```json
{ "detail": "Validation error: <message>" }
```

**Example** (missing required `title`)

```json
{ "detail": "Validation error: Field required" }
```

---

## Data models

### Prompt

#### PromptCreate (request body)

| Field | Type | Required | Constraints |
|---|---|---:|---|
| `title` | string | yes | 1–200 chars |
| `content` | string | yes | min 1 char |
| `description` | string \| null | no | max 500 chars |
| `collection_id` | string \| null | no | must reference an existing collection if provided |
| `tags` | string[] \| null | no | each tag must be a non-empty string |

#### PromptUpdate (request body for PUT)
Same shape as `PromptCreate`.

#### PromptUpdateOptional (request body for PATCH)
All fields optional. Empty or whitespace-only strings are normalized to `null`.

#### Prompt (response)

```json
{
  "id": "d010f7fa-10a5-4d1f-9b16-2dc2c75eafd3",
  "title": "Summarize content",
  "content": "Summarize: {{input}}",
  "description": "General-purpose summarization prompt",
  "collection_id": "50ab7cc9-eed7-414d-8f23-1b19e20683f8",
  "tags": ["summarize", "general"],
  "version": 1,
  "created_at": "2026-02-18T18:24:20.454842",
  "updated_at": "2026-02-18T18:24:20.454844"
}
```

### Collection

#### CollectionCreate (request body)

| Field | Type | Required | Constraints |
|---|---|---:|---|
| `name` | string | yes | 1–100 chars |
| `description` | string \| null | no | max 500 chars |

#### CollectionUpdateOptional (request body for PATCH)

All fields optional. Empty or whitespace-only strings are normalized to `null`.

#### Collection (response)

```json
{
  "id": "50ab7cc9-eed7-414d-8f23-1b19e20683f8",
  "name": "Onboarding",
  "description": "Prompts used during onboarding",
  "prompt_ids": ["d010f7fa-10a5-4d1f-9b16-2dc2c75eafd3"],
  "created_at": "2026-02-18T19:51:56.546992"
}
```

### Versioning Models

#### PromptVersion (response)

```json
{
  "prompt_id": "d010f7fa-10a5-4d1f-9b16-2dc2c75eafd3",
  "version": 1,
  "title": "Summarize content",
  "content": "Summarize: {{input}}",
  "description": "General-purpose summarization prompt",
  "collection_id": "50ab7cc9-eed7-414d-8f23-1b19e20683f8",
  "created_at": "2026-02-18T18:24:20.454842"
}
```

#### VersionSummary (response)

```json
{
  "version": 1,
  "created_at": "2026-02-18T18:24:20.454842",
  "title": "Summarize content",
  "description": "General-purpose summarization prompt"
}
```

#### VersionList (response)

```json
{
  "prompt_id": "d010f7fa-10a5-4d1f-9b16-2dc2c75eafd3",
  "versions": [
    {
      "version": 2,
      "created_at": "2026-02-18T19:00:00.000000",
      "title": "Summarize content (v2)",
      "description": "Updated version"
    },
    {
      "version": 1,
      "created_at": "2026-02-18T18:24:20.454842",
      "title": "Summarize content",
      "description": "General-purpose summarization prompt"
    }
  ],
  "total": 2
}
```

### List wrappers

#### PromptList (response)

```json
{
  "prompts": [/* Prompt[] */],
  "total": 0,
  "next_cursor": null
}
```

`next_cursor` is a base64-encoded keyset pagination token. Pass it as `cursor=<value>` in the next request to retrieve the following page. `null` when on the last page.

#### CollectionList (response)

```json
{
  "collections": [/* Collection[] */],
  "total": 0
}
```

---

## Endpoints

### Documentation

#### GET `/docs`
Interactive Swagger UI for exploring and testing the API in a browser.

**Request**

- No parameters
- No body

**curl**

```bash
curl -sS -i http://localhost:8000/docs
```

**fetch**

```javascript
const res = await fetch('http://localhost:8000/docs');
const html = await res.text();
console.log(res.status);
console.log(html.slice(0, 200));
```

**Success response — 200**

- Content-Type: `text/html; charset=utf-8`

**Response body (truncated example)**

```html
<!DOCTYPE html>
<html>
  <head>
    <link type="text/css" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@.../swagger-ui.css">
    <title>PromptLab API - Swagger UI</title>
    <!-- ... -->
  </head>
  <body>
    <div id="swagger-ui"></div>
    <!-- ... -->
  </body>
</html>
```

---

#### GET `/openapi.json`
OpenAPI schema (JSON) for the running API.

**Request**

- No parameters
- No body

**curl**

```bash
curl -sS http://localhost:8000/openapi.json
```

**fetch**

```javascript
const res = await fetch('http://localhost:8000/openapi.json');
const schema = await res.json();
console.log(schema.openapi);
console.log(Object.keys(schema.paths));
```

**Success response — 200**

**Response body (sample)**

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "PromptLab API",
    "version": "0.1.0"
  },
  "paths": {
    "/health": {
      "get": {
        "responses": {
          "200": {
            "description": "Successful Response"
          }
        }
      }
    }
  }
}
```

---

### Health

#### GET `/health`
Returns a simple health indicator plus the running app version.

**Request**

- No parameters
- No body

**curl**

```bash
curl -sS http://localhost:8000/health
```

**fetch**

```javascript
const res = await fetch('http://localhost:8000/health');
const data = await res.json();
console.log(data);
```

**Success response — 200**

```json
{ "status": "healthy", "version": "0.1.0" }
```

**Errors**

- `500 Internal Server Error` (unexpected)

---

### Prompts

#### GET `/prompts`
List prompts.

**Query parameters**

| Name | Type | Required | Default | Description |
|---|---|---:|---|---|
| `collection_id` | string | no | — | Filter prompts by exact `collection_id` |
| `search` | string | no | — | Search query matched against prompt fields |
| `filter` | string | no | `'all'` | Restrict search to a specific field. One of: `'title'`, `'description'`, `'content'`, `'tags'`, `'collection'`, or `'all'` |
| `fuzzy` | bool | no | `true` | `true` = pg_trgm trigram similarity; `false` = exact case-insensitive substring match |
| `semantic` | bool | no | `false` | `true` = pgvector cosine-distance search using embeddings (ignores `search`/`filter`/`fuzzy` when active) |
| `limit` | int | no | — | Maximum number of results to return per page |
| `cursor` | string | no | — | Keyset pagination cursor from `next_cursor` in a previous response |
| `offset` | int | no | `0` | Offset-based pagination — number of results to skip (alternative to `cursor`) |

**curl**

```bash
# List all prompts
curl -sS "http://localhost:8000/prompts"

# Filter by collection
curl -sS "http://localhost:8000/prompts?collection_id=<collection_id>"

# Search with fuzzy matching (default)
curl -sS "http://localhost:8000/prompts?search=summarize"

# Search with exact substring match
curl -sS "http://localhost:8000/prompts?search=summarize&fuzzy=false"

# Semantic search
curl -sS "http://localhost:8000/prompts?search=summarize&semantic=true"

# Paginate
curl -sS "http://localhost:8000/prompts?limit=10"
curl -sS "http://localhost:8000/prompts?limit=10&cursor=<next_cursor>"
```

**fetch**

```javascript
const params = new URLSearchParams({ search: 'summarize' });
const res = await fetch(`http://localhost:8000/prompts?${params.toString()}`);
const data = await res.json();
console.log(data);
```

**Success response — 200**

```json
{
  "prompts": [
    {
      "id": "d010f7fa-10a5-4d1f-9b16-2dc2c75eafd3",
      "title": "Summarize content",
      "content": "Summarize: {{input}}",
      "description": "General-purpose summarization prompt",
      "collection_id": null,
      "tags": ["summarize", "general"],
      "version": 1,
      "created_at": "2026-02-18T18:24:20.454842",
      "updated_at": "2026-02-18T18:24:20.454844"
    }
  ],
  "total": 1,
  "next_cursor": null
}
```

Note: `content` is truncated to 300 characters in list responses. Use `GET /prompts/{prompt_id}` to retrieve the full content.

**Errors**

- `500 Internal Server Error` (unexpected)

---

#### GET `/prompts/{prompt_id}`
Fetch a single prompt by ID.

**Path parameters**

| Name | Type | Required | Description |
|---|---|---:|---|
| `prompt_id` | string | yes | Prompt UUID |

**curl**

```bash
curl -sS "http://localhost:8000/prompts/<prompt_id>"
```

**fetch**

```javascript
const promptId = '<prompt_id>';
const res = await fetch(`http://localhost:8000/prompts/${promptId}`);
if (!res.ok) throw new Error(await res.text());
console.log(await res.json());
```

**Success response — 200**

```json
{
  "id": "d010f7fa-10a5-4d1f-9b16-2dc2c75eafd3",
  "title": "Summarize content",
  "content": "Summarize: {{input}}",
  "description": "General-purpose summarization prompt",
  "collection_id": null,
  "tags": ["summarize", "general"],
  "version": 1,
  "created_at": "2026-02-18T18:24:20.454842",
  "updated_at": "2026-02-18T18:24:20.454844"
}
```

**Errors**

- `404 Not Found`

```json
{ "detail": "Prompt not found" }
```

---

#### POST `/prompts`
Create a new prompt.

**Request body**: `PromptCreate`

**curl**

```bash
curl -sS -X POST "http://localhost:8000/prompts" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Summarize content",
    "content": "Summarize the following: {{input}}",
    "description": "General-purpose summarization prompt",
    "collection_id": null
  }'
```

**fetch**

```javascript
const res = await fetch('http://localhost:8000/prompts', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    title: 'Summarize content',
    content: 'Summarize the following: {{input}}',
    description: 'General-purpose summarization prompt',
    collection_id: null,
  }),
});

if (!res.ok) throw new Error(await res.text());
console.log(await res.json());
```

**Success response — 201**

```json
{
  "id": "d010f7fa-10a5-4d1f-9b16-2dc2c75eafd3",
  "title": "Summarize content",
  "content": "Summarize the following: {{input}}",
  "description": "General-purpose summarization prompt",
  "collection_id": null,
  "tags": null,
  "version": 1,
  "created_at": "2026-02-18T18:24:20.454842",
  "updated_at": "2026-02-18T18:24:20.454844"
}
```

**Errors**

- `400 Bad Request` (when `collection_id` is provided but does not exist)

```json
{ "detail": "Collection not found" }
```

- `400 Bad Request` (invalid body; example: missing `title`)

```json
{ "detail": "Validation error: Field required" }
```

---

#### PUT `/prompts/{prompt_id}`
Replace (fully update) an existing prompt.

Notes:
- `PUT` is a **full replace**.
- You must include required fields (`title`, `content`).
- If you omit optional fields like `description` or `collection_id`, they will be set to `null`.

**Path parameters**

| Name | Type | Required | Description |
|---|---|---:|---|
| `prompt_id` | string | yes | Prompt UUID |

**curl**

```bash
curl -sS -X PUT "http://localhost:8000/prompts/<prompt_id>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Summarize content (v2)",
    "content": "Summarize: {{input}}\n\nKeep it under 5 bullets.",
    "description": "Updated constraints",
    "collection_id": null
  }'
```

**fetch**

```javascript
const promptId = '<prompt_id>';

const res = await fetch(`http://localhost:8000/prompts/${promptId}`, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    title: 'Summarize content (v2)',
    content: 'Summarize: {{input}}\n\nKeep it under 5 bullets.',
    description: 'Updated constraints',
    collection_id: null,
  }),
});

if (!res.ok) throw new Error(await res.text());
console.log(await res.json());
```

**Success response — 200**

```json
{
  "id": "d010f7fa-10a5-4d1f-9b16-2dc2c75eafd3",
  "title": "Summarize content (v2)",
  "content": "Summarize: {{input}}\n\nKeep it under 5 bullets.",
  "description": "Updated constraints",
  "collection_id": null,
  "tags": null,
  "version": 2,
  "created_at": "2026-02-18T18:24:20.454842",
  "updated_at": "2026-02-18T18:30:01.123456"
}
```

**Errors**

- `404 Not Found`

```json
{ "detail": "Prompt not found" }
```

- `400 Bad Request` (when `collection_id` is provided but does not exist)

```json
{ "detail": "Collection not found" }
```

- `400 Bad Request` (invalid body; example: missing `content`)

```json
{ "detail": "Validation error: Field required" }
```

---

#### PATCH `/prompts/{prompt_id}`
Partially update an existing prompt.

Notes:
- Only fields you send are updated; omitted fields remain unchanged.
- Empty or whitespace-only strings are normalized to `null`.
- Sending an empty JSON object (`{}`) returns the prompt unchanged.

**Path parameters**

| Name | Type | Required | Description |
|---|---|---:|---|
| `prompt_id` | string | yes | Prompt UUID |

**Request body**: `PromptUpdateOptional`

**curl**

```bash
curl -sS -X PATCH "http://localhost:8000/prompts/<prompt_id>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Summarize content (patched)",
    "description": ""
  }'
```

**fetch**

```javascript
const promptId = '<prompt_id>';

const res = await fetch(`http://localhost:8000/prompts/${promptId}`, {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    title: 'Summarize content (patched)',
    description: '', // whitespace/empty strings are normalized to null
  }),
});

if (!res.ok) throw new Error(await res.text());
console.log(await res.json());
```

**Success response — 200**

```json
{
  "id": "d010f7fa-10a5-4d1f-9b16-2dc2c75eafd3",
  "title": "Summarize content (patched)",
  "content": "Summarize: {{input}}",
  "description": null,
  "collection_id": null,
  "tags": ["summarize", "general"],
  "version": 2,
  "created_at": "2026-02-18T18:24:20.454842",
  "updated_at": "2026-02-18T18:35:10.000000"
}
```

**Errors**

- `404 Not Found`

```json
{ "detail": "Prompt not found" }
```

- `400 Bad Request` (when `collection_id` is provided but does not exist)

```json
{ "detail": "Collection not found" }
```

- `400 Bad Request` (invalid body; example: wrong type)

```json
{ "detail": "Validation error: Input should be a valid string" }
```

---

#### DELETE `/prompts/{prompt_id}`
Delete a prompt by ID.

**Path parameters**

| Name | Type | Required | Description |
|---|---|---:|---|
| `prompt_id` | string | yes | Prompt UUID |

**curl**

```bash
curl -sS -X DELETE "http://localhost:8000/prompts/<prompt_id>" -i
```

**fetch**

```javascript
const promptId = '<prompt_id>';

const res = await fetch(`http://localhost:8000/prompts/${promptId}`, {
  method: 'DELETE',
});

if (res.status !== 204) throw new Error(await res.text());
```

**Success response — 204**

No response body.

**Errors**

- `404 Not Found`

```json
{ "detail": "Prompt not found" }
```

---

### Collections

#### GET `/collections`
List collections.

**curl**

```bash
curl -sS "http://localhost:8000/collections"
```

**fetch**

```javascript
const res = await fetch('http://localhost:8000/collections');
const data = await res.json();
console.log(data);
```

**Success response — 200**

```json
{
  "collections": [
    {
      "id": "50ab7cc9-eed7-414d-8f23-1b19e20683f8",
      "name": "Onboarding",
      "description": "Prompts used during onboarding",
      "prompt_ids": ["d010f7fa-10a5-4d1f-9b16-2dc2c75eafd3"],
      "created_at": "2026-02-18T19:51:56.546992"
    }
  ],
  "total": 1
}
```

**Errors**

- `500 Internal Server Error` (unexpected)

---

#### GET `/collections/{collection_id}`
Fetch a single collection by ID.

**Path parameters**

| Name | Type | Required | Description |
|---|---|---:|---|
| `collection_id` | string | yes | Collection UUID |

**curl**

```bash
curl -sS "http://localhost:8000/collections/<collection_id>"
```

**fetch**

```javascript
const collectionId = '<collection_id>';
const res = await fetch(`http://localhost:8000/collections/${collectionId}`);
if (!res.ok) throw new Error(await res.text());
console.log(await res.json());
```

**Success response — 200**

```json
{
  "id": "50ab7cc9-eed7-414d-8f23-1b19e20683f8",
  "name": "Onboarding",
  "description": "Prompts used during onboarding",
  "prompt_ids": ["d010f7fa-10a5-4d1f-9b16-2dc2c75eafd3"],
  "created_at": "2026-02-18T19:51:56.546992"
}
```

**Errors**

- `404 Not Found`

```json
{ "detail": "Collection not found" }
```

---

#### POST `/collections`
Create a new collection.

**Request body**: `CollectionCreate`

**curl**

```bash
curl -sS -X POST "http://localhost:8000/collections" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Onboarding",
    "description": "Prompts used during onboarding"
  }'
```

**fetch**

```javascript
const res = await fetch('http://localhost:8000/collections', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'Onboarding',
    description: 'Prompts used during onboarding',
  }),
});

if (!res.ok) throw new Error(await res.text());
console.log(await res.json());
```

**Success response — 201**

```json
{
  "id": "50ab7cc9-eed7-414d-8f23-1b19e20683f8",
  "name": "Onboarding",
  "description": "Prompts used during onboarding",
  "prompt_ids": [],
  "created_at": "2026-02-18T19:51:56.546992"
}
```

**Errors**

- `400 Bad Request` (invalid body; example: missing `name`)

```json
{ "detail": "Validation error: Field required" }
```

---

#### PUT `/collections/{collection_id}`
Replace (fully update) an existing collection.

**Path parameters**

| Name | Type | Required | Description |
|---|---|---:|---|
| `collection_id` | string | yes | Collection UUID |

**Request body**: `CollectionCreate`

**curl**

```bash
curl -sS -X PUT "http://localhost:8000/collections/<collection_id>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Onboarding Updated",
    "description": "Updated description for onboarding prompts"
  }'
```

**fetch**

```javascript
const collectionId = '<collection_id>';

const res = await fetch(`http://localhost:8000/collections/${collectionId}`, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'Onboarding Updated',
    description: 'Updated description for onboarding prompts',
  }),
});

if (!res.ok) throw new Error(await res.text());
console.log(await res.json());
```

**Success response — 200**

```json
{
  "id": "50ab7cc9-eed7-414d-8f23-1b19e20683f8",
  "name": "Onboarding Updated",
  "description": "Updated description for onboarding prompts",
  "prompt_ids": ["d010f7fa-10a5-4d1f-9b16-2dc2c75eafd3"],
  "created_at": "2026-02-18T19:51:56.546992"
}
```

**Errors**

- `404 Not Found`

```json
{ "detail": "Collection not found" }
```

---

#### PATCH `/collections/{collection_id}`
Partially update an existing collection.

Notes:
- Only fields you send are updated; omitted fields remain unchanged.
- Empty or whitespace-only strings are normalized to `null`.
- Sending an empty JSON object (`{}`) returns the collection unchanged.

**Path parameters**

| Name | Type | Required | Description |
|---|---|---:|---|
| `collection_id` | string | yes | Collection UUID |

**Request body**: `CollectionUpdateOptional`

**curl**

```bash
curl -sS -X PATCH "http://localhost:8000/collections/<collection_id>" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description"
  }'
```

**fetch**

```javascript
const collectionId = '<collection_id>';

const res = await fetch(`http://localhost:8000/collections/${collectionId}`, {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    description: 'Updated description',
  }),
});

if (!res.ok) throw new Error(await res.text());
console.log(await res.json());
```

**Success response — 200**

```json
{
  "id": "50ab7cc9-eed7-414d-8f23-1b19e20683f8",
  "name": "Onboarding",
  "description": "Updated description",
  "prompt_ids": ["d010f7fa-10a5-4d1f-9b16-2dc2c75eafd3"],
  "created_at": "2026-02-18T19:51:56.546992"
}
```

**Errors**

- `404 Not Found`

```json
{ "detail": "Collection not found" }
```

---

#### DELETE `/collections/{collection_id}`
Delete a collection by ID.

Notes:
- Deleting a collection also deletes all prompts that belong to it.

**Path parameters**

| Name | Type | Required | Description |
|---|---|---:|---|
| `collection_id` | string | yes | Collection UUID |

**curl**

```bash
curl -sS -X DELETE "http://localhost:8000/collections/<collection_id>" -i
```

**fetch**

```javascript
const collectionId = '<collection_id>';

const res = await fetch(`http://localhost:8000/collections/${collectionId}`, {
  method: 'DELETE',
});

if (res.status !== 204) throw new Error(await res.text());
```

**Success response — 204**

No response body.

**Errors**

- `404 Not Found`

```json
{ "detail": "Collection not found" }
```

---

### Admin

#### POST `/admin/populate-test-data`
Start test-data generation as a background task. Returns immediately with `202 Accepted`. Poll `GET /admin/populate-status` to track progress.

**Request body** (all fields optional)

| Field | Type | Default | Description |
|---|---|---|---|
| `num_prompts` | int | `40` | Number of prompts to generate |
| `num_collections` | int | `4` | Number of collections to create |
| `collection_chance` | float | `0.6` | Probability each prompt is assigned to a collection |
| `tags_per_prompt` | int | `3` | Number of tags assigned to each prompt |
| `random_seed` | int \| null | `null` | Seed for reproducible generation |
| `tag_as_test_fill` | bool | `false` | If true, adds `"test fill"` to every prompt's tags |
| `append_mode` | bool | `false` | If false (default), clears all data before generating. If true, adds to existing data. |
| `data_source` | string | `"dataset"` | `"dataset"` = sample from curated prompt pool; `"template"` = auto-generated from topics |

**curl**

```bash
# Default settings
curl -sS -X POST "http://localhost:8000/admin/populate-test-data"

# Custom settings
curl -sS -X POST "http://localhost:8000/admin/populate-test-data" \
  -H "Content-Type: application/json" \
  -d '{ "num_prompts": 100, "num_collections": 10, "append_mode": true }'
```

**fetch**

```javascript
const res = await fetch('http://localhost:8000/admin/populate-test-data', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ num_prompts: 100, num_collections: 10 }),
});
const data = await res.json();
console.log(data);
```

**Success response — 202**

```json
{ "status": "started", "total": 40 }
```

**Errors**

- `409 Conflict` (a populate operation is already running)

```json
{ "detail": "A populate operation is already in progress." }
```

---

#### DELETE `/admin/clear-all-data`
Clear all prompts and collections from the database.

**Request**

- No parameters
- No body

**curl**

```bash
curl -sS -X DELETE "http://localhost:8000/admin/clear-all-data"
```

**fetch**

```javascript
const res = await fetch('http://localhost:8000/admin/clear-all-data', {
  method: 'DELETE',
});
const data = await res.json();
console.log(data);
```

**Success response — 200**

```json
{
  "status": "success",
  "message": "All data cleared successfully",
  "prompts_removed": 40,
  "collections_removed": 4
}
```

**Errors**

- `500 Internal Server Error` (if data clearing fails)

```json
{ "detail": "Failed to clear data: <message>" }
```

---

#### DELETE `/admin/clear-test-data`
Delete only prompts tagged with `"test fill"` (created by `populate-test-data` with `tag_as_test_fill: true`). Leaves all other data untouched.

**curl**

```bash
curl -sS -X DELETE "http://localhost:8000/admin/clear-test-data"
```

**fetch**

```javascript
const res = await fetch('http://localhost:8000/admin/clear-test-data', { method: 'DELETE' });
const data = await res.json();
console.log(data);
```

**Success response — 200**

```json
{
  "status": "success",
  "message": "Removed 40 prompt(s) tagged 'test fill'",
  "prompts_removed": 40
}
```

---

#### GET `/admin/populate-status`
Poll the progress of a running `populate-test-data` background task.

**curl**

```bash
curl -sS "http://localhost:8000/admin/populate-status"
```

**fetch**

```javascript
const res = await fetch('http://localhost:8000/admin/populate-status');
const data = await res.json();
console.log(data);
```

**Success response — 200**

```json
{
  "current": 25,
  "total": 40,
  "active": true,
  "phase": "inserting",
  "error": null,
  "prompts_created": 25,
  "collections_created": 0,
  "skipped": 0
}
```

`phase` progresses through: `"generating"` → `"inserting"` → `"versioning"` → `"collections"` → `"assigning"` → `"done"`.

When `active` is `false` and `error` is `null`, the operation completed successfully. When `active` is `false` and `error` is non-null, the operation failed.

---

#### GET `/admin/embedding-status`
Return the number of prompts with and without vector embeddings.

**curl**

```bash
curl -sS "http://localhost:8000/admin/embedding-status"
```

**Success response — 200**

```json
{ "total": 40, "embedded": 38, "complete": false }
```

`complete` is `true` when all prompts have embeddings (or when there are no prompts).

---

#### POST `/admin/backfill-embeddings`
Generate vector embeddings for all prompts that are missing them. Safe to call multiple times — already-embedded prompts are skipped.

**curl**

```bash
curl -sS -X POST "http://localhost:8000/admin/backfill-embeddings"
```

**Success response — 200**

```json
{ "status": "success", "updated": 2, "message": "Embeddings generated for 2 prompt(s)." }
```

**Errors**

- `503 Service Unavailable` (embedding model not available)

```json
{ "detail": "Model unavailable: <message>" }
```

---

#### GET `/admin/events`
Server-Sent Events (SSE) stream for real-time data change notifications. Connect once and receive push events whenever data is populated or cleared.

**curl**

```bash
curl -sS -N "http://localhost:8000/admin/events"
```

**fetch**

```javascript
const source = new EventSource('http://localhost:8000/admin/events');
source.onmessage = (e) => console.log(JSON.parse(e.data));
```

**Event types**

| Event | When | Example data |
|---|---|---|
| `connected` | On initial connection | `{ "event": "connected" }` |
| `data_changed` | After populate or clear | `{ "event": "data_changed", "message": "Test data populated", "action": "populate" }` |

Actions: `"populate"`, `"clear"`, `"clear_test"`.

Keep-alive comment lines (`: keepalive`) are sent every 15 seconds to prevent connection timeouts.

---

### Prompt Versioning

#### GET `/prompts/{prompt_id}/versions`
List all versions of a prompt.

**Path parameters**

| Name | Type | Required | Description |
|---|---|---:|---|
| `prompt_id` | string | yes | Prompt UUID |

**curl**

```bash
curl -sS "http://localhost:8000/prompts/<prompt_id>/versions"
```

**fetch**

```javascript
const promptId = '<prompt_id>';
const res = await fetch(`http://localhost:8000/prompts/${promptId}/versions`);
if (!res.ok) throw new Error(await res.text());
console.log(await res.json());
```

**Success response — 200**

```json
{
  "prompt_id": "d010f7fa-10a5-4d1f-9b16-2dc2c75eafd3",
  "versions": [
    {
      "version": 2,
      "created_at": "2026-02-18T19:00:00.000000",
      "title": "Summarize content (v2)",
      "description": "Updated version"
    },
    {
      "version": 1,
      "created_at": "2026-02-18T18:24:20.454842",
      "title": "Summarize content",
      "description": "General-purpose summarization prompt"
    }
  ],
  "total": 2
}
```

**Errors**

- `404 Not Found`

```json
{ "detail": "Prompt not found" }
```

---

#### GET `/prompts/{prompt_id}/versions/{version}`
Get a specific version of a prompt.

**Path parameters**

| Name | Type | Required | Description |
|---|---|---:|---|
| `prompt_id` | string | yes | Prompt UUID |
| `version` | integer | yes | Version number |

**curl**

```bash
curl -sS "http://localhost:8000/prompts/<prompt_id>/versions/1"
```

**fetch**

```javascript
const promptId = '<prompt_id>';
const res = await fetch(`http://localhost:8000/prompts/${promptId}/versions/1`);
if (!res.ok) throw new Error(await res.text());
console.log(await res.json());
```

**Success response — 200**

```json
{
  "prompt_id": "d010f7fa-10a5-4d1f-9b16-2dc2c75eafd3",
  "version": 1,
  "title": "Summarize content",
  "content": "Summarize: {{input}}",
  "description": "General-purpose summarization prompt",
  "collection_id": "50ab7cc9-eed7-414d-8f23-1b19e20683f8",
  "created_at": "2026-02-18T18:24:20.454842"
}
```

**Errors**

- `404 Not Found`

```json
{ "detail": "Prompt not found" }
```

or

```json
{ "detail": "Version not found" }
```

---

#### POST `/prompts/{prompt_id}/versions/{version}/promote`
Promote an old version to become the new latest version.

This creates a new version that is a copy of the specified old version, making it the current version.

**Path parameters**

| Name | Type | Required | Description |
|---|---|---:|---|
| `prompt_id` | string | yes | Prompt UUID |
| `version` | integer | yes | Version number to promote |

**curl**

```bash
curl -sS -X POST "http://localhost:8000/prompts/<prompt_id>/versions/1/promote"
```

**fetch**

```javascript
const promptId = '<prompt_id>';
const res = await fetch(`http://localhost:8000/prompts/${promptId}/versions/1/promote`, {
  method: 'POST',
});

if (!res.ok) throw new Error(await res.text());
console.log(await res.json());
```

**Success response — 201**

```json
{
  "id": "d010f7fa-10a5-4d1f-9b16-2dc2c75eafd3",
  "title": "Summarize content",
  "content": "Summarize: {{input}}",
  "description": "General-purpose summarization prompt",
  "collection_id": "50ab7cc9-eed7-414d-8f23-1b19e20683f8",
  "created_at": "2026-02-18T18:24:20.454842",
  "updated_at": "2026-02-18T19:30:00.000000",
  "version": 3
}
```

**Errors**

- `404 Not Found`

```json
{ "detail": "Prompt not found" }
```

or

```json
{ "detail": "Version not found" }
```
