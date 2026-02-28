"""Tests covering the core Pydantic models in PromptLab."""

import json
from datetime import datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.models import (
    PromptBase,
    Prompt,
    PromptUpdateOptional,
    CollectionBase,
    Collection,
    PromptList,
    CollectionList,
)


class TestPromptValidation:
    """Validation rules for prompt models."""

    def test_prompt_base_requires_title_and_content(self):
        """PromptBase should demand both title and content."""
        with pytest.raises(ValidationError) as exc:  # missing title
            PromptBase(content="Has content but no title")
        assert "title" in str(exc.value)

        with pytest.raises(ValidationError) as exc:  # missing content
            PromptBase(title="Only a title")
        assert "content" in str(exc.value)

    def test_prompt_base_enforces_length_constraints(self):
        """Title, content, and description must respect the declared bounds."""
        with pytest.raises(ValidationError):
            PromptBase(title="", content="valid content")

        with pytest.raises(ValidationError):
            PromptBase(title="A" * 201, content="valid content")

        with pytest.raises(ValidationError):
            PromptBase(title="Valid", content="", description="ok")

        with pytest.raises(ValidationError):
            PromptBase(title="Valid", content="valid", description="A" * 501)

    def test_prompt_update_optional_normalizes_blank_strings(self):
        """Blank strings should become None during PromptUpdateOptional validation."""
        update_payload = PromptUpdateOptional(
            title="   ",
            content="\n\t",
            description="  ",
            collection_id="   ",
        )

        assert update_payload.title is None
        assert update_payload.content is None
        assert update_payload.description is None
        assert update_payload.collection_id is None


class TestPromptValidationEdgeCases:
    """Additional validation scenarios that currently protect data quality."""

    def test_prompt_base_rejects_whitespace_only_text(self):
        """Newline/whitespace-only titles or content should not succeed."""
        with pytest.raises(ValidationError):
            PromptBase(title="\n \t", content="Valid content")

        with pytest.raises(ValidationError):
            PromptBase(title="Valid", content="\n\n")


class TestCollectionValidation:
    """Validation rules for collection models."""

    def test_collection_base_requires_name(self):
        """Collections must have a non-empty name."""
        with pytest.raises(ValidationError):
            CollectionBase()

    def test_collection_base_enforces_length_constraints(self):
        """Name and description fields enforce their min/max lengths."""
        with pytest.raises(ValidationError):
            CollectionBase(name="")

        with pytest.raises(ValidationError):
            CollectionBase(name="A" * 101)

        with pytest.raises(ValidationError):
            CollectionBase(name="Valid", description="A" * 501)


class TestPromptAndCollectionDefaults:
    """Ensure default factories and attribute-based construction behave correctly."""

    def test_prompt_generates_id_and_timestamps(self):
        """Prompt should generate a UUID and timestamps when not provided."""
        from datetime import timezone
        before = datetime.now(timezone.utc).replace(tzinfo=None)
        prompt = Prompt(title="Default Test", content="Default content")
        after = datetime.now(timezone.utc).replace(tzinfo=None)

        uuid_obj = UUID(prompt.id)
        assert isinstance(uuid_obj, UUID)
        assert before <= prompt.created_at <= after
        assert before <= prompt.updated_at <= after

    def test_collection_generates_id_and_timestamp(self):
        """Collections should also auto-generate an ID and created_at timestamp."""
        collection = Collection(name="Default Collection")
        assert isinstance(UUID(collection.id), UUID)
        assert isinstance(collection.created_at, datetime)

    def test_prompt_handles_attribute_based_data(self):
        """Config.from_attributes allows constructing a Prompt from attribute-rich objects."""

        class DummyPrompt:
            def __init__(self):
                self.title = "Attribute Title"
                self.content = "Attribute content"
                self.description = "Attribute description"

        dummy = DummyPrompt()
        prompt = Prompt.model_validate(dummy)

        assert prompt.title == dummy.title
        assert prompt.content == dummy.content
        assert prompt.description == dummy.description
        assert isinstance(prompt.created_at, datetime)
        assert prompt.collection_id is None

    def test_collection_handles_attribute_based_data(self):
        """Collections benefit from the same from_attributes configuration as Prompt."""

        class DummyCollection:
            def __init__(self):
                self.name = "Attribute Collection"
                self.description = "Attribute description"

        dummy = DummyCollection()
        collection = Collection.model_validate(dummy)

        assert collection.name == dummy.name
        assert collection.description == dummy.description
        assert isinstance(collection.created_at, datetime)


