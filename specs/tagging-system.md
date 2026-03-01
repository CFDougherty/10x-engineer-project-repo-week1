# Tagging System

Tags are an optional list of strings on every `Prompt`. They are stored as part of the prompt record, captured in every version snapshot, and searchable via the standard `GET /prompts` endpoint using `filter=tags`.

## Storage Model

Tags live on the `Prompt` model as `Optional[List[str]]`. `None` means the prompt has no tags; an empty list is also valid. Tags are persisted inline — there is no separate tags table or index.

```json
{
  "id": "a1b2c3d4-...",
  "title": "Code review assistant",
  "content": "You are an expert code reviewer...",
  "tags": ["code-review", "python", "engineering"],
  "version": 2
}
```

Tags are also captured in every `PromptVersion` snapshot, so historical versions accurately reflect the tags that were active at the time.

---

## Validation Rules

| Rule | Detail |
|------|--------|
| Type | Each element must be a `str` |
| Non-empty | Whitespace-only strings are rejected |
| No max count | No limit on number of tags per prompt |
| No max length | No character limit per individual tag |
| SQL injection | Blocked by `validate_no_sql_injection` on the parent `PromptBase` |
| HTML | Not explicitly sanitized in the tags field (sanitization applies to `title`, `content`, `description`) |

Validation is enforced by `validate_tags` in `PromptBase` (see [backend/app/models.py](../backend/app/models.py)).

---

## Search and Filter API

Tags are searchable via the standard list endpoint:

```
GET /prompts?search={query}&filter=tags&fuzzy={true|false}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `search` | `str` | — | Term to match against tags |
| `filter` | `str` | — | Set to `tags` to restrict matching to the tags field |
| `fuzzy` | `bool` | `true` | Enable fuzzy matching (fuzzysearch) vs exact substring |
| `collection_id` | `str` | — | Optional: pre-filter by collection before searching |
| `limit` | `int` | — | Pagination: max results to return |
| `offset` | `int` | `0` | Pagination: number of results to skip |

---

## Tag Search Decision Flow

```mermaid
flowchart TD
    A["GET /prompts?search=X&filter=tags"] --> B{Is query empty<br/>or whitespace?}
    B -- Yes --> C[Return all prompts unchanged]
    B -- No --> D{fuzzy=true?}

    D -- Yes --> E{"prompt.tags<br/>non-empty?"}
    E -- No --> H[Exclude prompt]
    E -- Yes --> F["Join all tags into one string<br/>' '.join(prompt.tags).lower()"]
    F --> G["fuzzysearch.find_near_matches()<br/>max_dist = 0 if single-char<br/>else max(1, len(query)//2)"]
    G --> G2{Any near<br/>matches found?}
    G2 -- No --> H
    G2 -- Yes --> G3["Filter: keep matches where<br/>dist ≤ min(2, len(query)//2)<br/>(single-char: dist = 0 only)"]
    G3 --> G4{Any good<br/>matches remain?}
    G4 -- No --> H
    G4 -- Yes --> I["Score = max(0,<br/>100×weight − start×2 − dist×5)<br/>(field weight = 1.0 for tags)"]
    I --> J[Add prompt+score to results]

    D -- No --> K[Iterate over each tag in prompt.tags]
    K --> L{query.lower() in<br/>tag.lower()?}
    L -- Yes --> M[Include prompt, stop checking tags]
    L -- No --> N{More tags?}
    N -- Yes --> K
    N -- No --> O[Exclude prompt]

    J --> P["Filter results: score ≥ 30<br/>Sort by score descending"]
    M --> Q[Return prompts in original order]
    P --> R[Return PromptList]
    Q --> R
    H --> R
    O --> R
    C --> R
```

---

## Tag Lifecycle

Tags travel with the prompt through every operation:

| Operation | Tag Behavior |
|-----------|-------------|
| `POST /prompts` | Tags set from request body; captured in version 1 snapshot |
| `PUT /prompts/{id}` | Tags fully replaced from request body; new version snapshot created |
| `PATCH /prompts/{id}` | Tags **cannot** be changed via PATCH — `PromptUpdateOptional` has no `tags` field. Existing tags are always preserved unchanged. Use `PUT` to update tags. |
| Version snapshot | `PromptVersion.tags` captures the exact tag list at the time of the snapshot |
| Promote | Promoted version restores the old snapshot's tag list as the new current tags |

---

## Example Requests

### Create a prompt with tags

```http
POST /prompts
Content-Type: application/json

{
  "title": "Code review assistant",
  "content": "You are an expert code reviewer...",
  "tags": ["code-review", "python", "engineering"]
}
```

### Add a tag via PUT

Tags can only be changed through a full replacement using `PUT`. `PATCH` does not support the `tags` field.

```http
PUT /prompts/a1b2c3d4
Content-Type: application/json

{
  "title": "Code review assistant",
  "content": "You are an expert code reviewer...",
  "tags": ["code-review", "python", "engineering", "new-tag"]
}
```

### Search prompts by tag (fuzzy)

```http
GET /prompts?search=python&filter=tags
```

### Search prompts by tag (exact substring)

```http
GET /prompts?search=python&filter=tags&fuzzy=false
```

### Search within a collection by tag

```http
GET /prompts?search=engineering&filter=tags&collection_id=c9d8e7f6
```

---

## Fuzzy Matching Details

When `fuzzy=true` (the default), matching uses the `fuzzysearch` library:

- All tags for a prompt are **joined into a single string** before matching — this means a multi-word query can match across tag boundaries
- `fuzzysearch.find_near_matches` is called with `max_l_dist = max(1, len(query) // 2)` (single-char: `0`)
- Results are then filtered to `dist ≤ min(2, len(query) // 2)`, so the effective ceiling is **2** for queries of 5+ characters
- Single-character queries require an exact match (distance 0) at both stages
- Scores below `30` are discarded to suppress low-quality results
- Results are sorted by score descending so the most relevant prompts appear first
