"""FastAPI routes for PromptLab.

This module defines the FastAPI application instance and its HTTP routes.

The application is configured with basic OpenAPI metadata (title, description,
version), which is used for generated API documentation and client integrations.

This module also configures Cross-Origin Resource Sharing (CORS) middleware on
the application instance to control how browsers handle cross-origin requests.

The current configuration is fully permissive:
- Allows requests from any origin (``allow_origins=["*"]``).
- Allows all HTTP methods and headers (``allow_methods=["*"]``,
  ``allow_headers=["*"]``).

Note:
    ``allow_credentials=True`` is intentionally omitted. Combining it with
    ``allow_origins=["*"]`` is invalid under the CORS specification and is
    rejected by browsers. The frontend does not send cookies or authorization
    headers, so credentials support is not required.

Authentication:
    When the ``API_KEY`` environment variable is set, all endpoints require an
    ``X-API-Key`` header matching that value. The ``/health`` endpoint is always
    public so Docker health checks continue to work.

    For the SSE endpoint (``/admin/events``), which uses the native
    ``EventSource`` API that cannot send custom headers, pass the key as a
    ``?api_key=`` query parameter instead.

    Leave ``API_KEY`` unset (or empty) to disable authentication — useful for
    local development and testing.
"""

import logging
import random
import secrets
import uuid
import asyncio
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

from fastapi import FastAPI, HTTPException, Body, Request, status, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse, PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import ClassVar, Literal, Optional

from app.models import (
    Prompt, PromptCreate, PromptUpdate, PromptUpdateOptional,
    Collection, CollectionCreate, CollectionUpdateOptional,
    PromptList, CollectionList, HealthResponse,
    get_current_time,
    PromptVersion, VersionList, VersionSummary
)
from app.storage import storage
from app import __version__
from app.database import get_settings


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Enforce API key authentication on all endpoints except /health.

    Authentication is disabled when the ``API_KEY`` setting is empty, which is
    the default for local development and test environments.

    Clients should send the key in the ``X-API-Key`` request header. For the
    SSE endpoint (which uses ``EventSource`` and cannot send custom headers),
    pass the key via the ``?api_key=`` query parameter instead.
    """

    async def dispatch(self, request: Request, call_next):
        expected = get_settings().api_key
        if not expected:
            return await call_next(request)
        if request.url.path == "/health":
            return await call_next(request)
        key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
        if not key or not secrets.compare_digest(key.encode(), expected.encode()):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
            )
        return await call_next(request)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize the database on startup."""
    from app.database import init_db
    await init_db()
    from app.embeddings import agenerate_query_embedding
    await agenerate_query_embedding("")  # warm up model so first semantic search is instant
    yield


app = FastAPI(
    title="PromptLab API",
    description="AI Prompt Engineering Platform",
    version=__version__,
    lifespan=lifespan,
)

# Auth middleware — runs before CORS so unauthenticated requests are rejected early
app.add_middleware(APIKeyMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware to validate content type for JSON endpoints
@app.middleware("http")
async def validate_content_type(request: Request, call_next):
    """Middleware to validate content type for JSON endpoints."""
    if request.method == "POST" and request.url.path == "/prompts":
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type:
            return PlainTextResponse(
                status_code=415,
                content="Unsupported media type"
            )
    return await call_next(request)

# Exception handler to convert Pydantic validation errors (422) to HTTP 400
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Convert Pydantic validation errors to HTTP 400 Bad Request."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Validation error: " + str(exc.errors()[0]["msg"]) if exc.errors() else "Invalid input"},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# ============== Helpers ==============

async def _get_collection_with_prompt_ids(collection: Collection) -> Collection:
    """Return a copy of ``collection`` with ``prompt_ids`` populated from storage.

    Looks up all prompts whose ``collection_id`` matches ``collection.id`` and
    injects their IDs into the returned ``Collection`` instance. The original
    object is not mutated.

    Args:
        collection: The collection to enrich with prompt IDs.

    Returns:
        A new :class:`app.models.Collection` instance identical to ``collection``
        but with ``prompt_ids`` set to the list of prompt IDs currently
        associated with it.
    """
    prompts = await storage.get_prompts_by_collection_id(collection.id)
    return Collection(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        created_at=collection.created_at,
        prompt_ids=[p.id for p in prompts],
    )


