# PromptLab

AI Prompt Engineering Platform — store, organize, version, and test prompt templates for your team.

PromptLab is a full-stack "Postman for prompts": a shared workspace to create, organize, search, and version prompt templates via a REST API and a React UI.

Features:
- Prompt templates with variables (e.g. `{{input}}`, `{{context}}`)
- Collections (group prompts by project)
- Full versioning — every edit creates a snapshot; promote old versions back to current
- Fuzzy and semantic search (pgvector embeddings)
- Real-time updates via Server-Sent Events

---

## Project Overview

PromptLab lets AI engineers manage prompts through both a web interface and a REST API. The backend is a FastAPI app backed by PostgreSQL (with the pgvector extension for semantic search). The frontend is a React/Vite app.

---

## Installation & Setup

### Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose (required — the backend depends on PostgreSQL + pgvector)
- Node.js 18+ (only needed if running the frontend outside Docker)
- Python 3.11+ (only needed if running the backend outside Docker)

### Quick Start with Docker (Recommended)

```bash
docker-compose up --build
```

This starts three services:
- **db** — PostgreSQL 16 with pgvector, port 5432
- **backend** — FastAPI API, port 8000
- **frontend** — React/Vite (served by nginx), port 3000

Access the app at: http://localhost:3000
API docs (Swagger): http://localhost:8000/docs

Data is persisted in a Docker volume (`postgres_data`) and survives restarts.

### Run Locally Without Docker

You need a running PostgreSQL instance with the pgvector extension installed.

#### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Set the database URL (adjust credentials to match your instance)
export DATABASE_URL="postgresql+asyncpg://promptlab:promptlab@localhost:5432/promptlab"

uvicorn app.api:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at:
- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

#### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at: http://localhost:5173

### Run in GitHub Codespaces

GitHub Codespaces forwards port `8000` automatically (see the **Ports** tab). Use Docker Compose:

```bash
docker-compose up --build
```

From the Codespaces terminal, `http://localhost:8000` works. To open the Swagger UI in your browser, use the forwarded URL shown in the Codespaces **Ports** tab and append `/docs`.

### Run tests

Tests require a running PostgreSQL database. Start it with Docker Compose first:

```bash
docker-compose up db -d
```

Then run the tests:

```bash
cd backend
python -m pytest tests/ -v --tb=short
```

---

## Authentication

PromptLab uses a static API key to protect all endpoints. Authentication is **disabled by default** (useful for local development and testing) and enabled by setting the `API_KEY` environment variable.

### Enabling authentication

**1. Generate a key**

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**2. Set the key on the backend**

Add it to your `.env` file (copy `.env.example` as a starting point):

```
API_KEY=your-generated-key-here
```

Or pass it directly to Docker Compose:

```bash
API_KEY=your-generated-key-here docker-compose up
```

**3. Rebuild**

Docker Compose automatically passes `API_KEY` to the frontend build as `VITE_API_KEY` (Vite bakes it into the JS bundle at build time), so there's only one variable to set:

```bash
docker-compose up --build
```

### How it works

- **Web UI (port 3000):** nginx HTTP Basic Auth — browser shows a username/password dialog. Username is `admin`, password is your `API_KEY`.
- **Backend API (port 8000):** every request must include the header `X-API-Key: <your-key>`. The frontend sends this automatically (key is baked in at build time).
- The following endpoints are always public (no key required):
  - `/health` — Docker health checks
  - `/docs` — Swagger UI (interactive API explorer)
  - `/openapi.json` — OpenAPI specification
- Leaving `API_KEY` empty disables all auth (dev/test mode).

### Making authenticated API calls

```bash
# With curl
curl -H "X-API-Key: your-key" http://localhost:8000/prompts

# Without a key when auth is enabled → 401
curl http://localhost:8000/prompts
# {"detail": "Invalid or missing API key"}
```

---

## API Summary

- Base URL: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI spec: `http://localhost:8000/openapi.json`

### Endpoints

#### Prompts

| Method | Endpoint | Success | Notes |
|---|---|---:|---|
| GET | `/prompts` | 200 | Returns `{ prompts, total, next_cursor }`. Query params: `collection_id`, `search`, `filter` (title\|content\|description\|tags\|collection\|all), `fuzzy` (bool, default `true`), `semantic` (bool, default `false`), `limit`, `cursor`, `offset` |
| GET | `/prompts/{prompt_id}` | 200 | 404 if not found |
| POST | `/prompts` | 201 | 400 if `collection_id` is provided but does not exist |
| PUT | `/prompts/{prompt_id}` | 200 | Full replace. Creates a new version. 404 if not found. 400 if `collection_id` is invalid |
| PATCH | `/prompts/{prompt_id}` | 200 | Partial update. Creates a new version only if fields changed. Empty `{}` leaves the resource unchanged. 404 if not found |
| DELETE | `/prompts/{prompt_id}` | 204 | 404 if not found |

