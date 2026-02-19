"""Pydantic models for PromptLab."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator

def generate_id() -> str:
    """Generate a UUID4 identifier string.

    Returns:
        str: A UUID4 string (e.g., "3fa85f64-5717-4562-b3fc-2c963f66afa6").
    """
    return str(uuid4())

def get_current_time() -> datetime:
    """Get the current UTC time as a naive `datetime`.

    This function returns the current time in Coordinated Universal Time (UTC)
    without timezone information (i.e., a naive `datetime`).

    Returns:
        datetime: The current time in UTC (naive).
    """
    return datetime.utcnow()


# ============== Prompt Models ==============
class PromptUpdateOptional(BaseModel):
    """Schema for updating a prompt with optional fields.

    Attributes:
        title (Optional[str]): Updated prompt title.
        content (Optional[str]): Updated prompt content.
        description (Optional[str]): Updated prompt description.
        collection_id (Optional[str]): Updated collection identifier for the prompt.
    """

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, max_length=500)
    collection_id: Optional[str] = None

    @field_validator('*', mode='before')
    def check_empty_values(cls, v, info):
        """Normalize empty or whitespace-only strings to None.

        Args:
            cls: The model class.
            v: The value being validated.
            info: Validator context information provided by Pydantic.

        Returns:
            Any: None if the input is an empty or whitespace-only string; otherwise
                the original value.
        """

        # Ensure that fields are not empty strings or only whitespace
        if isinstance(v, str) and not v.strip():
            return None
        return v
    
class PromptBase(BaseModel):
    """Base schema for a prompt.

    Attributes:
        title (str): Prompt title (1-200 characters).
        content (str): Prompt content (minimum 1 character).
        description (Optional[str]): Optional prompt description (up to 500 characters).
        collection_id (Optional[str]): Optional identifier for the collection the prompt belongs to.
    """

    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    description: Optional[str] = Field(None, max_length=500)
    collection_id: Optional[str] = None


class PromptCreate(PromptBase):
    """Schema for creating a new prompt."""
    pass


class PromptUpdate(PromptBase):
    """Schema for updating an existing prompt.

    This model inherits all fields and validation rules from PromptBase
    and does not introduce additional fields. It is typically used for request
    payloads where a prompt update is expected.

    Attributes:
        Inherited from PromptBase.
    """
    pass


class Prompt(PromptBase):
    """Represent a persisted prompt entity.

    This model extends PromptBase by adding persistence-related fields
    such as a unique identifier and audit timestamps. The ``id`` is generated
    automatically, and ``created_at`` / ``updated_at`` default to the current
    time at instantiation.

    Attributes:
        id: Unique identifier for the prompt. Automatically generated via
            ``generate_id`` when not provided.
        created_at: Timestamp indicating when the prompt was created. Defaults
            to the current time via ``get_current_time``.
        updated_at: Timestamp indicating when the prompt was last updated.
            Defaults to the current time via ``get_current_time``.

    Notes:
        The inner ``Config`` sets ``from_attributes = True`` to allow creating
        instances from objects with attributes (e.g., ORM objects) rather than
        requiring a dict-like input.
    """

    id: str = Field(default_factory=generate_id)
    created_at: datetime = Field(default_factory=get_current_time)
    updated_at: datetime = Field(default_factory=get_current_time)

    class Config:
        from_attributes = True


# ============== Collection Models ==============

class CollectionBase(BaseModel):
    """Base schema for a collection.

    Attributes:
        name: The collection name. Must be between 1 and 100 characters.
        description: Optional description of the collection. If provided, must be
            at most 500 characters.
    """

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class CollectionCreate(CollectionBase):
    """Schema for creating a collection.

    This model represents the payload required to create a new collection.
    It inherits all fields and validation rules from CollectionBase and
    does not introduce any additional attributes.

    Attributes:
        (Inherited): All attributes are inherited from CollectionBase.
    """
    pass


class Collection(CollectionBase):
    """Represent a persisted collection with a unique identifier and timestamps.

    This model extends CollectionBase by adding fields that are typically assigned
    when the collection is created and stored, such as a generated ID and a
    creation timestamp.

    Attributes:
        id: Unique identifier for the collection. Automatically generated using
            `generate_id` when not explicitly provided.
        created_at: Timestamp indicating when the collection was created.
            Automatically set using `get_current_time` when not explicitly provided.

    Notes:
        The inner `Config` sets `from_attributes = True` to allow the model to be
        created from object attributes (e.g., ORM instances), not only from dicts.
    """

    id: str = Field(default_factory=generate_id)
    created_at: datetime = Field(default_factory=get_current_time)

    class Config:
        from_attributes = True


# ============== Response Models ==============

class PromptList(BaseModel):
    """Container model representing a paginated (or summarized) collection of prompts.

    Attributes:
        prompts (List[Prompt]): The list of `Prompt` items included in this response.
        total (int): The total number of prompts available (e.g., across all pages),
            not just the number returned in `prompts`.
    """

    prompts: List[Prompt]
    total: int


class CollectionList(BaseModel):
    """Container for a paginated list of collections.

    Attributes:
        collections (List[Collection]): The list of `Collection` items returned for the
            current page/query.
        total (int): The total number of collections matching the query across all pages.
    """

    collections: List[Collection]
    total: int


class HealthResponse(BaseModel):
    """Response model for the service health check endpoint.

    Attributes:
        status (str): Current health status of the service (e.g., "ok", "degraded").
        version (str): Deployed application version identifier (e.g., a semantic
            version like "1.2.3" or a git SHA).
    """

    status: str
    version: str