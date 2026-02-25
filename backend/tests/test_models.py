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
        before = datetime.utcnow()
        prompt = Prompt(title="Default Test", content="Default content")
        after = datetime.utcnow()

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