#### Versioning

| Method | Endpoint | Success | Notes |
|---|---|---:|---|
| GET | `/prompts/{prompt_id}/versions` | 200 | List all versions (newest first) |
| GET | `/prompts/{prompt_id}/versions/{version}` | 200 | Get a specific immutable version snapshot |
| POST | `/prompts/{prompt_id}/versions/{version}/promote` | 201 | Promote an old version to become the new current version |

#### Collections

| Method | Endpoint | Success | Notes |
|---|---|---:|---|
| GET | `/collections` | 200 | Returns `{ collections, total }` with `prompt_ids` populated on each |
| GET | `/collections/{collection_id}` | 200 | 404 if not found |
| POST | `/collections` | 201 | |
| PUT | `/collections/{collection_id}` | 200 | Full replace. 404 if not found |
| PATCH | `/collections/{collection_id}` | 200 | Partial update. 404 if not found |
| DELETE | `/collections/{collection_id}` | 204 | Deletes the collection **and all prompts** in it. 404 if not found |

#### Admin

| Method | Endpoint | Success | Notes |
|---|---|---:|---|
| GET | `/health` | 200 | Returns `{ "status": "healthy", "version": "…" }` |
| GET | `/admin/events` | 200 | SSE stream — real-time data-change notifications (text/event-stream) |
| POST | `/admin/populate-test-data` | 202 | Seeds test data in the background. Body: `{ num_prompts, num_collections, ... }`. Returns `{ status, total }` |
| GET | `/admin/populate-status` | 200 | Progress of the in-flight populate job: `{ current, total, active, phase, ... }` |
| DELETE | `/admin/clear-all-data` | 200 | Truncates all tables. Returns counts of removed items |
| DELETE | `/admin/clear-test-data` | 200 | Deletes only prompts tagged "test fill" |
| GET | `/admin/embedding-status` | 200 | Returns `{ total, embedded, complete }` |
| POST | `/admin/backfill-embeddings` | 200 | Generates embeddings for any prompts that are missing them |

### Data model notes

- IDs are server-generated UUIDv4 strings.
- Timestamps are ISO-8601 strings treated as UTC (e.g. `"2026-02-18T18:24:20.454842"`).
- `id`, `created_at`, `updated_at`, and `version` are read-only response fields; they are not accepted in request bodies.

`Prompt` shape (response):

```json
{
  "id": "uuid",
  "title": "string",
  "content": "string",
  "description": "string | null",
  "collection_id": "uuid | null",
  "tags": ["string"] | null,
  "version": 3,
  "created_at": "2026-02-18T18:24:20.454842",
  "updated_at": "2026-02-18T18:24:20.454844"
}
```

`Collection` shape (response):

```json
{
  "id": "uuid",
  "name": "string",
  "description": "string | null",
  "prompt_ids": ["uuid", "uuid"],
  "created_at": "2026-02-18T18:24:20.452339"
}
```

> Note: `prompt_ids` is computed at response time (not stored in the DB).

`PromptVersion` shape (response from `/versions/{version}`):

```json
{
  "prompt_id": "uuid",
  "version": 2,
  "title": "string",
  "content": "string",
  "description": "string | null",
  "collection_id": "uuid | null",
  "tags": ["string"] | null,
  "created_at": "2026-02-18T18:24:20.454842"
}
```

### Persistence

Storage uses **PostgreSQL** (async, via SQLAlchemy + asyncpg). Data is durable across restarts when running with Docker Compose (persisted in the `postgres_data` volume). The **pgvector** extension enables semantic similarity search over prompt embeddings.

---

## Test Data Generation

### Via the API (recommended)

Use the admin endpoint with real-time progress tracking via SSE:

```bash
curl -sS -X POST http://localhost:8000/admin/populate-test-data \
  -H 'Content-Type: application/json' \
  -d '{"num_prompts": 40, "num_collections": 4}'
```

Check progress:

```bash
curl -sS http://localhost:8000/admin/populate-status | jq
```

### Via the CLI script (legacy)

```bash
cd backend
python populate_test_data.py
```

Options:

```bash
# Create 40 prompts and 4 collections (default)
python populate_test_data.py

# Custom amounts
python populate_test_data.py --prompts 50 --collections 5

# Clear existing data first
python populate_test_data.py --clear

# Dry run (no API calls)
python populate_test_data.py --dry-run

# Connect to remote server
python populate_test_data.py --base-url http://your-server:8000
```

---

## Usage Examples

Examples below use `curl` and assume the server is running at `http://localhost:8000`. Pipe to `jq` for readability.

