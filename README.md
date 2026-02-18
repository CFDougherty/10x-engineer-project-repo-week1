# PromptLab

AI Prompt Engineering Platform — store, organize, version, and test prompt templates for your team.

PromptLab is a lightweight FastAPI backend (frontend planned) that lets AI engineers manage:

- Prompt templates with variables (e.g. `{{input}}`, `{{context}}`)
- Collections (group prompts by project)
- Search and filtering
- Versioning/tagging (planned in upcoming weeks)

---

## Project Overview

PromptLab acts like a “Postman for prompts”: a shared workspace to create prompts, keep them organized, and retrieve/update them via a simple REST API.

---

## Installation & Setup

### Prerequisites

- Python 3.10+
- Git

### Run in GitHub Codespaces

GitHub Codespaces forwards port `8000` automatically (see the **Ports** tab).

If the devcontainer setup did not install dependencies, install them from the repository root:

```bash
python -m pip install -r backend/requirements.txt
```

Then start the API server:

```bash
cd backend
python main.py
# or: uvicorn app.api:app --reload --host 0.0.0.0 --port 8000
```

### Run locally

```bash
# Clone the repo
git clone <your-repo-url>
cd promptlab

# (Recommended) create & activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install backend dependencies
cd backend
python -m pip install -r requirements.txt

# Start the API server
# NOTE: run from the backend/ directory so the `app` module can be imported.
uvicorn app.api:app --reload --host 0.0.0.0 --port 8000
```

- API base URL: `http://localhost:8000`
- Interactive Swagger docs: `http://localhost:8000/docs`

**GitHub Codespaces note:** if you open the Swagger UI in your browser, use the forwarded URL shown in the Codespaces **Ports** tab (port `8000`) and append `/docs` (e.g. `https://<your-codespace>-8000.app.github.dev/docs`). From the Codespaces terminal, `http://localhost:8000` works.

### Run tests

```bash
cd backend
pytest -v
```

---

## API Summary

- Base URL: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI spec: `http://localhost:8000/openapi.json`

### Endpoints

| Method | Endpoint | Success | Notes |
|---|---|---:|---|
| GET | `/health` | 200 | Returns `{ "status": "healthy", "version": "…" }` |
| GET | `/prompts` | 200 | Returns `{ prompts: Prompt[], total: number }`. Optional query params: `collection_id` (exact match), `search` (matches **title** and **description**). |
| GET | `/prompts/{prompt_id}` | 200 | 404 if not found |
| POST | `/prompts` | 201 | 400 if `collection_id` is provided but does not exist |
| PUT | `/prompts/{prompt_id}` | 200 | Full replace (requires at least `title` and `content`). 404 if not found. 400 if `collection_id` is invalid |
| PATCH | `/prompts/{prompt_id}` | 200 | Partial update (send only fields you want to change). Empty `{}` leaves the resource unchanged. 404 if not found. 400 if `collection_id` is invalid |
| DELETE | `/prompts/{prompt_id}` | 204 | 404 if not found |
| GET | `/collections` | 200 | Returns `{ collections: Collection[], total: number }` |
| GET | `/collections/{collection_id}` | 200 | 404 if not found |
| POST | `/collections` | 201 |  |
| DELETE | `/collections/{collection_id}` | 204 | Deletes the collection **and all prompts** that reference it. 404 if not found |

### Data model notes

- IDs are server-generated UUIDv4 strings (e.g. `"d010f7fa-10a5-4d1f-9b16-2dc2c75eafd3"`).
- Timestamps are generated using `datetime.utcnow()` and serialized as ISO-8601 strings **without** a timezone offset (e.g. `"2026-02-18T18:24:20.454842"`). Treat them as UTC.
- `id`, `created_at`, and `updated_at` are read-only response fields; they are not accepted in create/update request bodies.

`Prompt` shape (response):

