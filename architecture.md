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
  - **Prompt Models**:
    - **`PromptBase`**: A base class for prompts with fields for title, content, description, and an optional collection ID.
      - **Dependencies**: Uses fields and types from Pydantic (`BaseModel`, `Field`), `Optional` from `typing`.
      - **Expected Input**: Title and content strings must be non-empty, with respective length constraints.
      - **Expected Output**: An instance of `PromptBase` with validated fields.
      - **Failure Modes**: It will raise validation errors if constraints are not met (e.g., empty title).
    - **`PromptCreate`**: Inherits from `PromptBase`, used for creating new prompts.
    - **`PromptUpdate`**: Inherits from `PromptBase`, used for updating existing prompts.
    - **`Prompt`**: Extends `PromptBase` and includes auto-generated fields: `id`, `created_at`, `updated_at`.
      - **Dependencies**: Relies on `generate_id` and `get_current_time` utility functions.
      - **Failure Modes**: Misuse of factory for ID or timestamps might lead to incorrect data states, but Pydantic handles field defaults gracefully.
  
  - **Collection Models**:
    - **`CollectionBase`**: A base class representing a collection with a name and an optional description.
      - **Dependencies**: Utilizes Pydantic for field validation.
      - **Expected Input**: Name must be a non-empty string.
      - **Expected Output**: Validated instance of `CollectionBase`.
      - **Failure Modes**: Similar validation failures as `PromptBase`.
    - **`CollectionCreate`**: Inherits from `CollectionBase`, used for creating collections.
    - **`Collection`**: Extends `CollectionBase` with fields for `id` and `created_at`.
      - **Dependencies**: Uses `generate_id` and `get_current_time` for default IDs and timestamps.
  
  - **Utility Functions**:
    - **`generate_id()`**: Generates a random UUID for model instances.
      - **Dependencies**: Uses `uuid4` from Python's `uuid` library.
      - **Expected Output**: A unique string identifier.
    - **`get_current_time()`**: Fetches the current UTC time for timestamps.
      - **Dependencies**: Utilizes `datetime` for time operations.
      - **Expected Output**: A `datetime` object representing the current time.

  - **Response Models**:
    - **`PromptList`**: Contains a list of `Prompt` instances and a total count.
    - **`CollectionList`**: Contains a list of `Collection` instances and a total count.
    - **`HealthResponse`**: Indicates application health with status and version fields.

These models and functions are foundational for managing and validating data related to prompts and collections within the application, ensuring robust data handling and integrity.

### 5. `app/utils.py`
- **Utility Functions**:
  - **`sort_prompts_by_date()`**: Sorts a list of prompt instances by their creation date.
    - **Dependencies**: Requires a list of `Prompt` models and utilizes Python's built-in `sorted()` function.
    - **Expected Input**: A list of `Prompt` instances and an optional boolean for descending order.
    - **Expected Output**: A new list of `Prompt` instances sorted by the `created_at` attribute.
    - **Failure Modes**: Currently contains a bug where the descending parameter is ignored, thus always sorting in ascending order (oldest first).
  
  - **`filter_prompts_by_collection()`**: Filters prompts based on their collection ID.
    - **Dependencies**: Works with a list of `Prompt` instances.
    - **Expected Input**: A list of `Prompt` instances and a collection ID string.
    - **Expected Output**: A list of `Prompt` instances whose `collection_id` matches the input ID.
    - **Failure Modes**: Relies on valid collection IDs; unexpected IDs will result in no matches.

  - **`search_prompts()`**: Searches through prompts to find those that match a query in their title or description.
    - **Dependencies**: Utilizes Python string methods for case-insensitive search.
    - **Expected Input**: A list of `Prompt` instances and a query string.
    - **Expected Output**: A list of `Prompt` instances where the query is present in the title or description.
    - **Failure Modes**: Handles empty or missing descriptions gracefully using condition checks.

  - **`validate_prompt_content()`**: Validates the content of a prompt to ensure it meets basic criteria.
    - **Dependencies**: Operates with standard string methods.
    - **Expected Input**: A content string from a prompt.
    - **Expected Output**: Returns `True` if valid (non-empty, not just whitespace, at least 10 characters).
    - **Failure Modes**: Will return `False` for empty, whitespace-only, or too-short content.

  - **`extract_variables()`**: Extracts template variables from prompt content following `{{variable_name}}` pattern.
    - **Dependencies**: Uses Python's `re` module for regular expression matching.
    - **Expected Input**: A content string potentially containing variables.
    - **Expected Output**: A list of variable names found within the content.
    - **Failure Modes**: Assumes content well-formed for the regex pattern; malformed brackets might lead to no matches.