### 0) Seed sample data

```bash
# Requires: jq
ONBOARDING_ID=$(curl -sS -X POST http://localhost:8000/collections \
  -H 'Content-Type: application/json' \
  -d '{"name":"Onboarding","description":"Prompts used during onboarding"}' \
  | jq -r .id)

MARKETING_ID=$(curl -sS -X POST http://localhost:8000/collections \
  -H 'Content-Type: application/json' \
  -d '{"name":"Marketing","description":"Prompts used by marketing"}' \
  | jq -r .id)

curl -sS -X POST http://localhost:8000/prompts \
  -H 'Content-Type: application/json' \
  -d '{"title":"Summarize content","content":"Summarize the following text for a non-technical audience: {{input}}","description":"General-purpose summarization prompt","collection_id":"'"$ONBOARDING_ID"'","tags":["summarize","general"]}' \
  >/dev/null

curl -sS -X POST http://localhost:8000/prompts \
  -H 'Content-Type: application/json' \
  -d '{"title":"Summarize meeting notes","content":"Summarize these meeting notes into action items: {{notes}}","description":"Summarize and extract action items","tags":["summarize","meetings"]}' \
  >/dev/null

curl -sS -X POST http://localhost:8000/prompts \
  -H 'Content-Type: application/json' \
  -d '{"title":"Write ad copy","content":"Write 3 ad variants for: {{product}}. Tone: {{tone}}","description":"Paid social ads","collection_id":"'"$MARKETING_ID"'","tags":["marketing","ads"]}' \
  >/dev/null

echo "ONBOARDING_ID=$ONBOARDING_ID"
echo "MARKETING_ID=$MARKETING_ID"

# Sanity check
curl -sS "http://localhost:8000/prompts?search=summarize" | jq
```

### 1) Health check

```bash
curl -s http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

### 2) Create a collection

```bash
curl -sS -X POST http://localhost:8000/collections \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Onboarding",
    "description": "Prompts used during onboarding"
  }'
```

Expected response (example):

```json
{
  "name": "Onboarding",
  "description": "Prompts used during onboarding",
  "id": "e2d1cfef-53b9-4920-a7ad-9fcb1c01b910",
  "prompt_ids": [],
  "created_at": "2026-02-18T19:19:33.340310"
}
```

### 3) List collections

```bash
curl -s http://localhost:8000/collections
```

Example response:

```json
{
  "collections": [
    {
      "name": "Onboarding",
      "description": "Prompts used during onboarding",
      "id": "50ab7cc9-eed7-414d-8f23-1b19e20683f8",
      "prompt_ids": ["d010f7fa-10a5-4d1f-9b16-2dc2c75eafd3"],
      "created_at": "2026-02-18T19:51:56.546992"
    }
  ],
  "total": 1
}
```

> To list the prompts inside a collection, use `GET /prompts?collection_id=<id>`.

### 4) Create a prompt

```bash
COLLECTION_ID=$(curl -sS -X POST http://localhost:8000/collections \
  -H 'Content-Type: application/json' \
  -d '{"name":"Onboarding","description":"Prompts used during onboarding"}' \
  | jq -r .id)

PROMPT_ID=$(curl -sS -X POST http://localhost:8000/prompts \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Summarize content",
    "content": "Summarize the following text for a non-technical audience: {{input}}",
    "description": "General-purpose summarization prompt",
    "collection_id": "'"$COLLECTION_ID"'",
    "tags": ["summarize", "general"]
  }' \
  | jq -r .id)

echo "PROMPT_ID=$PROMPT_ID"
```

### 5) Search prompts

```bash
# Fuzzy search (default)
curl -sS "http://localhost:8000/prompts?search=summarize" | jq

# Exact substring search
curl -sS "http://localhost:8000/prompts?search=summarize&fuzzy=false" | jq

# Semantic search (requires embeddings to be generated)
curl -sS "http://localhost:8000/prompts?search=condense+text&semantic=true" | jq

# Search only in title field
curl -sS "http://localhost:8000/prompts?search=summarize&filter=title" | jq

# Filter by collection
curl -sS "http://localhost:8000/prompts?collection_id=<collection_id_here>" | jq
```

### 6) Get / update / delete a prompt

```bash
COLLECTION_ID=$(curl -sS -X POST http://localhost:8000/collections \
  -H 'Content-Type: application/json' \
  -d '{"name":"Demo Collection"}' | jq -r .id)

PROMPT_ID=$(curl -sS -X POST http://localhost:8000/prompts \
  -H 'Content-Type: application/json' \
  -d '{"title":"Summarize content","content":"Summarize: {{input}}","collection_id":"'"$COLLECTION_ID"'"}' \
  | jq -r .id)

