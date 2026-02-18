"""FastAPI routes for PromptLab"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from fastapi import FastAPI, HTTPException, Path, Body
from app.models import Prompt, PromptUpdateOptional

from app.models import (
    Prompt, PromptCreate, PromptUpdate,
    Collection, CollectionCreate,
    PromptList, CollectionList, HealthResponse,
    get_current_time
)
from app.storage import storage
from app.utils import sort_prompts_by_date, filter_prompts_by_collection, search_prompts
from app import __version__


"""Initialize the FastAPI application instance.

Creates the central ASGI application object for PromptLab. The application is
configured with basic OpenAPI metadata (title, description, version), which is
used for generated API documentation and client integrations.

Args:
    None.

Returns:
    fastapi.FastAPI: A configured FastAPI application instance with OpenAPI
    metadata set (title, description, version).

Raises:
    None.
"""
app = FastAPI(
    title="PromptLab API",
    description="AI Prompt Engineering Platform",
    version=__version__
)

# CORS middleware
"""Configure Cross-Origin Resource Sharing (CORS) middleware for the application.

This registers FastAPI/Starlette's :class:`~starlette.middleware.cors.CORSMiddleware`
on the application instance to control how browsers handle cross-origin requests.

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

Args:
    None: This block does not take parameters; it mutates the application by
        adding middleware.

Returns:
    None: The middleware is registered for its side effects.
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    search: Optional[str] = None
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

    Returns:
        A `PromptList` containing the resulting list of prompts and the total
        number of prompts returned.
    """
    prompts = storage.get_all_prompts()
    
    # Filter by collection if specified
    if collection_id:
        prompts = filter_prompts_by_collection(prompts, collection_id)
    
    # Search if query provided
    if search:
        prompts = search_prompts(prompts, search)
    
    # Sort by date (newest first)
    # Note: There might be an issue with the sorting...
    prompts = sort_prompts_by_date(prompts, descending=True)
    
    return PromptList(prompts=prompts, total=len(prompts))


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
def create_prompt(prompt_data: PromptCreate):
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
    """
    # Validate collection exists if provided
    if prompt_data.collection_id:
        collection = storage.get_collection(prompt_data.collection_id)
        if not collection:
            raise HTTPException(status_code=400, detail="Collection not found")
    
    prompt = Prompt(**prompt_data.model_dump())
    return storage.create_prompt(prompt)


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
        created_at=existing.created_at,
        updated_at=get_current_time()
    )
    
    return storage.update_prompt(prompt_id, updated_prompt)


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

    # Check for actual changes
    updated_fields = prompt_data.dict(exclude_unset=True)
    if updated_fields:
        updated_prompt = existing.model_copy(
            update=updated_fields
        )
        updated_prompt.updated_at = get_current_time()  # Update timestamp only if changes are made
    else:
        updated_prompt = existing  # No changes, keep the original
    
    return storage.update_prompt(prompt_id, updated_prompt)


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
    return CollectionList(collections=collections, total=len(collections))


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
    return collection


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