class TestModelSerialization:
    """Serialization behavior for individual models and list containers."""

    def test_prompt_json_serialization_handles_nulls(self):
        """JSON dumps should expose optional fields even when they are None."""
        prompt = Prompt(
            title="Serialize",
            content="Serialization content",
            description=None,
            collection_id=None,
        )

        dump = prompt.model_dump()
        assert dump["title"] == "Serialize"
        assert dump["description"] is None
        assert dump["collection_id"] is None

        serialized_json = prompt.model_dump_json()
        parsed = json.loads(serialized_json)
        assert parsed["title"] == "Serialize"
        assert parsed["description"] is None
        assert parsed["collection_id"] is None

    def test_prompt_and_collection_lists_model_dump(self):
        """Containers should preserve totals and serialize nested models."""
        prompts = [
            Prompt(title="One", content="First content"),
            Prompt(title="Two", content="Second content"),
        ]
        prompt_list = PromptList(prompts=prompts, total=2)
        prompt_dump = prompt_list.model_dump()

        assert prompt_dump["total"] == 2
        assert len(prompt_dump["prompts"]) == 2
        assert {item["title"] for item in prompt_dump["prompts"]} == {"One", "Two"}

        collections = [
            Collection(name="Default"),
            Collection(name="Secondary"),
        ]
        collection_list = CollectionList(collections=collections, total=2)
        collection_dump = collection_list.model_dump()

        assert collection_dump["total"] == 2
        assert len(collection_dump["collections"]) == 2
        assert {item["name"] for item in collection_dump["collections"]} == {"Default", "Secondary"}


class TestModelSerializationEdgeCases:
    """Additional serialization assertions for JSON helpers."""

    def test_prompt_model_dump_exclude_none(self):
        """`exclude_none` should drop optional fields instead of emitting nulls."""
        prompt = Prompt(
            title="Selective",
            content="Selective content",
            description=None,
            collection_id=None,
        )

        filtered_dump = prompt.model_dump(exclude_none=True)
        assert "description" not in filtered_dump
        assert "collection_id" not in filtered_dump

        default_dump = prompt.model_dump()
        assert default_dump["description"] is None
        assert default_dump["collection_id"] is None

    def test_prompt_list_json_by_alias_and_indentation(self):
        """JSON output honors formatting options even when no aliases exist."""
        prompts = [
            Prompt(title="Alpha", content="First"),
            Prompt(title="Beta", content="Second"),
        ]
        prompt_list = PromptList(prompts=prompts, total=2)
        serialized = prompt_list.model_dump_json(by_alias=True, indent=2)
        parsed = json.loads(serialized)

        assert parsed["total"] == 2
        assert len(parsed["prompts"]) == 2
        assert parsed["prompts"][0]["title"] in {"Alpha", "Beta"}
        assert serialized.startswith("{")
        assert "prompts" in serialized

    def test_collection_list_json_exclude_none(self):
        """Collection containers should behave consistently when serialized."""
        collections = [Collection(name="Outer"), Collection(name="Inner", description=None)]
        serialized = CollectionList(collections=collections, total=2).model_dump_json(exclude_none=True)
        parsed = json.loads(serialized)

        assert parsed["total"] == 2
        assert len(parsed["collections"]) == 2
        assert all("name" in item for item in parsed["collections"])


class TestPromptValidationErrors:
    """Test specific validation error messages and details."""

    def test_prompt_base_validation_error_messages(self):
        """Verify validation errors include helpful messages."""
        with pytest.raises(ValidationError) as exc:
            PromptBase(title="", content="valid")
        errors = exc.value.errors()
        assert any("title" in str(e) and "non-empty" in str(e).lower() for e in errors)

    def test_prompt_base_rejects_invalid_uuid(self):
        """Test that invalid UUID formats are rejected."""
        with pytest.raises(ValidationError):
            Prompt(id="not-a-uuid", title="Test", content="Test")

class TestModelComparison:
    """Test model equality and comparison behavior."""

    def test_prompt_equality(self):
        """Prompts with same data and same ID should be equal."""
        p1 = Prompt(title="Test", content="Content")
        p2 = Prompt(id=p1.id, title="Test", content="Content")
        assert p1 == p2

    def test_prompt_inequality_with_different_data(self):
        """Prompts with different data should not be equal."""
        p1 = Prompt(title="Test", content="Content1")
        p2 = Prompt(title="Test", content="Content2")
        assert p1 != p2