# Get
curl -sS "http://localhost:8000/prompts/$PROMPT_ID" | jq

# Full replace (PUT) — creates a new version
curl -sS -X PUT "http://localhost:8000/prompts/$PROMPT_ID" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Summarize content (v2)","content":"Summarize: {{input}}\n\nKeep it under 5 bullets.","collection_id":"'"$COLLECTION_ID"'"}' \
  | jq

# Partial update (PATCH) — creates a new version if fields changed
curl -sS -X PATCH "http://localhost:8000/prompts/$PROMPT_ID" \
  -H 'Content-Type: application/json' \
  -d '{"description":"Optimized for bullet summaries"}' | jq

# Delete (returns 204 No Content)
curl -i -X DELETE "http://localhost:8000/prompts/$PROMPT_ID"
```

### 7) View and promote versions

```bash
# List all versions
curl -sS "http://localhost:8000/prompts/$PROMPT_ID/versions" | jq

# Get a specific version snapshot
curl -sS "http://localhost:8000/prompts/$PROMPT_ID/versions/1" | jq

# Promote version 1 back to current (creates a new version copy)
curl -sS -X POST "http://localhost:8000/prompts/$PROMPT_ID/versions/1/promote" | jq
```

### 8) Delete a collection

`DELETE /collections/{collection_id}` deletes the collection **and all prompts** in it.

```bash
BASE_URL="http://localhost:8000"

COLLECTION_ID=$(curl -sS -X POST "$BASE_URL/collections" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Temp Collection"}' | jq -er .id)

PROMPT_ID=$(curl -sS -X POST "$BASE_URL/prompts" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Temp Prompt","content":"Hello {{name}}","collection_id":"'"$COLLECTION_ID"'"}' \
  | jq -er .id)

# Delete the collection (cascades to prompts)
curl -sS -i -X DELETE "$BASE_URL/collections/$COLLECTION_ID"

# Confirm both are gone (expect 404)
curl -sS -i "$BASE_URL/prompts/$PROMPT_ID"
curl -sS -i "$BASE_URL/collections/$COLLECTION_ID"
```

---

## Troubleshooting

### Backend won't start
- Make sure the `db` service is running and healthy: `docker-compose up db -d`
- Check `DATABASE_URL` is set correctly if running outside Docker
- Run `docker-compose logs backend` to see startup errors

### Can't connect to the database
- Verify PostgreSQL is running: `docker-compose ps`
- Confirm the pgvector extension is installed in the DB (the Docker image includes it automatically)

### Semantic search returns no results
- Embeddings may not have been generated yet. Use the admin endpoint to backfill:
  ```bash
  curl -sS -X POST http://localhost:8000/admin/backfill-embeddings | jq
  ```
- Check status: `curl -sS http://localhost:8000/admin/embedding-status | jq`

### Port conflicts
Change the ports in `docker-compose.yml` if 8000, 3000, or 5432 are already in use.

---

## API Testing

Test the API using Swagger UI at http://localhost:8000/docs or with curl:

```bash
# Health check
curl http://localhost:8000/health

# Create a collection
curl -X POST http://localhost:8000/collections \
  -H 'Content-Type: application/json' \
  -d '{"name":"Test Collection","description":"Test"}'

# List collections
curl http://localhost:8000/collections
```

---

## Project Structure

```text
promptlab/
├── backend/
│   ├── app/
│   │   ├── api.py           # Routes/endpoints, SSE, admin endpoints
│   │   ├── models.py        # Pydantic models (Prompt, Collection, versioning)
│   │   ├── models_db.py     # SQLAlchemy ORM models
│   │   ├── storage.py       # Async PostgreSQL storage (SQLAlchemy)
│   │   ├── database.py      # Engine + session factory
│   │   └── utils.py         # Search, sort, filter, variable extraction
│   ├── tests/               # pytest tests (404 tests across 14 files)
│   ├── populate_test_data.py  # CLI script to seed test data
│   └── main.py              # API entrypoint
├── docker-compose.yml       # Orchestrates db + backend + frontend
└── frontend/
    ├── src/
    │   ├── pages/           # PromptsPage, CollectionsPage, Layout
    │   ├── components/      # PromptCard, VersionHistoryDialog, AdminToolsDialog, etc.
    │   └── contexts/        # PromptsContext, CollectionsContext
    └── Dockerfile
```

---

## Tech Stack

- **Backend**: FastAPI, Pydantic v2
- **Database**: PostgreSQL 16 + pgvector (async SQLAlchemy + asyncpg)
- **Semantic search**: sentence-transformers (local embeddings)
- **Frontend**: React, Vite, MUI
- **Real-time**: Server-Sent Events (SSE)
- **Testing**: pytest, pytest-asyncio
