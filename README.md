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
pip install -r requirements.txt

# Start the API server
python main.py
```

- API base URL: `http://localhost:8000`
- Interactive Swagger docs: `http://localhost:8000/docs`

### Run tests

```bash
cd backend
pytest -v
```

---

## API Summary

All endpoints are served from the base URL (`http://localhost:8000`).

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/prompts` | List prompts (optional `collection_id`, `search`) |
| GET | `/prompts/{prompt_id}` | Get a single prompt by ID |
| POST | `/prompts` | Create a new prompt |
| PUT | `/prompts/{prompt_id}` | Replace an existing prompt |
| PATCH | `/prompts/{prompt_id}` | Partially update an existing prompt |
| DELETE | `/prompts/{prompt_id}` | Delete a prompt |
| GET | `/collections` | List collections |
| GET | `/collections/{collection_id}` | Get a single collection by ID |
| POST | `/collections` | Create a new collection |
| DELETE | `/collections/{collection_id}` | Delete a collection (and its prompts) |

---

## Usage Examples

Examples below use `curl` and assume the server is running at `http://localhost:8000`.

### 1) Health check

```bash
curl -s http://localhost:8000/health
```

### 2) Create a collection

```bash
curl -s -X POST http://localhost:8000/collections \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Onboarding",
    "description": "Prompts used during onboarding"
  }'
```

### 3) List collections

```bash
curl -s http://localhost:8000/collections
```

### 4) Create a prompt

```bash
curl -s -X POST http://localhost:8000/prompts \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Summarize content",
    "content": "Summarize the following text for a non-technical audience: {{input}}",
    "description": "General-purpose summarization prompt",
    "collection_id": "<collection_id_here>"
  }'
```

### 5) List prompts (filter + search)

```bash
# Filter by collection
curl -s "http://localhost:8000/prompts?collection_id=<collection_id_here>"

# Search by text in title/description
curl -s "http://localhost:8000/prompts?search=summarize"
```

### 6) Get / update / delete a prompt

```bash
# Get
curl -s http://localhost:8000/prompts/<prompt_id_here>

# Replace (PUT)
curl -s -X PUT http://localhost:8000/prompts/<prompt_id_here> \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Summarize content (v2)",
    "content": "Summarize: {{input}}\n\nKeep it under 5 bullets.",
    "description": "Updated constraints",
    "collection_id": "<collection_id_here>"
  }'

# Partial update (PATCH) - only send fields you want to change
curl -s -X PATCH http://localhost:8000/prompts/<prompt_id_here> \
  -H 'Content-Type: application/json' \
  -d '{
    "description": "Now optimized for bullet summaries"
  }'

# Delete (returns 204 No Content)
curl -i -X DELETE http://localhost:8000/prompts/<prompt_id_here>
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
