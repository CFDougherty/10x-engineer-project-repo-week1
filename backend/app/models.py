"""Pydantic models for PromptLab."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator
import html

def sanitize_html(text: str) -> str:
    """Sanitize HTML content to prevent XSS attacks.

    Args:
        text: The text to sanitize.

    Returns:
        Sanitized text with HTML entities escaped.
    """
    if not isinstance(text, str):
        return text
    return html.escape(text)

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

    title: str = Field(..., max_length=200)
    content: str = Field(...)
    description: Optional[str] = Field(None, max_length=500)
    collection_id: Optional[str] = Field(None, min_length=0)  # Allow empty string or None

    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    @field_validator('title', 'content', mode='after')
    def validate_content_non_empty(cls, v):
        """Ensure content is not empty."""
        if not v or not v.strip():
            raise ValueError("field must be a non-empty string")
        return v

    @field_validator('title', 'content', mode='after')
    def validate_no_sql_injection(cls, v):
        """Check for SQL injection patterns in title and content."""
        sql_patterns = ["'; DROP", "'; DELETE", "'; INSERT", "'; UPDATE", "'; SELECT", "'; TRUNCATE"]
        if isinstance(v, str):
            for pattern in sql_patterns:
                if pattern.upper() in v.upper():
                    raise ValueError(f"Input contains disallowed SQL pattern: {pattern}")
        return v

    @field_validator('title', mode='after')
    def validate_title_length(cls, v):
        """Ensure title doesn't exceed maximum length."""
        if len(v) > 200:
            raise ValueError("Title must be 200 characters or less")
        return v

    @field_validator('description', mode='after')
    def validate_description_length(cls, v):
        """Ensure description doesn't exceed maximum length."""
        if v is not None and len(v) > 500:
            raise ValueError("Description must be 500 characters or less")
        return v

    @field_validator('title', mode='after')
    def validate_title_non_empty(cls, v):
        """Ensure title is not empty."""
        if not v or not v.strip():
            raise ValueError("title must be a non-empty string")
        return v


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
        version: Current version number of the prompt.

    Notes:
        The inner ``Config`` sets ``from_attributes = True`` to allow creating
        instances from objects with attributes (e.g., ORM objects) rather than
        requiring a dict-like input.
    """

    id: str = Field(default_factory=generate_id, min_length=1)
    created_at: datetime = Field(default_factory=get_current_time)
    updated_at: datetime = Field(default_factory=get_current_time)
    version: Optional[int] = Field(None, description="Current version number")

    def __init__(self, **data):
        """Initialize a Prompt instance and sanitize HTML content."""
        # Sanitize HTML fields before setting them
        if 'title' in data and data['title'] is not None:
            data['title'] = sanitize_html(data['title'])
        if 'content' in data and data['content'] is not None:
            data['content'] = sanitize_html(data['content'])
        if 'description' in data and data['description'] is not None:
            data['description'] = sanitize_html(data['description'])
        super().__init__(**data)

    def __setattr__(self, name, value):
        """Override attribute setting to update timestamp when content changes and sanitize HTML."""
        if name in ['title', 'content', 'description']:
            # Sanitize HTML to prevent XSS attacks
            if value is not None:
                value = sanitize_html(value)
            super().__setattr__(name, value)
            # Only update timestamp if this is not the initial creation
            if hasattr(self, 'updated_at'):
                super().__setattr__('updated_at', get_current_time())
        elif name == 'collection_id':
            super().__setattr__(name, value)
        else:
            super().__setattr__(name, value)

    def __eq__(self, other):
        """Compare prompts by their data, not by object identity.

        Two prompts are considered equal if they have the same content fields.
        This allows for comparison of prompts regardless of their IDs or timestamps.
        """
        if not isinstance(other, Prompt):
            return False
        # Compare all content fields, ignoring timestamps, version, and ID
        return (self.title == other.title and
                self.content == other.content and
                self.description == other.description and
                self.collection_id == other.collection_id)

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

    @field_validator('name', mode='after')
    def validate_non_whitespace_name(cls, v):
        """Ensure name is not just whitespace."""
        if isinstance(v, str) and not v.strip():
            raise ValueError("Name cannot be empty or whitespace only")
        return v

class CollectionUpdateOptional(BaseModel):
    """Schema for partially updating a collection with optional fields.

    Attributes:
        name (Optional[str]): Updated collection name.
        description (Optional[str]): Updated collection description.
    """

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

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
        if isinstance(v, str) and not v.strip():
            return None
        return v

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

    def __eq__(self, other):
        """Compare collections by their data, not by object identity."""
        if not isinstance(other, Collection):
            return False
        return (self.id == other.id and
                self.name == other.name and
                self.description == other.description)

    class Config:
        from_attributes = True

# ============== Versioning Models ==============

class PromptVersion(BaseModel):
    """Represent an immutable version of a prompt.

    This model stores a snapshot of prompt fields at a specific point in time.
    Versions are immutable once created and maintain the state of the prompt
    at the time they were created.

    Attributes:
        prompt_id: The unique identifier of the parent prompt.
        version: The version number (starts at 1 and increments by 1).
        title: The prompt title at this version.
        content: The prompt content at this version.
        description: The prompt description at this version (optional).
        collection_id: The collection identifier at this version (optional).
        created_at: Timestamp when this version was created.
    """

    prompt_id: str
    version: int
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    description: Optional[str] = Field(None, max_length=500)
    collection_id: Optional[str] = None
    created_at: datetime = Field(default_factory=get_current_time)

    class Config:
        from_attributes = True

class PromptMeta(BaseModel):
    """Metadata for a prompt's version history.

    This model tracks the current version and creation timestamp for a prompt.
    It serves as the "logical prompt" that users interact with, while versions
    store the immutable history.

    Attributes:
        id: Unique identifier for the prompt.
        current_version: The highest version number for this prompt.
        created_at: Timestamp when the prompt was first created.
    """

    id: str
    current_version: int
    created_at: datetime = Field(default_factory=get_current_time)

    class Config:
        from_attributes = True

class VersionSummary(BaseModel):
    """Summary information for a prompt version.

    This model provides a lightweight representation of a version for listing
    purposes, without including the full content.

    Attributes:
        version: The version number.
        created_at: Timestamp when the version was created.
        title: The prompt title at this version.
        description: The prompt description at this version (optional).
    """

    version: int
    created_at: datetime
    title: str
    description: Optional[str]

class VersionList(BaseModel):
    """Container for listing all versions of a prompt.

    Attributes:
        prompt_id: The unique identifier of the prompt.
        versions: List of version summaries.
        total: The total number of versions.
    """

    prompt_id: str
    versions: List[VersionSummary]
    total: int

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
        collections (List[Collection]): The list of `Collection` items returned for
            the current page/query.
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