# ============== Health Check ==============

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Returns the service health status and the running application version.

    This endpoint is intended for use by load balancers, orchestration systems,
    and monitoring tools to verify that the API process is running and to
    retrieve the currently deployed version.

    Returns:
        HealthResponse: A response object containing:
            - status: Health status string (typically "healthy").
            - version: The current application version.

    """
    return HealthResponse(status="healthy", version=__version__)


# ============== Prompt Endpoints ==============

@app.get("/prompts", response_model=PromptList)
async def list_prompts(
    collection_id: Optional[str] = None,
    search: Optional[str] = None,
    filter: Optional[str] = None,  # 'title', 'description', 'tags', 'collection', or 'all'
    fuzzy: bool = True,
    semantic: bool = False,
    limit: int = Query(default=20, ge=0),
    cursor: Optional[str] = None,
    offset: Optional[int] = Query(default=None, ge=0),
):
    """Lists prompts with server-side filtering, DB-level search, and cursor pagination.

    Returns prompts with content truncated to a preview length.  Use
    ``GET /prompts/{id}`` to retrieve the full content of a specific prompt.

    Pagination modes (mutually exclusive; ``cursor`` takes priority):
    - **Keyset** (recommended): use ``cursor`` from the previous response's
      ``next_cursor`` field.  Stable under concurrent writes.
    - **Offset** (legacy): use ``offset`` + ``limit``.  Supported for
      backward-compatibility with existing clients.

    Args:
        collection_id: Filter to prompts in this collection.
        search: Text search query applied server-side via pg_trgm.
        filter: Field to search. One of 'title', 'description', 'tags',
            'content', 'collection', or 'all' (default).
        fuzzy: When True (default) uses pg_trgm similarity in addition to
            substring matching.  False uses substring-only (ILIKE).
        semantic: When True uses pgvector cosine similarity instead of text
            search.  Requires embeddings to be generated.
        limit: Page size (default 20, min 0).
        cursor: Opaque keyset cursor from a previous response's ``next_cursor``.
        offset: Legacy SQL offset for backward-compatible pagination.

    Returns:
        PromptList with prompts (preview content), total, and next_cursor.
    """
    # ── Semantic search path (unchanged) ─────────────────────────────────────
    if semantic and search and search.strip():
        try:
            from app.embeddings import agenerate_query_embedding
            query_embedding = await agenerate_query_embedding(search)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=f"Semantic search unavailable: {exc}")

        _offset = offset or 0
        _limit = limit or 20
        results = await storage.semantic_search(
            query_embedding=query_embedding,
            limit=_limit,
            offset=_offset,
            collection_id=collection_id,
        )
        total = await storage.count_semantic_results(
            query_embedding=query_embedding,
            collection_id=collection_id,
        )
        next_offset = _offset + len(results)
        next_cursor_val = str(next_offset) if next_offset < total else None
        return PromptList(prompts=results, total=total, next_cursor=next_cursor_val)

    # ── Lexical / browse path ─────────────────────────────────────────────────
    search_field = filter if filter is not None else "all"

    try:
        prompts, next_cursor, total = await storage.get_prompts_page(
            limit=limit,
            cursor=cursor,
            offset=offset,
            collection_id=collection_id,
            search=search,
            fuzzy=fuzzy,
            search_field=search_field,
        )
    except ValueError as exc:
        # Invalid cursor string
        raise HTTPException(status_code=400, detail=str(exc))

    return PromptList(prompts=prompts, total=total, next_cursor=next_cursor)


@app.get("/prompts/{prompt_id}", response_model=Prompt)
async def get_prompt(prompt_id: str):
    """Retrieves a prompt by its unique identifier.

    Args:
        prompt_id (str): The unique ID of the prompt to retrieve.

    Returns:
        Prompt: The prompt associated with ``prompt_id``.

    Raises:
        HTTPException: Raised with status code 404 if no prompt exists for the
            given ``prompt_id``.
    """
    prompt = await storage.get_prompt(prompt_id)

    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return prompt


@app.post("/prompts", response_model=Prompt, status_code=201)
async def create_prompt(prompt_data: PromptCreate):
    """Creates a new prompt and persists it to storage.

    If `prompt_data.collection_id` is provided, this endpoint validates that the
    referenced collection exists before creating the prompt. If the collection
    does not exist, a 400 error is returned.

    Args:
        prompt_data (PromptCreate): Payload containing the fields required to
            create a new prompt. If `collection_id` is provided, it must refer
            to an existing collection.

    Returns:
        Prompt: The newly created prompt as stored in the database.

    Raises:
        HTTPException: Raised with status code 400 if `prompt_data.collection_id`
            is provided but no matching collection is found.
        HTTPException: Raised with status code 415 if the content type is not
            application/json (handled by middleware).
    """
    # Validate collection exists if provided
    if prompt_data.collection_id:
        collection = await storage.get_collection(prompt_data.collection_id)
        if not collection:
            raise HTTPException(status_code=400, detail="Collection not found")

    prompt = Prompt(**prompt_data.model_dump())
    await storage.create_prompt(prompt)

    # Create version 1, then re-fetch to get the updated version field
    await storage.create_prompt_version(prompt.id, prompt)

    return await storage.get_prompt(prompt.id)


@app.put("/prompts/{prompt_id}", response_model=Prompt)
async def update_prompt(prompt_id: str, prompt_data: PromptUpdate):
    """Update an existing prompt.

    Retrieves the prompt identified by ``prompt_id`` and replaces its mutable fields
    (title, content, description, collection_id) with the values provided in
    ``prompt_data``. If ``collection_id`` is provided, this endpoint validates that
    the referenced collection exists. The prompt's ``created_at`` timestamp is
    preserved, and ``updated_at`` is set to the current time.

    Args:
        prompt_id: The unique identifier of the prompt to update.
        prompt_data: The updated prompt fields. If ``collection_id`` is set, it must
            reference an existing collection.

    Returns:
        The updated prompt as persisted by the storage layer.

    Raises:
        HTTPException: If no prompt exists for ``prompt_id`` (404).
        HTTPException: If ``prompt_data.collection_id`` is provided but does not
            correspond to an existing collection (400).
    """
    existing = await storage.get_prompt(prompt_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Validate collection if provided
    if prompt_data.collection_id:
        collection = await storage.get_collection(prompt_data.collection_id)
        if not collection:
            raise HTTPException(status_code=400, detail="Collection not found")

    updated_prompt = Prompt(
        id=existing.id,
        title=prompt_data.title,
        content=prompt_data.content,
        description=prompt_data.description,
        collection_id=prompt_data.collection_id,
        tags=prompt_data.tags,
        created_at=existing.created_at,
        updated_at=get_current_time()
    )

    result = await storage.update_prompt(prompt_id, updated_prompt)

    # Create new version, then re-fetch to get the updated version field
    if result:
        await storage.create_prompt_version(prompt_id, result)
        result = await storage.get_prompt(prompt_id)

    return result


@app.patch("/prompts/{prompt_id}", response_model=Prompt)
async def patch_prompt(prompt_id: str, prompt_data: PromptUpdateOptional = Body(...)):
    """Partially updates an existing prompt.

    This endpoint applies a partial update (PATCH semantics) to the prompt
    identified by `prompt_id`. Only fields explicitly provided in `prompt_data`
    are applied (unset fields are ignored). If `collection_id` is provided, it
    is validated to ensure the referenced collection exists. The prompt's
    `updated_at` timestamp is updated only when at least one field changes.

    Args:
        prompt_id: Unique identifier of the prompt to update.
        prompt_data: Partial prompt payload. Only fields set in this object are
            applied to the existing prompt.

    Returns:
        The persisted, updated prompt model after applying any requested changes.
        If no fields are provided, the existing prompt is returned unchanged.

    Raises:
        HTTPException: If the prompt does not exist (404), or if a provided
            `collection_id` does not correspond to an existing collection (400).
    """
    existing = await storage.get_prompt(prompt_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Validate new collection_id
    if prompt_data.collection_id:
        collection = await storage.get_collection(prompt_data.collection_id)
        if not collection:
            raise HTTPException(status_code=400, detail="Collection not found")

    # Check for actual changes by comparing field values
    updated_fields = prompt_data.model_dump(exclude_unset=True)
    if not updated_fields:
        return existing  # No changes, return the original without updating

    # Check if any of the provided fields actually differ from existing values
    has_changes = False
    for field in updated_fields:
        if field in ['title', 'content', 'description', 'collection_id', 'tags']:
            if getattr(existing, field) != updated_fields[field]:
                has_changes = True
                break

    if not has_changes:
        return existing  # No actual changes, return the original

    updated_prompt = existing.model_copy(
        update=updated_fields
    )
    # Preserve the original created_at timestamp and update updated_at
    updated_prompt.created_at = existing.created_at
    updated_prompt.updated_at = get_current_time()  # Update timestamp only if changes are made

    result = await storage.update_prompt(prompt_id, updated_prompt)

    # Create new version if changes were made, then re-fetch to get the updated version field
    if result:
        await storage.create_prompt_version(prompt_id, result)
        result = await storage.get_prompt(prompt_id)

    return result


@app.delete("/prompts/{prompt_id}", status_code=204)
async def delete_prompt(prompt_id: str):
    """Deletes a prompt by its ID.

    This endpoint deletes the prompt identified by `prompt_id`. If no prompt with
    the given ID exists, it returns a 404 error.

    Args:
        prompt_id: The unique identifier of the prompt to delete.

    Returns:
        None. On success, the endpoint responds with HTTP 204 (No Content).

    Raises:
        HTTPException: If the prompt does not exist (HTTP 404, "Prompt not found").
    """
    if not await storage.delete_prompt(prompt_id):
        raise HTTPException(status_code=404, detail="Prompt not found")
    return None


# ============== Collection Endpoints ==============

@app.get("/collections", response_model=CollectionList)
async def list_collections():
    """Lists all collections.

    Retrieves all collections from storage and returns them along with the total
    number of collections. Each collection includes a ``prompt_ids`` field
    containing the IDs of all prompts currently associated with it.

    Returns:
        CollectionList: Response object containing:
            - collections: The list of all collections with ``prompt_ids`` populated.
            - total: The total number of collections returned.
    """
    collections = await storage.get_all_collections()
    enriched = [await _get_collection_with_prompt_ids(c) for c in collections]
    return CollectionList(collections=enriched, total=len(enriched))


@app.get("/collections/{collection_id}", response_model=Collection)
async def get_collection(collection_id: str):
    """Retrieves a collection by its ID.

    Looks up the collection in storage using the provided identifier and returns
    it if found, with ``prompt_ids`` populated from the current prompt set.
    If no matching collection exists, raises an HTTP 404 error.

    Args:
        collection_id (str): The ID of the collection to retrieve.

    Returns:
        Collection: The requested collection with ``prompt_ids`` populated.

    Raises:
        HTTPException: If the collection is not found (HTTP 404).
    """
    collection = await storage.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    return await _get_collection_with_prompt_ids(collection)


@app.post("/collections", response_model=Collection, status_code=201)
async def create_collection(collection_data: CollectionCreate):
    """Creates a new collection.

    Constructs a `Collection` model instance from the incoming request payload
    and persists it using the storage layer.

    Args:
        collection_data (CollectionCreate): Request payload containing the
            fields required to create a new collection.

    Returns:
        Collection: The newly created collection as persisted by the storage
            layer.
    """
    collection = Collection(**collection_data.model_dump())
    result = await storage.create_collection(collection)
    return await _get_collection_with_prompt_ids(result)


@app.put("/collections/{collection_id}", response_model=Collection)
async def update_collection(collection_id: str, collection_data: CollectionCreate):
    """Update an existing collection.

    Retrieves the collection identified by ``collection_id`` and replaces its fields
    with the values provided in ``collection_data``. The original ``created_at``
    timestamp is preserved.

    Args:
        collection_id: The unique identifier of the collection to update.
        collection_data: The updated collection fields.

    Returns:
        The updated collection as persisted by the storage layer.

    Raises:
        HTTPException: If no collection exists for ``collection_id`` (404).
    """
    existing = await storage.get_collection(collection_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Collection not found")

    updated_collection = Collection(
        id=existing.id,
        name=collection_data.name,
        description=collection_data.description,
        created_at=existing.created_at
    )

    result = await storage.update_collection(collection_id, updated_collection)
    return await _get_collection_with_prompt_ids(result)

@app.patch("/collections/{collection_id}", response_model=Collection)
async def patch_collection(collection_id: str, collection_data: CollectionUpdateOptional = Body(...)):
    """Partially updates an existing collection.

    This endpoint applies a partial update (PATCH semantics) to the collection
    identified by ``collection_id``. Only fields explicitly provided in
    ``collection_data`` are applied (unset fields are ignored).

    Args:
        collection_id: The unique identifier of the collection to update.
        collection_data: Partial collection payload. Only fields set in this object are
            applied to the existing collection.

    Returns:
        The persisted, updated collection model after applying any requested changes.
        If no fields are provided, the existing collection is returned unchanged.

    Raises:
        HTTPException: If the collection does not exist (404).
    """
    existing = await storage.get_collection(collection_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Check for actual changes using model_dump(exclude_unset=True)
    updated_fields = collection_data.model_dump(exclude_unset=True)
    if not updated_fields:
        return await _get_collection_with_prompt_ids(existing)

    # Update only the fields that are provided
    updated_collection = Collection(
        id=existing.id,
        name=collection_data.name if collection_data.name is not None else existing.name,
        description=collection_data.description if collection_data.description is not None else existing.description,
        created_at=existing.created_at
    )

    result = await storage.update_collection(collection_id, updated_collection)
    return await _get_collection_with_prompt_ids(result)

@app.delete("/collections/{collection_id}", status_code=204)
async def delete_collection(collection_id: str):
    """Deletes a collection and all prompts associated with it.

    This endpoint removes every prompt that belongs to the specified collection,
    then deletes the collection itself. If the collection does not exist, a
    404 HTTPException is raised.

    Args:
        collection_id (str): The ID of the collection to delete.

    Raises:
        HTTPException: If the collection is not found.

    Returns:
        None: Always returns ``None``. The endpoint responds with HTTP 204 (No Content)
        on success.
    """
    # Retrieve prompts in the collection
    prompts = await storage.get_prompts_by_collection_id(collection_id)

    # Delete each prompt within the collection
    for prompt in prompts:
        await storage.delete_prompt(prompt.id)

    if not await storage.delete_collection(collection_id):
        raise HTTPException(status_code=404, detail="Collection not found")

    return None

# ============== SSE Endpoint ==============

# One asyncio.Queue per connected client
sse_client_queues: list[asyncio.Queue] = []

async def notify_sse_clients(message: str):
    """Notify all SSE clients about data changes."""
    for queue in sse_client_queues:
        await queue.put(message)

@app.get("/admin/events")
async def sse_endpoint(request: Request):
    """Server-Sent Events endpoint for real-time data change notifications.

    Clients can subscribe to this endpoint to receive notifications when
    data is populated or cleared.

    Returns:
        StreamingResponse: SSE stream that sends data change events.
    """
    queue: asyncio.Queue = asyncio.Queue()
    sse_client_queues.append(queue)

    async def event_stream():
        yield 'data: {"event": "connected", "message": "Connected to SSE stream"}\n\n'
        get_task = None
        try:
            while True:
                try:
                    get_task = asyncio.ensure_future(queue.get())
                    message = await asyncio.wait_for(asyncio.shield(get_task), timeout=15)
                    get_task = None
                    yield f'data: {message}\n\n'
                except asyncio.TimeoutError:
                    get_task.cancel()
                    get_task = None
                    yield ': keep-alive\n\n'
        except asyncio.CancelledError:
            pass
        finally:
            if get_task is not None:
                get_task.cancel()
            if queue in sse_client_queues:
                sse_client_queues.remove(queue)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "cache-control",
        }
    )

# ============== Admin Endpoints ==============

from pydantic import BaseModel as _BaseModel, ValidationError, field_validator

class PopulateTestDataRequest(_BaseModel):
    num_prompts: int = 40
    num_collections: int = 4
    collection_chance: float = 0.6
    tags_per_prompt: int = 3
    random_seed: Optional[int] = None
    tag_as_test_fill: bool = False
    append_mode: bool = False
    data_source: Literal["template", "dataset"] = "dataset"

    MAX_PROMPTS: ClassVar[int] = 10_000
    MAX_COLLECTIONS: ClassVar[int] = 1_000
    MAX_TAGS_PER_PROMPT: ClassVar[int] = 500

    @field_validator("num_prompts")
    @classmethod
    def clamp_prompts(cls, v: int) -> int:
        return min(max(v, 0), cls.MAX_PROMPTS)

    @field_validator("num_collections")
    @classmethod
    def clamp_collections(cls, v: int) -> int:
        return min(max(v, 0), cls.MAX_COLLECTIONS)

    @field_validator("tags_per_prompt")
    @classmethod
    def clamp_tags(cls, v: int) -> int:
        return min(max(v, 0), cls.MAX_TAGS_PER_PROMPT)

_populate_progress: dict = {"current": 0, "total": 0, "active": False, "error": None}

_PROMPT_TOPICS = [
    "Chatbot Personality", "Data Analysis", "Creative Writing",
    "Technical Documentation", "Customer Support", "Content Generation",
    "Code Review", "API Design", "Database Optimization",
    "Security Audit", "Performance Testing", "UX Research",
    "Product Management", "Marketing Strategy", "Sales Script",
    "Email Campaign", "Social Media Post", "Blog Article",
    "Technical Interview", "System Design", "Algorithm Explanation",
    "Debugging Guide", "CI/CD Pipeline", "DevOps Best Practices",
    "Cloud Architecture", "Microservices", "Monolith Conversion",
    "API Gateway", "Service Mesh", "Containerization",
    "Orchestration", "Infrastructure as Code", "Observability",
    "Monitoring", "Logging", "Tracing", "Incident Response",
    "Disaster Recovery", "Backup Strategy", "Compliance Check",
    "Risk Assessment", "Threat Modeling", "Penetration Testing"
]

_TAG_CATEGORIES = [
    ["AI", "Machine Learning", "Deep Learning", "NLP", "Computer Vision"],
    ["Chatbot", "Virtual Assistant", "Conversational AI", "Dialogue Systems"],
    ["Data Analysis", "Data Science", "Statistics", "Visualization", "ETL"],
    ["Creative Writing", "Storytelling", "Content Creation", "Copywriting"],
    ["Technical", "Documentation", "API", "SDK", "Library"],
    ["Testing", "QA", "Automation", "Unit Test", "Integration Test"],
    ["Security", "Compliance", "Audit", "Risk", "Threat"],
    ["DevOps", "CI/CD", "Infrastructure", "Cloud", "Container"],
    ["Product", "Management", "Strategy", "Roadmap", "Prioritization"],
    ["Marketing", "Sales", "Customer", "Support", "Engagement"]
]

_COLLECTION_THEMES = [
    "AI Assistants",
    "Creative Writing Prompts",
    "Data Analysis Templates",
    "Technical Documentation",
    "Customer Support Scripts",
    "Content Generation",
    "Code Review Guidelines",
    "API Design Patterns",
    "DevOps Best Practices",
    "Security and Compliance"
]

async def _do_populate(request: PopulateTestDataRequest) -> None:
    """Background worker: generates test data and updates _populate_progress."""
    try:
        # Optionally clear existing data first
        if not request.append_mode:
            await storage.clear()

        # ── Phase 1: build all prompt objects in memory (pure Python, no I/O) ──
        rng = random.Random(request.random_seed)
        created_prompts = []

        if request.data_source == "dataset":
            from app.prompt_pool import get_pool
            samples = get_pool().sample(rng, request.num_prompts)
            for sample in samples:
                title = sample["title"]
                content = sample["content"]
                title_lower = title.lower()

                relevant_categories = [
                    cat for cat in _TAG_CATEGORIES
                    if any(any(word in title_lower for word in tag.lower().split()) for tag in cat)
                ] or rng.sample(_TAG_CATEGORIES, min(3, len(_TAG_CATEGORIES)))

                tags_set: set[str] = {rng.choice(cat) for cat in relevant_categories if cat}
                if len(tags_set) < request.tags_per_prompt:
                    flat_pool = [t for cat in _TAG_CATEGORIES for t in cat if t not in tags_set]
                    rng.shuffle(flat_pool)
                    tags_set.update(flat_pool[: request.tags_per_prompt - len(tags_set)])
                tags = list(tags_set)[: request.tags_per_prompt]
                if request.tag_as_test_fill:
                    tags.append("test fill")

                instruction = sample.get("instruction", "")
                description = instruction[:490] if instruction else None

                try:
                    created_prompts.append(Prompt(
                        id=str(uuid.uuid4()),
                        title=title[:190],
                        content=content,
                        description=description,
                        tags=list(set(tags)),
                    ))
                except ValidationError as exc:
                    logger.warning("[populate] Skipping dataset prompt — validation error: %s", exc)
                    _populate_progress["skipped"] += 1
        else:
            modifiers = [
                "Guide for", "Template for", "Best Practices for",
                "Checklist for", "Framework for", "Strategy for",
                "Tactics for", "Approach to", "Methodology for",
                "How to", "The Art of", "Mastering", "Essentials of"
            ]
            for _ in range(request.num_prompts):
                topic = rng.choice(_PROMPT_TOPICS)
                title = f"{rng.choice(modifiers)} {topic}"

                paragraphs = [
                    f"This prompt is designed to help with {rng.choice(['creating', 'developing', 'improving', 'optimizing'])} "
                    f"{rng.choice(['solutions', 'strategies', 'approaches', 'implementations'])} related to {title.lower()}. "
                    f"It provides a structured framework for {rng.choice(['generating', 'evaluating', 'documenting', 'testing'])} "
                    f"{rng.choice(['ideas', 'code', 'content', 'systems'])} in the context of {title.lower()}.",
                    "Key considerations:",
                ]
                for _ in range(3, 8):
                    paragraphs.append(
                        f"- {rng.choice(['Consider', 'Evaluate', 'Analyze', 'Document', 'Test'])} the {rng.choice(['impact', 'effectiveness', 'quality', 'performance'])} "
                        f"of {rng.choice(['your', 'the', 'this'])} {title.lower()} implementation"
                    )
                paragraphs.append("\nBest practices:")
                for _ in range(3, 6):
                    paragraphs.append(
                        f"- Always {rng.choice(['validate', 'test', 'document', 'review', 'optimize'])} your {title.lower()} "
                        f"before {rng.choice(['deployment', 'release', 'sharing', 'presentation'])}"
                    )
                paragraphs.append(
                    f"By following this prompt, you should be able to {rng.choice(['create', 'develop', 'improve', 'optimize'])} "
                    f"high-quality {title.lower()} solutions that meet your requirements."
                )

                title_lower = title.lower()
                relevant_categories = [
                    cat for cat in _TAG_CATEGORIES
                    if any(any(word in title_lower for word in tag.lower().split()) for tag in cat)
                ] or rng.sample(_TAG_CATEGORIES, min(3, len(_TAG_CATEGORIES)))

                tags_set = {rng.choice(cat) for cat in relevant_categories if cat}
                if len(tags_set) < request.tags_per_prompt:
                    flat_pool = [t for cat in _TAG_CATEGORIES for t in cat if t not in tags_set]
                    rng.shuffle(flat_pool)
                    tags_set.update(flat_pool[: request.tags_per_prompt - len(tags_set)])
                tags = list(tags_set)[: request.tags_per_prompt]
                if request.tag_as_test_fill:
                    tags.append("test fill")

                try:
                    created_prompts.append(Prompt(
                        id=str(uuid.uuid4()),
                        title=title,
                        content="\n\n".join(paragraphs),
                        description=(
                            f"A comprehensive prompt for {title.lower()}, covering key aspects and best practices. "
                            f"This template helps ensure consistency and quality in your {title.lower()} work."
                        ),
                        tags=list(set(tags)),
                    ))
                except ValidationError as exc:
                    logger.warning("[populate] Skipping template prompt — validation error: %s", exc)
                    _populate_progress["skipped"] += 1

        # ── Phase 2: batch-insert all prompts in one DB round-trip (no embeddings) ──
        _populate_progress["phase"] = "inserting"
        await storage.batch_create_prompts(created_prompts)
        num_created = len(created_prompts)
        _populate_progress["total"] = num_created
        _populate_progress["current"] = 0

        # ── Phase 3: create versions concurrently (no embeddings) ──
        _populate_progress["phase"] = "versioning"
        ver_sem = asyncio.Semaphore(20)
        version_counter = 0

        async def _create_version(p: Prompt) -> None:
            nonlocal version_counter
            async with ver_sem:
                await storage.create_prompt_version(p.id, p)
                version_counter += 1
                _populate_progress["current"] = version_counter

        await asyncio.gather(*[_create_version(p) for p in created_prompts])

        # ── Phase 4: create collections + bulk-assign prompts (no embeddings) ──
        _populate_progress["phase"] = "collections"
        created_collections = []
        for _ in range(request.num_collections):
            name = rng.choice(_COLLECTION_THEMES)
            collection_obj = Collection(
                id=str(uuid.uuid4()),
                name=name,
                description=(
                    f"A curated collection of prompts focused on {name.lower()}. "
                    f"These templates help standardize and improve your work in this area."
                ),
            )
            await storage.create_collection(collection_obj)
            created_collections.append(collection_obj)

        if created_collections:
            _populate_progress["phase"] = "assigning"
            assignments = [
                (p.id, rng.choice(created_collections).id)
                for p in created_prompts
                if rng.random() < request.collection_chance
            ]
            chunk_size = 500
            for i in range(0, len(assignments), chunk_size):
                chunk = assignments[i : i + chunk_size]
                await storage.batch_update_collection_ids(chunk)

        _populate_progress["prompts_created"] = len(created_prompts)
        _populate_progress["collections_created"] = len(created_collections)
        # Notify clients about data change
        await notify_sse_clients('{"event": "data_changed", "message": "Test data populated", "action": "populate"}')

        # ── Phase 5: embedding backfill ──
        _populate_progress["phase"] = "embeddings"
        try:
            from app.embeddings import generate_embedding
            await storage.backfill_embeddings(generate_fn=generate_embedding)
        except Exception as e:
            logging.getLogger(__name__).warning("Embedding backfill failed: %s", e)

        _populate_progress["phase"] = "done"
        _populate_progress["active"] = False

    except Exception as e:
        _populate_progress["active"] = False
        _populate_progress["error"] = str(e)
        print(f"[populate background task] Error: {e}")


@app.post("/admin/populate-test-data", status_code=202)
async def populate_test_data(
    background_tasks: BackgroundTasks,
    request: PopulateTestDataRequest = PopulateTestDataRequest(),
):
    """Start test-data generation in the background and return immediately.

    Returns 202 Accepted. Clients poll /admin/populate-status for progress.
    Returns 409 Conflict if a generation is already running.
    """
    global _populate_progress

    if _populate_progress.get("active"):
        raise HTTPException(status_code=409, detail="A populate operation is already in progress.")

    # Seed in-request so determinism is preserved even in background context
    if request.random_seed is not None:
        random.seed(request.random_seed)
    else:
        random.seed()

    _populate_progress = {"current": 0, "total": request.num_prompts, "active": True, "error": None, "prompts_created": 0, "collections_created": 0, "skipped": 0, "phase": "generating"}

    background_tasks.add_task(_do_populate, request)

    return {"status": "started", "total": request.num_prompts}

@app.delete("/admin/clear-all-data")
async def clear_all_data():
    """Clear all prompts and collections from the database.

    This endpoint clears all data from storage, including prompts,
    collections, and their version history.

    Returns:
        A response object containing:
            - status: Operation status
            - message: Success message
            - prompts_removed: Number of prompts removed
            - collections_removed: Number of collections removed
    """
    try:
        # Count items before clearing
        prompts_before = len(await storage.get_all_prompts())
        collections_before = len(await storage.get_all_collections())

        # Clear all data
        await storage.clear()

        # Notify clients about data change
        await notify_sse_clients('{"event": "data_changed", "message": "All data cleared", "action": "clear"}')

        return {
            "status": "success",
            "message": "All data cleared successfully",
            "prompts_removed": prompts_before,
            "collections_removed": collections_before
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear data: {str(e)}"
        )

@app.get("/admin/populate-status")
async def get_populate_status():
    """Return the current progress of an in-flight populate-test-data operation."""
    return _populate_progress


@app.delete("/admin/clear-test-data")
async def clear_test_data():
    """Delete only prompts tagged with 'test fill'.

    Returns:
        A response object containing:
            - status: Operation status
            - prompts_removed: Number of prompts deleted
    """
    try:
        all_prompts = await storage.get_all_prompts()
        test_prompts = [p for p in all_prompts if p.tags and "test fill" in p.tags]
        for p in test_prompts:
            await storage.delete_prompt(p.id)

        await notify_sse_clients('{"event": "data_changed", "message": "Test data cleared", "action": "clear_test"}')

        return {
            "status": "success",
            "message": f"Removed {len(test_prompts)} prompt(s) tagged 'test fill'",
            "prompts_removed": len(test_prompts)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear test data: {str(e)}"
        )


@app.get("/admin/embedding-status")
async def embedding_status():
    """Return the number of prompts with and without embeddings.

    Used by the frontend to display an embedding progress indicator.

    Returns:
        A response object containing:
            - total: Total number of prompts
            - embedded: Number of prompts that have an embedding
            - complete: True when all prompts have embeddings (or total is 0)
    """
    all_prompts = await storage.get_all_prompts()
    total = len(all_prompts)
    embedded = await storage.count_embedded_prompts()
    return {"total": total, "embedded": embedded, "complete": total == 0 or embedded == total}


@app.post("/admin/backfill-embeddings")
async def backfill_embeddings():
    """Generate embeddings for all prompts that do not have one.

    Loads the sentence-transformers model on first call (may take a few seconds).
    Re-running this endpoint is safe — it skips prompts that already have embeddings.

    Returns:
        A response object containing:
            - status: Operation status ("success")
            - updated: Number of prompts that received embeddings
            - message: Human-readable summary
    """
    try:
        from app.embeddings import generate_embedding
        updated = await storage.backfill_embeddings(generate_fn=generate_embedding)
        return {
            "status": "success",
            "updated": updated,
            "message": f"Embeddings generated for {updated} prompt(s).",
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=f"Model unavailable: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

# ============== Versioning Endpoints ==============

@app.get("/prompts/{prompt_id}/versions", response_model=VersionList)
async def list_prompt_versions(prompt_id: str):
    """List all versions of a prompt.

    Retrieves all versions of the specified prompt, sorted by version number
    (newest first).

    Args:
        prompt_id: The unique identifier of the prompt.

    Returns:
        VersionList: A list of all versions with metadata.

    Raises:
        HTTPException: If the prompt does not exist (404).
    """
    prompt = await storage.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    versions = await storage.get_all_prompt_versions(prompt_id)

    # Create version summaries
    version_summaries = [
        VersionSummary(
            version=v.version,
            created_at=v.created_at,
            title=v.title,
            description=v.description
        )
        for v in versions
    ]

    return VersionList(
        prompt_id=prompt_id,
        versions=version_summaries,
        total=len(versions)
    )

@app.get("/prompts/{prompt_id}/versions/{version}", response_model=PromptVersion)
async def get_prompt_version(prompt_id: str, version: int):
    """Get a specific version of a prompt.

    Retrieves the specified version of a prompt as an immutable snapshot.

    Args:
        prompt_id: The unique identifier of the prompt.
        version: The version number to retrieve.

    Returns:
        PromptVersion: The version snapshot.

    Raises:
        HTTPException: If the prompt or version does not exist (404).
    """
    prompt = await storage.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    version_data = await storage.get_prompt_version(prompt_id, version)
    if not version_data:
        raise HTTPException(status_code=404, detail="Version not found")

    return version_data

@app.post("/prompts/{prompt_id}/versions/{version}/promote", response_model=Prompt, status_code=201)
async def promote_prompt_version(prompt_id: str, version: int):
    """Promote an old version to become the new latest version.

    Creates a new version that is a copy of the specified old version, making it
    the current version.

    Args:
        prompt_id: The unique identifier of the prompt.
        version: The version number to promote.

    Returns:
        Prompt: The new latest version of the prompt.

    Raises:
        HTTPException: If the prompt or version does not exist (404).
    """
    prompt = await storage.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    promoted_prompt = await storage.promote_prompt_version(prompt_id, version)
    if not promoted_prompt:
        raise HTTPException(status_code=404, detail="Version not found")

    return promoted_prompt