```json README.md
{
  "id": "uuid",
  "title": "string",
  "content": "string",
  "description": "string | null",
  "collection_id": "uuid | null",
  "created_at": "2026-02-18T18:24:20.454842",
  "updated_at": "2026-02-18T18:24:20.454844"
}
```

`Collection` shape (response):

```json README.md
{
  "id": "uuid",
  "name": "string",
  "description": "string | null",
  "created_at": "2026-02-18T18:24:20.452339"
}
```

> Note: Collections currently do not have an `updated_at` field.

### Persistence

Storage is **in-memory** (`backend/app/storage.py`). Restarting the server clears all prompts and collections.

---

## Usage Examples

Examples below use `curl` and assume the server is running at `http://localhost:8000`.

- If you run these commands **inside** a GitHub Codespace, `http://localhost:8000` works.
- If you call the API from your **browser** or your **local machine**, use the forwarded URL shown in the Codespaces **Ports** tab (port `8000`).

Tip: pipe responses to `jq` for readability (e.g. `... | jq`).

### 0) (Optional) Seed sample data

If you want something to query right away, run the following to create 2 collections and 3 prompts.

> Note: storage is in-memory; restarting the server clears this data.

```bash
# Requires: jq (preinstalled in GitHub Codespaces)
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
  -d '{"title":"Summarize content","content":"Summarize the following text for a non-technical audience: {{input}}","description":"General-purpose summarization prompt","collection_id":"'"$ONBOARDING_ID"'"}' \
  >/dev/null

curl -sS -X POST http://localhost:8000/prompts \
  -H 'Content-Type: application/json' \
  -d '{"title":"Summarize meeting notes","content":"Summarize these meeting notes into action items: {{notes}}","description":"Summarize and extract action items"}' \
  >/dev/null

curl -sS -X POST http://localhost:8000/prompts \
  -H 'Content-Type: application/json' \
  -d '{"title":"Write ad copy","content":"Write 3 ad variants for: {{product}}. Tone: {{tone}}","description":"Paid social ads","collection_id":"'"$MARKETING_ID"'"}' \
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
  "created_at": "2026-02-18T19:19:33.340310"
}
```

To reuse the collection ID in later examples:

```bash
COLLECTION_ID=$(curl -sS -X POST http://localhost:8000/collections \
  -H 'Content-Type: application/json' \
  -d '{"name":"Onboarding","description":"Prompts used during onboarding"}' \
  | jq -r .id)

echo "COLLECTION_ID=$COLLECTION_ID"
```

### 3) List collections

```bash
curl -s http://localhost:8000/collections
```

If you haven't created any collections yet, you'll see:

```json
{
  "collections": [],
  "total": 0
}
```

After you create one or more collections (and optionally prompts that reference them), you’ll see something like this (example):

```json
{
  "collections": [
    {
      "name": "Onboarding",
      "description": "Prompts used during onboarding",
      "id": "50ab7cc9-eed7-414d-8f23-1b19e20683f8",
      "created_at": "2026-02-18T19:51:56.546992"
    },
    {
      "name": "Marketing",
      "description": null,
      "id": "38d3aa4c-a82b-442d-aa64-370f34113878",
      "created_at": "2026-02-18T19:52:20.828994"
    }
  ],
  "total": 2
}
```

> Note: `/collections` returns collection metadata only. To list the prompts “inside” a collection, use `GET /prompts?collection_id=<collection_id_here>` (or any collection UUID).

### 4) Create a prompt

