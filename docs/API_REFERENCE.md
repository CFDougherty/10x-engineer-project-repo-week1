# PromptLab API Reference

Base URL (local): `http://localhost:8000`

- Swagger UI: `GET /docs`
- OpenAPI JSON: `GET /openapi.json`
- Content type: JSON (`Content-Type: application/json`)
- Auth: none
- Storage: in-memory (restarting the server clears data)

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

- Status code: `422 Unprocessable Entity`
- Typical causes:
  - missing required fields (`title`, `content`, `name`)
  - field length constraints (e.g., `title` max 200)

**Format (example)**

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "title"],
      "msg": "Field required",
      "input": { "content": "..." }
    }
  ]
}
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

#### Collection (response)

```json
{
  "id": "50ab7cc9-eed7-414d-8f23-1b19e20683f8",
  "name": "Onboarding",
  "description": "Prompts used during onboarding",
  "created_at": "2026-02-18T19:51:56.546992"
}
```

### List wrappers

#### PromptList (response)

```json
{
  "prompts": [/* Prompt[] */],
  "total": 0
}
```

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

| Name | Type | Required | Description |
|---|---|---:|---|
| `collection_id` | string | no | Filter prompts by exact `collection_id` |
| `search` | string | no | Case-insensitive substring match against `title` and `description` |

**curl**

```bash
# List all prompts
curl -sS "http://localhost:8000/prompts"

# Filter by collection
curl -sS "http://localhost:8000/prompts?collection_id=<collection_id>"

# Search
curl -sS "http://localhost:8000/prompts?search=summarize"

# Combine filter + search
curl -sS "http://localhost:8000/prompts?collection_id=<collection_id>&search=summarize"
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
      "created_at": "2026-02-18T18:24:20.454842",
      "updated_at": "2026-02-18T18:24:20.454844"
    }
  ],
  "total": 1
}
```

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
  "created_at": "2026-02-18T18:24:20.454842",
  "updated_at": "2026-02-18T18:24:20.454844"
}
```

**Errors**

- `400 Bad Request` (when `collection_id` is provided but does not exist)

```json
{ "detail": "Collection not found" }
```

- `422 Unprocessable Entity` (invalid body; example: missing `title`)

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "title"],
      "msg": "Field required",
      "input": { "content": "Summarize: {{input}}" }
    }
  ]
}
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

- `422 Unprocessable Entity` (invalid body; example: missing `content`)

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "content"],
      "msg": "Field required",
      "input": { "title": "Summarize content (v2)" }
    }
  ]
}
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

- `422 Unprocessable Entity` (invalid body; example: wrong type)

```json
{
  "detail": [
    {
      "type": "string_type",
      "loc": ["body", "title"],
      "msg": "Input should be a valid string",
      "input": 123
    }
  ]
}
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
  "created_at": "2026-02-18T19:51:56.546992"
}
```

**Errors**

- `422 Unprocessable Entity` (invalid body; example: missing `name`)

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "name"],
      "msg": "Field required",
      "input": { "description": "Prompts used during onboarding" }
    }
  ]
}
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