These utility functions support the main functionalities of managing prompts by providing sorting, filtering, searching, validation, and variable extraction capabilities which are crucial for maintaining data integrity and enhancing user interactions.

### 6. `app/api.py`
- **FastAPI Routes**:
  - **General Setup**:
    - Initializes the FastAPI application with metadata and sets up CORS middleware to allow cross-origin requests from any origin.

  - **Health Check Endpoint**:
    - **`health_check()`**: Provides a health status of the application.
      - **Dependencies**: Returns a `HealthResponse` model.
      - **Expected Output**: JSON response with application's health status and version.
      - **Failure Modes**: None identified; straightforward response.

  - **Prompt Endpoints**:
    - **`list_prompts()`**: Lists all prompts, optionally filtered by `collection_id` and search query.
      - **Dependencies**: Relies on `storage.get_all_prompts()`, and utility functions `filter_prompts_by_collection`, `search_prompts`, and `sort_prompts_by_date`.
      - **Expected Input**: Optional `collection_id` and search query string.
      - **Expected Output**: A list of prompts and total count.
      - **Failure Modes**: Bug in sorting order might not list prompts as expected.
    - **`get_prompt()`**: Retrieves a specific prompt by its ID.
      - **Dependencies**: Uses `storage.get_prompt()`.
      - **Expected Input**: `prompt_id`.
      - **Expected Output**: A prompt object.
      - **Failure Modes**: Raises a 500 error if prompt is not found due to an assumption bug (should raise 404).
    - **`create_prompt()`**: Creates a new prompt.
      - **Dependencies**: Validates collection existence using `storage.get_collection()`.
      - **Expected Input**: `PromptCreate` model with optional `collection_id`.
      - **Expected Output**: Newly created `Prompt` model.
      - **Failure Modes**: Raises 400 if `collection_id` is invalid.
    - **`update_prompt()`**: Updates an existing prompt.
      - **Dependencies**: Fetches existing prompt and validates fields, but fails to update timestamp.
      - **Expected Input**: `prompt_id` and `PromptUpdate` data.
      - **Expected Output**: Updated `Prompt` model.
      - **Failure Modes**: Timestamp bug results in incorrect `updated_at` time.
    - **`delete_prompt()`**: Deletes a prompt by ID.
      - **Dependencies**: Uses `storage.delete_prompt()`.
      - **Expected Input**: `prompt_id`.
      - **Expected Output**: No content if successful deletion.
      - **Failure Modes**: Raises 404 if prompt is not found.

  - **Collection Endpoints**:
    - **`list_collections()`**: Lists all collections.
      - **Expected Output**: A list of collections and the total count.
    - **`get_collection()`**: Retrieves a collection by ID.
      - **Expected Input**: `collection_id`.
      - **Expected Output**: A `Collection` object.
      - **Failure Modes**: Raises 404 if not found.
    - **`create_collection()`**: Creates a new collection.
      - **Expected Input**: `CollectionCreate` data.
      - **Expected Output**: Created `Collection` with HTTP status 201.
    - **`delete_collection()`**: Deletes a collection by ID, but misses handling related prompts.
      - **Dependencies**: Uses `storage.delete_collection()`.
      - **Expected Input**: `collection_id`.
      - **Expected Output**: HTTP status 204 on successful deletion.
      - **Failure Modes**: Orphaned prompts remain if associated collection is deleted (unspecified handling).

These endpoints facilitate the management of prompts and collections, but require further attention to bugs related to sorting, updating timestamps, and handling prompt-collection relationships on deletion.


## Dependencies:
- Internal dependencies consist of cross-module method calls and class instantiations.
- Utilizes `fastapi`, `uvicorn`, `pydantic`, and standard Python libraries such as `datetime` and `uuid`.  

**Note**: Some functionalities are marked with existing bugs or unimplemented features, such as the POST update timestamp bug and handling orphaned collections.



