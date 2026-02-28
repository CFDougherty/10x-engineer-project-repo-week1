"""FastAPI routes for PromptLab.

This module defines the FastAPI application instance and its HTTP routes.

The application is configured with basic OpenAPI metadata (title, description,
version), which is used for generated API documentation and client integrations.

This module also configures Cross-Origin Resource Sharing (CORS) middleware on
the application instance to control how browsers handle cross-origin requests.

The current configuration is fully permissive:
- Allows requests from any origin (``allow_origins=["*"]``).
- Allows cookies/authorization headers to be included (``allow_credentials=True``).
- Allows all HTTP methods and headers (``allow_methods=["*"]``,
  ``allow_headers=["*"]``).

Note:
    Using ``allow_origins=["*"]`` together with ``allow_credentials=True`` is not
    valid under the CORS specification for credentialed browser requests; browsers
    will typically reject such responses unless a specific origin is echoed back.
    Prefer explicitly listing allowed origins when credentials are required.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi import status
from typing import Optional
import uuid
import asyncio
from fastapi import FastAPI, HTTPException, Path, Body, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi import Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi import Depends, Request
from app.models import Prompt, PromptUpdateOptional

from app.models import (
    Prompt, PromptCreate, PromptUpdate,
    Collection, CollectionCreate, CollectionUpdateOptional,
    PromptList, CollectionList, HealthResponse,
    get_current_time,
    PromptVersion, VersionList, VersionSummary
)
from app.storage import storage
from app.utils import sort_prompts_by_date, filter_prompts_by_collection, search_prompts
from app import __version__


app = FastAPI(
    title="PromptLab API",
    description="AI Prompt Engineering Platform",
    version=__version__
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
    """Handle HTTP exceptions, including unsupported media type."""
    if exc.status_code == 415:
        return PlainTextResponse(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            content="Unsupported media type"
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# ============== Health Check ==============

@app.get("/health", response_model=HealthResponse)
def health_check():
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
def list_prompts(
    collection_id: Optional[str] = None,
    search: Optional[str] = None,
    filter: Optional[str] = None,  # 'title', 'description', 'tags', 'collection', or 'all'
    fuzzy: bool = True,
    limit: Optional[int] = None,
    offset: Optional[int] = None
):
    """Lists prompts, optionally filtered by collection and/or a search query.

    This endpoint retrieves all prompts from storage, applies an optional
    collection filter, applies an optional text search filter, then sorts the
    resulting prompts by date (newest first).

    Args:
        collection_id: Optional collection ID used to filter prompts. If
            provided, only prompts belonging to this collection are returned.
        search: Optional search term used to filter prompts. If provided, only
            prompts matching the query are returned.
        filter: Optional field to filter search by. One of: 'title', 'description',
            'tags', 'collection', or 'all'. Default: 'all' (search all fields).
        fuzzy: If True (default), uses fuzzy string matching for search. If False, uses exact substring matching.
        limit: Optional maximum number of prompts to return.
        offset: Optional offset for pagination.

    Returns:
        A `PromptList` containing the resulting list of prompts and the total
        number of prompts returned.
    """
    all_prompts = storage.get_all_prompts()

    # Filter by collection if specified
    if collection_id:
        all_prompts = filter_prompts_by_collection(all_prompts, collection_id)

    # Search logic
    if search:
        # Determine which fields to search based on filter parameter
        # Default to 'all' if filter is not specified
        search_filter = filter if filter is not None else 'all'

        # Use search_prompts for all filter types to ensure consistent behavior
        all_prompts = search_prompts(all_prompts, search, fuzzy=fuzzy, search_field=search_filter)

    # Sort by date (newest first)
    all_prompts = sort_prompts_by_date(all_prompts, descending=True)

    # Calculate total before pagination
    total = len(all_prompts)

    # Apply pagination
    if offset is not None:
        all_prompts = all_prompts[offset:]
    if limit is not None:
        all_prompts = all_prompts[:limit]

    return PromptList(prompts=all_prompts, total=total)


@app.get("/prompts/{prompt_id}", response_model=Prompt)
def get_prompt(prompt_id: str):
    """Retrieves a prompt by its unique identifier.

    Args:
        prompt_id (str): The unique ID of the prompt to retrieve.

    Returns:
        Prompt: The prompt associated with ``prompt_id``.

    Raises:
        HTTPException: Raised with status code 404 if no prompt exists for the
            given ``prompt_id``.
    """
    prompt = storage.get_prompt(prompt_id)
    
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    return prompt


@app.post("/prompts", response_model=Prompt, status_code=201)
def create_prompt(prompt_data: PromptCreate, request: Request):
    """Creates a new prompt and persists it to storage.

    If `prompt_data.collection_id` is provided, this endpoint validates that the
    referenced collection exists before creating the prompt. If the collection
    does not exist, a 400 error is returned.

    Args:
        prompt_data (PromptCreate): Payload containing the fields required to
            create a new prompt. If `collection_id` is provided, it must refer
            to an existing collection.
        request: The request object to check content type.

    Returns:
        Prompt: The newly created prompt as stored in the database.

    Raises:
        HTTPException: Raised with status code 400 if `prompt_data.collection_id`
            is provided but no matching collection is found.
        HTTPException: Raised with status code 415 if the content type is not
            application/json.
    """
    # Validate content type
    content_type = request.headers.get("content-type", "")
    if "application/json" not in content_type:
        raise HTTPException(status_code=415, detail="Unsupported media type")

    # Validate collection exists if provided
    if prompt_data.collection_id:
        collection = storage.get_collection(prompt_data.collection_id)
        if not collection:
            raise HTTPException(status_code=400, detail="Collection not found")

    prompt = Prompt(**prompt_data.model_dump())
    created_prompt = storage.create_prompt(prompt)

    # Create version 1
    storage.create_prompt_version(prompt.id, prompt)

    return created_prompt


@app.put("/prompts/{prompt_id}", response_model=Prompt)
def update_prompt(prompt_id: str, prompt_data: PromptUpdate):
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
    existing = storage.get_prompt(prompt_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Validate collection if provided
    if prompt_data.collection_id:
        collection = storage.get_collection(prompt_data.collection_id)
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

    result = storage.update_prompt(prompt_id, updated_prompt)

    # Create new version
    if result:
        storage.create_prompt_version(prompt_id, result)

    return result


@app.patch("/prompts/{prompt_id}", response_model=Prompt)
def patch_prompt(prompt_id: str, prompt_data: PromptUpdateOptional = Body(...)):
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
    existing = storage.get_prompt(prompt_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Validate new collection_id
    if prompt_data.collection_id:
        collection = storage.get_collection(prompt_data.collection_id)
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

    result = storage.update_prompt(prompt_id, updated_prompt)

    # Create new version if changes were made
    if result:
        storage.create_prompt_version(prompt_id, result)

    return result


@app.delete("/prompts/{prompt_id}", status_code=204)
def delete_prompt(prompt_id: str):
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
    if not storage.delete_prompt(prompt_id):
        raise HTTPException(status_code=404, detail="Prompt not found")
    return None


# ============== Collection Endpoints ==============

@app.get("/collections", response_model=CollectionList)
def list_collections():
    """Lists all collections.

    Retrieves all collections from storage and returns them along with the total
    number of collections.

    Returns:
        CollectionList: Response object containing:
            - collections: The list of all collections.
            - total: The total number of collections returned.
    """
    collections = storage.get_all_collections()

    # Update each collection with its prompt_ids
    updated_collections = []
    for collection in collections:
        prompts = storage.get_prompts_by_collection_id(collection.id)
        prompt_ids = [p.id for p in prompts]

        updated_collection = Collection(
            id=collection.id,
            name=collection.name,
            description=collection.description,
            created_at=collection.created_at,
            prompt_ids=prompt_ids
        )
        updated_collections.append(updated_collection)

    return CollectionList(collections=updated_collections, total=len(updated_collections))


@app.get("/collections/{collection_id}", response_model=Collection)
def get_collection(collection_id: str):
    """Retrieves a collection by its ID.

    Looks up the collection in storage using the provided identifier and returns
    it if found. If no matching collection exists, raises an HTTP 404 error.

    Args:
        collection_id (str): The ID of the collection to retrieve.

    Returns:
        Collection: The requested collection.

    Raises:
        HTTPException: If the collection is not found (HTTP 404).
    """
    collection = storage.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Get all prompts in this collection
    prompts = storage.get_prompts_by_collection_id(collection_id)
    prompt_ids = [p.id for p in prompts]

    # Return collection with updated prompt_ids
    return Collection(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        created_at=collection.created_at,
        prompt_ids=prompt_ids
    )


@app.post("/collections", response_model=Collection, status_code=201)
def create_collection(collection_data: CollectionCreate):
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
    return storage.create_collection(collection)


@app.put("/collections/{collection_id}", response_model=Collection)
def update_collection(collection_id: str, collection_data: CollectionCreate):
    """Update an existing collection.

    Retrieves the collection identified by ``collection_id`` and replaces its fields
    with the values provided in ``collection_data``.

    Args:
        collection_id: The unique identifier of the collection to update.
        collection_data: The updated collection fields.

    Returns:
        The updated collection as persisted by the storage layer.

    Raises:
        HTTPException: If no collection exists for ``collection_id`` (404).
    """
    existing = storage.get_collection(collection_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Collection not found")

    updated_collection = Collection(
        id=existing.id,
        name=collection_data.name,
        description=collection_data.description,
        created_at=existing.created_at
    )

    result = storage.create_collection(updated_collection)
    return result

@app.patch("/collections/{collection_id}", response_model=Collection)
def patch_collection(collection_id: str, collection_data: CollectionUpdateOptional = Body(...)):
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
    existing = storage.get_collection(collection_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Check for actual changes using model_dump(exclude_unset=True)
    updated_fields = collection_data.model_dump(exclude_unset=True)
    if not updated_fields:
        return existing  # Return unchanged if no fields provided

    # Update only the fields that are provided
    updated_collection = Collection(
        id=existing.id,
        name=collection_data.name if collection_data.name is not None else existing.name,
        description=collection_data.description if collection_data.description is not None else existing.description,
        created_at=existing.created_at
    )

    result = storage.create_collection(updated_collection)
    return result

@app.delete("/collections/{collection_id}", status_code=204)
def delete_collection(collection_id: str):
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
    prompts = storage.get_prompts_by_collection_id(collection_id)

    # Delete each prompt within the collection
    for prompt in prompts:
        storage.delete_prompt(prompt.id)

    if not storage.delete_collection(collection_id):
        raise HTTPException(status_code=404, detail="Collection not found")

    return None

# ============== SSE Endpoint ==============

# Store active SSE connections and their message queues
from collections import defaultdict, deque
sse_connections = defaultdict(list)

async def notify_sse_clients(message: str):
    """Notify all SSE clients about data changes."""
    import asyncio
    tasks = []
    for connection in sse_connections["clients"]:
        try:
            # Create SSE message
            sse_message = f"data: {message}\n\n"
            await connection.write(sse_message)
            await connection.drain()
        except Exception as e:
            # Remove disconnected clients
            if connection in sse_connections["clients"]:
                sse_connections["clients"].remove(connection)
    await asyncio.gather(*tasks, return_exceptions=True)

@app.get("/admin/events")
async def sse_endpoint(request: Request):
    """Server-Sent Events endpoint for real-time data change notifications.

    Clients can subscribe to this endpoint to receive notifications when
    data is populated or cleared.

    Returns:
        StreamingResponse: SSE stream that sends data change events.
    """
    async def event_stream():
        # Send initial connection confirmation
        yield 'data: {"event": "connected", "message": "Connected to SSE stream"}\n\n'

        # Keep connection open indefinitely
        while True:
            try:
                # Send keep-alive every 15 seconds
                await asyncio.sleep(15)
                yield ': keep-alive\n\n'

            except asyncio.CancelledError:
                # Connection was closed by client
                raise
            except Exception as e:
                # Log error and continue
                print(f"SSE stream error: {e}")
                await asyncio.sleep(1)
                yield ': keep-alive\n\n'

    response = StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "cache-control",
        }
    )

    # Register client connection after creating the response
    sse_connections["clients"].append(response)

    # Clean up on disconnection
    async def cleanup():
        if response in sse_connections["clients"]:
            sse_connections["clients"].remove(response)

    response.on_disconnect = cleanup

    return response

# ============== Admin Endpoints ==============

@app.post("/admin/populate-test-data")
async def populate_test_data():
    """Populate the database with realistic test data.

    This endpoint directly calls the data generation functions to create
    sample prompts and collections for testing purposes.

    Returns:
        A response object containing:
            - status: Operation status
            - message: Success message
            - prompts_created: Number of prompts created
            - collections_created: Number of collections created
    """
    try:
        # Clear existing data first
        storage.clear()

        # Define prompt topics
        prompt_topics = [
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

        # Define tag categories
        tag_categories = [
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

        # Define collection themes
        collection_themes = [
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

        # Generate prompts
        import random
        random.seed(42)  # For reproducible results

        created_prompts = []
        for i in range(40):
            topic = random.choice(prompt_topics)
            modifiers = [
                "Guide for", "Template for", "Best Practices for",
                "Checklist for", "Framework for", "Strategy for",
                "Tactics for", "Approach to", "Methodology for",
                "How to", "The Art of", "Mastering", "Essentials of"
            ]
            modifier = random.choice(modifiers)
            title = f"{modifier} {topic}"

            # Generate content
            paragraphs = []
            paragraphs.append(
                f"This prompt is designed to help with {random.choice(['creating', 'developing', 'improving', 'optimizing'])} "
                f"{random.choice(['solutions', 'strategies', 'approaches', 'implementations'])} related to {title.lower()}. "
                f"It provides a structured framework for {random.choice(['generating', 'evaluating', 'documenting', 'testing'])} "
                f"{random.choice(['ideas', 'code', 'content', 'systems'])} in the context of {title.lower()}."
            )

            paragraphs.append("Key considerations:")
            for j in range(3, 8):
                paragraphs.append(
                    f"- {random.choice(['Consider', 'Evaluate', 'Analyze', 'Document', 'Test'])} the {random.choice(['impact', 'effectiveness', 'quality', 'performance'])} "
                    f"of {random.choice(['your', 'the', 'this'])} {title.lower()} implementation"
                )

            paragraphs.append("\nBest practices:")
            for j in range(3, 6):
                paragraphs.append(
                    f"- Always {random.choice(['validate', 'test', 'document', 'review', 'optimize'])} your {title.lower()} "
                    f"before {random.choice(['deployment', 'release', 'sharing', 'presentation'])}"
                )

            paragraphs.append(
                f"By following this prompt, you should be able to {random.choice(['create', 'develop', 'improve', 'optimize'])} "
                f"high-quality {title.lower()} solutions that meet your requirements."
            )

            content = "\n\n".join(paragraphs)
            description = (
                f"A comprehensive prompt for {title.lower()}, covering key aspects and best practices. "
                f"This template helps ensure consistency and quality in your {title.lower()} work."
            )

            # Generate tags
            relevant_categories = []
            title_lower = title.lower()
            for category in tag_categories:
                for tag in category:
                    if any(word in title_lower for word in tag.lower().split()):
                        relevant_categories.append(category)
                        break

            if not relevant_categories:
                relevant_categories = random.sample(tag_categories, min(3, len(tag_categories)))

            tags = []
            for category in relevant_categories[:3]:
                if category:
                    tags.append(random.choice(category))

            while len(tags) < 3:
                generic_tags = ["AI", "Template", "Best Practices", "Guide", "Framework"]
                new_tag = random.choice(generic_tags)
                if new_tag not in tags:
                    tags.append(new_tag)

            # Create prompt
            from app.models import Prompt
            prompt_obj = Prompt(
                id=str(uuid.uuid4()),
                title=title,
                content=content,
                description=description,
                tags=list(set(tags))  # Remove duplicates
            )
            storage.create_prompt(prompt_obj)
            storage.create_prompt_version(prompt_obj.id, prompt_obj)
            created_prompts.append(prompt_obj)

        # Generate collections
        created_collections = []
        for i in range(4):
            name = random.choice(collection_themes)
            description = (
                f"A curated collection of prompts focused on {name.lower()}. "
                f"These templates help standardize and improve your work in this area."
            )

            from app.models import Collection
            collection_obj = Collection(
                id=str(uuid.uuid4()),
                name=name,
                description=description
            )
            storage.create_collection(collection_obj)
            created_collections.append(collection_obj)

        # Randomly assign prompts to collections
        for prompt in created_prompts:
            if random.random() < 0.6 and created_collections:  # 60% chance
                collection = random.choice(created_collections)
                prompt.collection_id = collection.id
                storage.update_prompt(prompt.id, prompt)

        # Notify clients about data change
        await notify_sse_clients('{"event": "data_changed", "message": "Test data populated", "action": "populate"}')

        return {
            "status": "success",
            "message": "Test data populated successfully",
            "prompts_created": len(created_prompts),
            "collections_created": len(created_collections)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to populate test data: {str(e)}"
        )

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
        prompts_before = len(storage.get_all_prompts())
        collections_before = len(storage.get_all_collections())

        # Clear all data
        storage.clear()

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

# ============== Versioning Endpoints ==============

@app.get("/prompts/{prompt_id}/versions", response_model=VersionList)
def list_prompt_versions(prompt_id: str):
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
    prompt = storage.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    versions = storage.get_all_prompt_versions(prompt_id)

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
def get_prompt_version(prompt_id: str, version: int):
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
    prompt = storage.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    version_data = storage.get_prompt_version(prompt_id, version)
    if not version_data:
        raise HTTPException(status_code=404, detail="Version not found")

    return version_data

@app.post("/prompts/{prompt_id}/versions/{version}/promote", response_model=Prompt, status_code=201)
def promote_prompt_version(prompt_id: str, version: int):
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
    prompt = storage.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    promoted_prompt = storage.promote_prompt_version(prompt_id, version)
    if not promoted_prompt:
        raise HTTPException(status_code=404, detail="Version not found")

    return promoted_prompt