`collection_id` is optional. If you include it, it must be an existing collection UUID (otherwise you'll get `{"detail":"Collection not found"}`).

Create a prompt without assigning it to a collection:

```bash
curl -sS -X POST http://localhost:8000/prompts \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Summarize content",
    "content": "Summarize the following text for a non-technical audience: {{input}}",
    "description": "General-purpose summarization prompt"
  }' \
  | jq
```

Create a prompt and assign it to a new collection (standalone; captures IDs for later use):

```bash
# Requires: jq (preinstalled in GitHub Codespaces)
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
    "collection_id": "'"$COLLECTION_ID"'"
  }' \
  | jq -r .id)

echo "COLLECTION_ID=$COLLECTION_ID"
echo "PROMPT_ID=$PROMPT_ID"
```

### 5) List prompts (filter + search)

`GET /prompts` returns an object with `{ "prompts": [...], "total": <number> }`.

```bash
# Filter by collection
curl -sS "http://localhost:8000/prompts?collection_id=<collection_id_here>" | jq

# Search by text in title/description (case-insensitive)
curl -sS "http://localhost:8000/prompts?search=summarize" | jq

# You can combine filters
curl -sS "http://localhost:8000/prompts?collection_id=<collection_id_here>&search=summarize" | jq
```

Example response (truncated):

```json
{
  "prompts": [
    {
      "id": "...",
      "title": "Summarize content",
      "content": "...",
      "description": "General-purpose summarization prompt",
      "collection_id": "...",
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "total": 1
}
```

### 6) Get / update / delete a prompt

The commands below are **standalone**: they create a temporary collection + prompt, then demonstrate `GET`, `PUT`, `PATCH`, and `DELETE`.

> Notes:
>
> - `PUT /prompts/{prompt_id}` is a **full replace**. If you omit optional fields like `description` or `collection_id`, they will be set to `null`.
> - `PATCH /prompts/{prompt_id}` is a **partial update**. Send only the fields you want to change.

```bash
# Requires: jq (preinstalled in GitHub Codespaces)

# Create a collection (optional) and a prompt so we have IDs to work with.
COLLECTION_ID=$(curl -sS -X POST http://localhost:8000/collections \
  -H 'Content-Type: application/json' \
  -d '{"name":"Demo Collection","description":"Used for prompt CRUD example"}' \
  | jq -r .id)

PROMPT_ID=$(curl -sS -X POST http://localhost:8000/prompts \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Summarize content",
    "content": "Summarize: {{input}}",
    "description": "Initial version",
    "collection_id": "'"$COLLECTION_ID"'"
  }' \
  | jq -r .id)

echo "PROMPT_ID=$PROMPT_ID"

# Get
curl -sS "http://localhost:8000/prompts/$PROMPT_ID" | jq

# Replace (PUT) - include collection_id if you want to keep it assigned
curl -sS -X PUT "http://localhost:8000/prompts/$PROMPT_ID" \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Summarize content (v2)",
    "content": "Summarize: {{input}}\n\nKeep it under 5 bullets.",
    "description": "Updated constraints",
    "collection_id": "'"$COLLECTION_ID"'"
  }' \
  | jq

# Partial update (PATCH) - only send fields you want to change
curl -sS -X PATCH "http://localhost:8000/prompts/$PROMPT_ID" \
  -H 'Content-Type: application/json' \
  -d '{"description":"Now optimized for bullet summaries"}' \
  | jq

# Delete (returns 204 No Content)
curl -i -X DELETE "http://localhost:8000/prompts/$PROMPT_ID"
```

### 7) Delete a collection

```bash
# Deletes the collection and its associated prompts (returns 204 No Content)
curl -i -X DELETE http://localhost:8000/collections/<collection_id_here>
```

---

## Project Structure

```text
promptlab/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api.py           # Routes/endpoints
│   │   ├── models.py        # Pydantic models
│   │   ├── storage.py       # In-memory storage
│   │   └── utils.py         # Helper functions
│   ├── tests/               # pytest tests
│   └── main.py              # API entrypoint
├── docs/                    # Documentation (Week 2)
├── specs/                   # Feature specs (Week 2)
└── frontend/                # Frontend (Week 4)
```

---

## Tech Stack

- **Backend**: FastAPI, Pydantic
- **Testing**: pytest
- **Storage**: in-memory (planned to evolve)