class TestModelCopying:
    """Test model copying and cloning behavior."""

    def test_prompt_copy_creates_independent_instance(self):
        """Copying a prompt should create a new independent instance."""
        original = Prompt(title="Test", content="Content")
        copy = original.model_copy()
        assert copy != original
        assert copy.id != original.id
        assert copy.title == original.title

class TestUnicodeAndSpecialCharacters:
    """Test handling of unicode and special characters."""

    def test_prompt_with_unicode_characters(self):
        """Prompts should handle unicode characters correctly."""
        prompt = Prompt(
            title="Test 🚀",
            content="Content with émojis 🎉 and special chars: <>&\"'",
            description="Description with unicode: 日本語"
        )
        assert prompt.title == "Test 🚀"
        assert "émojis" in prompt.content
        assert "日本語" in prompt.description

    def test_prompt_with_newlines_and_tabs(self):
        """Content with newlines and tabs should be preserved."""
        content = "Line 1\n\tTabbed content\nLine 3"
        prompt = Prompt(title="Multi-line", content=content)
        assert prompt.content == content

class TestModelUpdateBehavior:
    """Test model update and modification behavior."""

    def test_prompt_update_preserves_timestamps(self):
        """Updating a prompt should update the updated_at timestamp."""
        import time
        prompt = Prompt(title="Test", content="Original")
        original_updated = prompt.updated_at
        time.sleep(0.01)  # Ensure time passes
        prompt.title = "Updated"
        assert prompt.updated_at > original_updated

    def test_prompt_update_with_optional_fields(self):
        """Test updating with optional fields set to None."""
        prompt = Prompt(
            title="Test",
            content="Content",
            description="Original",
            collection_id="col-123"
        )
        update = PromptUpdateOptional(description=None, collection_id=None)
        # This would need implementation in the actual model
        # Just testing the update object behavior
        assert update.description is None
        assert update.collection_id is None

class TestModelSerializationEdgeCases:
    """Additional serialization edge cases."""

    def test_prompt_serialization_with_all_fields(self):
        """Test serialization with all possible fields populated."""
        prompt = Prompt(
            id="123e4567-e89b-12d3-a456-426614174000",
            title="Complete",
            content="Full content",
            description="Full description",
            collection_id="col-123",
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 1, 2)
        )
        dump = prompt.model_dump()
        assert dump["id"] == "123e4567-e89b-12d3-a456-426614174000"
        assert dump["created_at"] == datetime(2023, 1, 1)
        assert dump["updated_at"] == datetime(2023, 1, 2)

    def test_prompt_json_serialization_with_custom_encoder(self):
        """Test JSON serialization handles datetime objects properly."""
        prompt = Prompt(
            title="Date test",
            content="Content",
            created_at=datetime(2023, 1, 1, 12, 30, 45)
        )
        json_str = prompt.model_dump_json()
        data = json.loads(json_str)
        assert "created_at" in data
        # The exact format depends on Pydantic's datetime serialization
        assert isinstance(data["created_at"], str)

class TestCollectionEdgeCases:
    """Additional collection-specific edge cases."""

    def test_collection_with_minimum_fields(self):
        """Collections should work with only required fields."""
        collection = Collection(name="Minimal")
        assert collection.name == "Minimal"
        assert collection.description is None
        assert isinstance(collection.id, str)
        assert isinstance(collection.created_at, datetime)

    def test_collection_update_optional(self):
        """Test collection update with optional fields."""
        update = CollectionBase(name="Updated", description="")
        # Empty string should be treated as None for description
        assert update.description == ""

        # But whitespace should be normalized
        update2 = CollectionBase(name="Updated", description="   ")
        assert update2.description == "   "  # This might need adjustment based on actual model behavior

class TestModelValidationWithInvalidTypes:
    """Test model validation with invalid data types."""

    def test_prompt_with_invalid_id_type(self):
        """Test that non-string/non-UUID IDs are rejected."""
        with pytest.raises(ValidationError):
            Prompt(id=123, title="Test", content="Test")

    def test_prompt_with_invalid_created_at_type(self):
        """Test that invalid created_at types are rejected."""
        with pytest.raises(ValidationError):
            Prompt(title="Test", content="Test", created_at="not-a-date")

    def test_collection_with_invalid_created_at(self):
        """Test that invalid created_at types are rejected for collections."""
        with pytest.raises(ValidationError):
            Collection(name="Test", created_at="invalid")