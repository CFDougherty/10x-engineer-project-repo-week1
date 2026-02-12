# Project Architecture

## Overview

This document provides a high-level architecture overview of the PromptLab project, detailing its main components and interdependencies.

### Main Components:

- **main.py**: Entry point of the application using Uvicorn to run FastAPI.
- **app module**: Core logic and API endpoints of PromptLab.

## Component Structure

### 1. `main.py`
- Runs the `FastAPI` application using `uvicorn`.
- References `app` from `app.api` for routing.

### 2. `app/__init__.py`
- Initializes the application with the current version.

### 3. `app/storage.py`
- **Storage Class**:
  - Maintains in-memory dictionaries for `Prompt` and `Collection`.
  - **CRUD Operations for Prompts**:
    - **`create_prompt(prompt: Prompt) -> Prompt`**: Adds a `Prompt` object to storage, using its unique ID. Dependencies include the `Prompt` model; potential failure mode includes overwriting existing prompts with the same ID.
    - **`get_prompt(prompt_id: str) -> Optional[Prompt]`**: Retrieves a prompt by its ID. Returns `None` if not found.
    - **`get_all_prompts() -> List[Prompt]`**: Fetches all prompts, potentially returning an empty list.
    - **`update_prompt(prompt_id: str, prompt: Prompt) -> Optional[Prompt]`**: Updates a `Prompt` if it exists; returns `None` otherwise. Dependencies require valid `Prompt` data.
    - **`delete_prompt(prompt_id: str) -> bool`**: Deletes a prompt by ID, returning `False` if the prompt is non-existent.
  - **Collection Operations**:
    - **`create_collection(collection: Collection) -> Collection`**: Stores a `Collection`. Similar overwrite risks exist as with prompts.
    - **`get_collection(collection_id: str) -> Optional[Collection]`**: Fetches a collection or returns `None`.
    - **`get_all_collections() -> List[Collection]`**: Retrieves all stored collections or an empty list.
    - **`delete_collection(collection_id: str) -> bool`**: Removes a collection; does not handle prompts linked to it, risking orphaned data.
  - **Utilities**:
    - **`get_prompts_by_collection(collection_id: str) -> List[Prompt]`**: Lists prompts belonging to a collection, or an empty list if none.
    - **`clear()`**: Wipes all data, a critical operation with no recovery unless external persistence is implemented.

### 4. `app/models.py`
- **Models**:
  - `Prompt` and `Collection` data models with base, creation, and update forms.
  - Utility functions for generating UUIDs and timestamps.

### 5. `app/utils.py`
- **Utility Functions**:
  - Sorting prompts by date (Note: Currently has a bug regarding sorting order).
  - Filtering prompts by collection.
  - Searching through prompts.
  - Validating prompt content.
  - Extracting variables from prompt content.

### 6. `app/api.py`
- **FastAPI Application**:
  - Configured with CORS middleware.
  - **Routes**:
    - `GET /health`: Health check endpoint.
    - `GET /prompts`: List prompts with optional `collection_id` filtering and search.
    - `GET /prompts/{prompt_id}`: Retrieve a specific prompt.
    - `POST /prompts`: Create a new prompt.
    - `PUT /prompts/{prompt_id}`: Update a specific prompt.
    - `DELETE /prompts/{prompt_id}`: Delete a prompt.
    - `GET /collections`: List collections.
    - `GET /collections/{collection_id}`: Retrieve a specific collection.
    - `POST /collections`: Create a new collection.
    - `DELETE /collections/{collection_id}`: Delete a collection. 
  - Handles data operations by leveraging storage and data models.
  - Implements validations and processes potential bugs, especially in sorting, invalid updates, and orphaned relationships after deletions.


## Dependencies:
- Internal dependencies consist of cross-module method calls and class instantiations.
- Utilizes `fastapi`, `uvicorn`, `pydantic`, and standard Python libraries such as `datetime` and `uuid`.  

**Note**: Some functionalities are marked with existing bugs or unimplemented features, such as the POST update timestamp bug and handling orphaned collections.

