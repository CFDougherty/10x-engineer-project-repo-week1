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


# ============== Health Check ==============

@app.get("/health", response_model=HealthResponse)
def health_check():
    """
    Return the health status and version of the application.

    Returns:
        HealthResponse: The health status and version.
    """
    return HealthResponse(status="healthy", version=__version__)


# ============== Prompt Endpoints ==============

@app.get("/prompts", response_model=PromptList)
def list_prompts(
    collection_id: Optional[str] = None,
    search: Optional[str] = None
    ):
    """Retrieve a list of prompts, optionally filtered by collection or search query.
    
    Args:
        collection_id: Optional; The ID of the collection to filter prompts by.
        search: Optional; The search term to filter prompts.

    Returns:
        PromptList: An object containing the list of prompts and the total count.
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
    """Fetch a prompt by its ID.

    Args:
        prompt_id: The ID of the prompt to retrieve.

    Returns:
        The prompt associated with the given ID.

    Raises:
        HTTPException: If no prompt is found with the given ID.
    """
    prompt = storage.get_prompt(prompt_id)
    
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    return prompt


@app.post("/prompts", response_model=Prompt, status_code=201)
def create_prompt(prompt_data: PromptCreate):
    """Create a new prompt and store it in the database.

    Args:
        prompt_data: Data required to create a new prompt.

    Returns:
        The created prompt object.

    Raises:
        HTTPException: If the specified collection does not exist.

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
    """
    Partially update the specified prompt.
    
    Args:
        prompt_id: The ID of the prompt to update.
        prompt_data: The new data for the prompt. Only non-null fields will be updated.
    
    Returns:
        The updated prompt.
    
    Raises:
        HTTPException: If the prompt does not exist or if the collection_id is invalid.
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
    """Delete a prompt with the given prompt ID.

    Args:
        prompt_id: The ID of the prompt to delete.

    Raises:
        HTTPException: If the prompt is not found.
    
    Returns:
        None
    """
    if not storage.delete_prompt(prompt_id):
        raise HTTPException(status_code=404, detail="Prompt not found")
    return None


# ============== Collection Endpoints ==============

@app.get("/collections", response_model=CollectionList)
def list_collections():
    """Retrieve and return a list of all collections.

    Returns:
        CollectionList: An object containing the collections and their total count.
    """
    collections = storage.get_all_collections()
    return CollectionList(collections=collections, total=len(collections))


@app.get("/collections/{collection_id}", response_model=Collection)
def get_collection(collection_id: str):
    """Retrieve a collection by its ID.

    Args:
        collection_id: The ID of the collection to retrieve.

    Returns:
        The requested collection.

    Raises:
        HTTPException: If the collection is not found.
    """
    collection = storage.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@app.post("/collections", response_model=Collection, status_code=201)
def create_collection(collection_data: CollectionCreate):
    """
    Create a new collection.

    Args:
        collection_data: The data required to create a new collection.

    Returns:
        A newly created Collection object.
    """
    collection = Collection(**collection_data.model_dump())
    return storage.create_collection(collection)


@app.delete("/collections/{collection_id}", status_code=204)
def delete_collection(collection_id: str):
    """
    Delete a collection and its associated prompts.

    Args:
        collection_id: The ID of the collection to delete.

    Raises:
        HTTPException: If the collection is not found.

    Returns:
        None
    """
    # Retrieve prompts in the collection
    prompts = storage.get_prompts_by_collection_id(collection_id)
    
    # Delete each prompt within the collection
    for prompt in prompts:
        storage.delete_prompt(prompt.id)

    if not storage.delete_collection(collection_id):
        raise HTTPException(status_code=404, detail="Collection not found")

    return None

