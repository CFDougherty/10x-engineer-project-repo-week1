"""Comprehensive tests for prompt versioning system.

This test suite covers all aspects of the prompt versioning feature,
including creating versions, retrieving specific versions, listing version history,
and promoting older versions to become the latest version.
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.models import Prompt, PromptCreate, PromptUpdate
from app.versioning import (
    create_prompt_with_version,
    create_version,
    get_prompt_version,
    get_prompt_versions,
    promote_version,
    get_latest_prompt
)

class TestPromptVersioning:
    """Test suite for prompt versioning functionality."""

    def test_create_prompt_creates_version_1(self):
        """Test that creating a prompt creates version 1."""
        prompt_data = PromptCreate(
            title="Test Prompt",
            content="This is the initial content",
            description="Initial description"
        )

        # Create prompt with versioning
        result = create_prompt_with_version(prompt_data)

        assert result.version == 1
        assert result.title == "Test Prompt"
        assert result.content == "This is the initial content"
        assert result.description == "Initial description"
        assert result.id is not None
        assert result.created_at is not None

    def test_create_version_increments_version_number(self):
        """Test that creating a new version increments the version number."""
        # Create initial prompt
        initial_data = PromptCreate(
            title="Test Prompt",
            content="Initial content",
            description="Initial description"
        )
        initial_prompt = create_prompt_with_version(initial_data)

        # Create first update
        update_data = PromptUpdate(
            title="Updated Prompt",
            content="Updated content",
            description="Updated description"
        )
        version_2 = create_version(initial_prompt.id, update_data)

        assert version_2.version == 2
        assert version_2.title == "Updated Prompt"
        assert version_2.content == "Updated content"
        assert version_2.description == "Updated description"

    def test_get_prompt_version_returns_correct_snapshot(self):
        """Test that getting a specific version returns the correct snapshot."""
        # Create initial prompt
        initial_data = PromptCreate(
            title="Version 1",
            content="Content 1",
            description="Description 1"
        )
        prompt = create_prompt_with_version(initial_data)

        # Create version 2
        update_data = PromptUpdate(
            title="Version 2",
            content="Content 2",
            description="Description 2"
        )
        create_version(prompt.id, update_data)

        # Create version 3
        update_data = PromptUpdate(
            title="Version 3",
            content="Content 3",
            description="Description 3"
        )
        create_version(prompt.id, update_data)

        # Get version 2
        version_2 = get_prompt_version(prompt.id, 2)

        assert version_2.version == 2
        assert version_2.title == "Version 2"
        assert version_2.content == "Content 2"
        assert version_2.description == "Description 2"

    def test_get_prompt_versions_returns_all_versions(self):
        """Test that getting all versions returns the complete history."""
        # Create initial prompt
        initial_data = PromptCreate(
            title="Initial",
            content="Initial content"
        )
        prompt = create_prompt_with_version(initial_data)

        # Create more versions
        for i in range(2, 6):
            update_data = PromptUpdate(
                title=f"Version {i}",
                content=f"Content {i}"
            )
            create_version(prompt.id, update_data)

        # Get all versions
        versions = get_prompt_versions(prompt.id)

        assert len(versions) == 5
        assert versions[0].version == 5  # Newest first
        assert versions[1].version == 4
        assert versions[2].version == 3
        assert versions[3].version == 2
        assert versions[4].version == 1

    def test_get_latest_prompt_returns_current_version(self):
        """Test that getting the latest prompt returns the current version."""
        # Create initial prompt
        initial_data = PromptCreate(
            title="Version 1",
            content="Content 1"
        )
        prompt = create_prompt_with_version(initial_data)

        # Create version 2
        update_data = PromptUpdate(
            title="Version 2",
            content="Content 2"
        )
        create_version(prompt.id, update_data)

        # Get latest prompt
        latest = get_latest_prompt(prompt.id)

        assert latest.version == 2
        assert latest.title == "Version 2"
        assert latest.content == "Content 2"

    def test_promote_version_creates_new_version(self):
        """Test that promoting an older version creates a new version."""
        # Create initial prompt
        initial_data = PromptCreate(
            title="Version 1",
            content="Content 1"
        )
        prompt = create_prompt_with_version(initial_data)

        # Create version 2
        update_data = PromptUpdate(
            title="Version 2",
            content="Content 2"
        )
        create_version(prompt.id, update_data)

        # Create version 3
        update_data = PromptUpdate(
            title="Version 3",
            content="Content 3"
        )
        create_version(prompt.id, update_data)

        # Promote version 1 to become the new latest
        promoted = promote_version(prompt.id, 1)

        assert promoted.version == 4  # New version created
        assert promoted.title == "Version 1"  # Content from version 1
        assert promoted.content == "Content 1"

    def test_promote_version_preserves_history(self):
        """Test that promoting a version preserves the complete history."""
        # Create initial prompt
        initial_data = PromptCreate(
            title="Version 1",
            content="Content 1"
        )
        prompt = create_prompt_with_version(initial_data)

        # Create version 2
        update_data = PromptUpdate(
            title="Version 2",
            content="Content 2"
        )
        create_version(prompt.id, update_data)

        # Promote version 1
        promote_version(prompt.id, 1)

        # Get all versions - should have 3 versions total
        versions = get_prompt_versions(prompt.id)

        assert len(versions) == 3
        assert versions[0].version == 3  # Newest (promoted version)
        assert versions[1].version == 2  # Original version 2
        assert versions[2].version == 1  # Original version 1

    def test_version_immutability(self):
        """Test that once created, versions cannot be modified."""
        # Create initial prompt
        initial_data = PromptCreate(
            title="Version 1",
            content="Content 1"
        )
        prompt = create_prompt_with_version(initial_data)

        # Create version 2
        update_data = PromptUpdate(
            title="Version 2",
            content="Content 2"
        )
        create_version(prompt.id, update_data)

        # Get version 1
        version_1 = get_prompt_version(prompt.id, 1)

        # Verify version 1 hasn't changed
        assert version_1.title == "Version 1"
        assert version_1.content == "Content 1"

    def test_partial_updates_create_new_versions(self):
        """Test that partial updates (PATCH-like) create new versions."""
        # Create initial prompt
        initial_data = PromptCreate(
            title="Initial Title",
            content="Initial Content",
            description="Initial Description"
        )
        prompt = create_prompt_with_version(initial_data)

        # Update only title
        partial_update = PromptUpdate(
            title="Updated Title",
            content="Initial Content",  # unchanged
            description="Initial Description"  # unchanged
        )
        version_2 = create_version(prompt.id, partial_update)

        assert version_2.version == 2
        assert version_2.title == "Updated Title"
        assert version_2.content == "Initial Content"
        assert version_2.description == "Initial Description"

    def test_version_timestamps_are_preserved(self):
        """Test that version timestamps reflect when each version was created."""
        # Create initial prompt
        initial_data = PromptCreate(
            title="Version 1",
            content="Content 1"
        )
        prompt = create_prompt_with_version(initial_data)

        # Small delay to ensure different timestamps
        import time
        time.sleep(0.01)

        # Create version 2
        update_data = PromptUpdate(
            title="Version 2",
            content="Content 2"
        )
        create_version(prompt.id, update_data)

        # Get both versions
        version_1 = get_prompt_version(prompt.id, 1)
        version_2 = get_prompt_version(prompt.id, 2)

        # Version 2 should have a later timestamp
        assert version_2.created_at > version_1.created_at

    def test_get_nonexistent_version_raises_error(self):
        """Test that requesting a non-existent version raises an appropriate error."""
        # Create initial prompt
        initial_data = PromptCreate(
            title="Version 1",
            content="Content 1"
        )
        prompt = create_prompt_with_version(initial_data)

        # Try to get version 5 (doesn't exist)
        with pytest.raises(ValueError):
            get_prompt_version(prompt.id, 5)

    def test_get_versions_for_nonexistent_prompt_returns_empty(self):
        """Test that getting versions for a non-existent prompt returns empty list."""
        versions = get_prompt_versions("nonexistent-id")
        assert versions == []

    def test_promote_nonexistent_version_raises_error(self):
        """Test that promoting a non-existent version raises an error."""
        # Create initial prompt
        initial_data = PromptCreate(
            title="Version 1",
            content="Content 1"
        )
        prompt = create_prompt_with_version(initial_data)

        # Try to promote version 5 (doesn't exist)
        with pytest.raises(ValueError):
            promote_version(prompt.id, 5)

    def test_promote_version_from_nonexistent_prompt_raises_error(self):
        """Test that promoting a version from a non-existent prompt raises an error."""
        with pytest.raises(ValueError):
            promote_version("nonexistent-id", 1)

    def test_version_numbers_are_sequential(self):
        """Test that version numbers are always sequential integers starting from 1."""
        # Create initial prompt
        initial_data = PromptCreate(
            title="Version 1",
            content="Content 1"
        )
        prompt = create_prompt_with_version(initial_data)

        # Create multiple versions
        for i in range(2, 11):
            update_data = PromptUpdate(
                title=f"Version {i}",
                content=f"Content {i}"
            )
            version = create_version(prompt.id, update_data)
            assert version.version == i

        # Verify all versions exist
        versions = get_prompt_versions(prompt.id)
        assert len(versions) == 10
        assert [v.version for v in versions] == [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]

    def test_collection_id_preserved_in_versions(self):
        """Test that collection_id is preserved across versions."""
        # Create initial prompt with collection
        initial_data = PromptCreate(
            title="Version 1",
            content="Content 1",
            collection_id="col-123"
        )
        prompt = create_prompt_with_version(initial_data)

        # Create version 2
        update_data = PromptUpdate(
            title="Version 2",
            content="Content 2",
            collection_id="col-123"  # Same collection
        )
        create_version(prompt.id, update_data)

        # Create version 3 with different collection
        update_data = PromptUpdate(
            title="Version 3",
            content="Content 3",
            collection_id="col-456"
        )
        create_version(prompt.id, update_data)

        # Verify all versions have correct collection_id
        version_1 = get_prompt_version(prompt.id, 1)
        version_2 = get_prompt_version(prompt.id, 2)
        version_3 = get_prompt_version(prompt.id, 3)

        assert version_1.collection_id == "col-123"
        assert version_2.collection_id == "col-123"
        assert version_3.collection_id == "col-456"

    def test_promote_preserves_collection_id(self):
        """Test that promoting a version preserves the collection_id from that version."""
        # Create initial prompt
        initial_data = PromptCreate(
            title="Version 1",
            content="Content 1",
            collection_id="col-123"
        )
        prompt = create_prompt_with_version(initial_data)

        # Create version 2 with different collection
        update_data = PromptUpdate(
            title="Version 2",
            content="Content 2",
            collection_id="col-456"
        )
        create_version(prompt.id, update_data)

        # Promote version 1
        promoted = promote_version(prompt.id, 1)

        assert promoted.collection_id == "col-123"

    def test_version_history_preserves_dangling_collection_references(self):
        """Test that version history preserves collection_id even if collection is deleted."""
        # Create initial prompt with collection
        initial_data = PromptCreate(
            title="Version 1",
            content="Content 1",
            collection_id="col-deleted"
        )
        prompt = create_prompt_with_version(initial_data)

        # Create version 2 without collection
        update_data = PromptUpdate(
            title="Version 2",
            content="Content 2",
            collection_id=None
        )
        create_version(prompt.id, update_data)

        # Version 1 should still have the original collection_id
        version_1 = get_prompt_version(prompt.id, 1)
        assert version_1.collection_id == "col-deleted"

class TestVersioningIntegration:
    """Integration tests for versioning with other system components."""

    def test_versioning_with_search_functionality(self):
        """Test that versioning works with existing search functionality."""
        from app.utils import search_prompts

        # Create initial prompt
        initial_data = PromptCreate(
            title="Python Tutorial",
            content="Learn Python programming",
            description="A comprehensive Python tutorial"
        )
        prompt = create_prompt_with_version(initial_data)

        # Create version 2 with different content
        update_data = PromptUpdate(
            title="Advanced Python",
            content="Advanced Python concepts",
            description="Advanced Python programming"
        )
        create_version(prompt.id, update_data)

        # Get all versions
        versions = get_prompt_versions(prompt.id)

        # Search should work on all versions
        python_results = search_prompts(versions, "python")
        assert len(python_results) == 2

        tutorial_results = search_prompts(versions, "tutorial")
        assert len(tutorial_results) == 1
        assert tutorial_results[0].title == "Python Tutorial"

    def test_versioning_with_sorting_functionality(self):
        """Test that versioning works with existing sorting functionality."""
        from app.utils import sort_prompts_by_date

        # Create initial prompt
        initial_data = PromptCreate(
            title="Version 1",
            content="Content 1"
        )
        prompt = create_prompt_with_version(initial_data)

        # Create more versions
        import time
        for i in range(2, 4):
            time.sleep(0.01)  # Ensure different timestamps
            update_data = PromptUpdate(
                title=f"Version {i}",
                content=f"Content {i}"
            )
            create_version(prompt.id, update_data)

        # Get all versions
        versions = get_prompt_versions(prompt.id)

        # Sort by date (descending)
        sorted_versions = sort_prompts_by_date(versions, descending=True)
        assert sorted_versions[0].version == 3
        assert sorted_versions[1].version == 2
        assert sorted_versions[2].version == 1

    def test_versioning_with_filtering_functionality(self):
        """Test that versioning works with existing filtering functionality."""
        from app.utils import filter_prompts_by_collection

        # Create initial prompt with collection
        initial_data = PromptCreate(
            title="Version 1",
            content="Content 1",
            collection_id="col-123"
        )
        prompt = create_prompt_with_version(initial_data)

        # Create version 2 with different collection
        update_data = PromptUpdate(
            title="Version 2",
            content="Content 2",
            collection_id="col-456"
        )
        create_version(prompt.id, update_data)

        # Create version 3 with no collection
        update_data = PromptUpdate(
            title="Version 3",
            content="Content 3",
            collection_id=None
        )
        create_version(prompt.id, update_data)

        # Get all versions
        versions = get_prompt_versions(prompt.id)

        # Filter by collection
        col_123_versions = filter_prompts_by_collection(versions, "col-123")
        assert len(col_123_versions) == 1
        assert col_123_versions[0].version == 1

        col_456_versions = filter_prompts_by_collection(versions, "col-456")
        assert len(col_456_versions) == 1
        assert col_456_versions[0].version == 2

    def test_versioning_preserves_variable_extraction(self):
        """Test that versioning preserves variable extraction functionality."""
        from app.utils import extract_variables
        from app.models import PromptCreate, PromptUpdate

        # Create initial prompt with variables
        initial_data = PromptCreate(
            title="Template 1",
            content="Hello {{name}}, you are {{age}} years old"
        )
        prompt = create_prompt_with_version(initial_data)

        # Create version 2 with different variables
        update_data = PromptUpdate(
            title="Template 2",
            content="Welcome {{user_name}}, your score is {{score}}"
        )
        create_version(prompt.id, update_data)  # Fixed: Added the actual function call

        # Get specific versions
        version_1 = get_prompt_version(prompt.id, 1)
        version_2 = get_prompt_version(prompt.id, 2)

        # Extract variables from each version
        vars_v1 = extract_variables(version_1.content)
        vars_v2 = extract_variables(version_2.content)

        assert vars_v1 == ["name", "age"]
        assert vars_v2 == ["user_name", "score"]

    def test_versioning_preserves_content_validation(self):
        """Test that versioning preserves content validation functionality."""
        from app.utils import validate_prompt_content

        # Create initial prompt with valid content
        initial_data = PromptCreate(
            title="Valid Content",
            content="This is valid content with 10+ characters"
        )
        prompt = create_prompt_with_version(initial_data)

        # Create version 2 with different valid content
        update_data = PromptUpdate(
            title="Another Valid Content",
            content="Another valid content that meets requirements"
        )
        create_version(prompt.id, update_data)

        # Verify content validation works on all versions
        version_1 = get_prompt_version(prompt.id, 1)
        version_2 = get_prompt_version(prompt.id, 2)

        assert validate_prompt_content(version_1.content) == True
        assert validate_prompt_content(version_2.content) == True

class TestVersioningEdgeCases:
    """Edge case tests for prompt versioning."""

    def test_create_version_with_empty_fields(self):
        """Test creating a version with empty or None fields."""
        # Create initial prompt
        initial_data = PromptCreate(
            title="Initial",
            content="Initial content"
        )
        prompt = create_prompt_with_version(initial_data)

        # Create version with empty title (should be validated)
        with pytest.raises(ValueError):
            update_data = PromptUpdate(
                title="",  # Empty title should fail validation
                content="Updated content"
            )
            create_version(prompt.id, update_data)

    def test_create_version_with_minimum_content_length(self):
        """Test creating a version with minimum content length."""
        # Create initial prompt
        initial_data = PromptCreate(
            title="Initial",
            content="Initial content"
        )
        prompt = create_prompt_with_version(initial_data)

        # Create version with exactly 10 characters (minimum)
        update_data = PromptUpdate(
            title="Updated",
            content="1234567890"  # Exactly 10 characters
        )
        version_2 = create_version(prompt.id, update_data)

        assert version_2.version == 2
        assert version_2.content == "1234567890"

    def test_create_version_with_maximum_title_length(self):
        """Test creating a version with maximum title length."""
        # Create initial prompt
        initial_data = PromptCreate(
            title="Initial",
            content="Initial content"
        )
        prompt = create_prompt_with_version(initial_data)

        # Create version with exactly 200 characters (maximum)
        long_title = "A" * 200
        update_data = PromptUpdate(
            title=long_title,
            content="Updated content"
        )
        version_2 = create_version(prompt.id, update_data)

        assert version_2.version == 2
        assert version_2.title == long_title
        assert len(version_2.title) == 200

    def test_create_version_with_maximum_description_length(self):
        """Test creating a version with maximum description length."""
        # Create initial prompt
        initial_data = PromptCreate(
            title="Initial",
            content="Initial content"
        )
        prompt = create_prompt_with_version(initial_data)

        # Create version with exactly 500 characters (maximum)
        long_description = "A" * 500
        update_data = PromptUpdate(
            title="Updated",
            content="Updated content",
            description=long_description
        )
        version_2 = create_version(prompt.id, update_data)

        assert version_2.version == 2
        assert version_2.description == long_description
        assert len(version_2.description) == 500

    def test_promote_first_version(self):
        """Test promoting the first version when it's not the latest."""
        # Create initial prompt
        initial_data = PromptCreate(
            title="Version 1",
            content="Content 1"
        )
        prompt = create_prompt_with_version(initial_data)

        # Create version 2
        update_data = PromptUpdate(
            title="Version 2",
            content="Content 2"
        )
        create_version(prompt.id, update_data)

        # Create version 3
        update_data = PromptUpdate(
            title="Version 3",
            content="Content 3"
        )
        create_version(prompt.id, update_data)

        # Promote version 1
        promoted = promote_version(prompt.id, 1)

        assert promoted.version == 4
        assert promoted.title == "Version 1"
        assert promoted.content == "Content 1"

    def test_promote_middle_version(self):
        """Test promoting a middle version."""
        # Create initial prompt
        initial_data = PromptCreate(
            title="Version 1",
            content="Content 1"
        )
        prompt = create_prompt_with_version(initial_data)

        # Create version 2
        update_data = PromptUpdate(
            title="Version 2",
            content="Content 2"
        )
        create_version(prompt.id, update_data)

        # Create version 3
        update_data = PromptUpdate(
            title="Version 3",
            content="Content 3"
        )
        create_version(prompt.id, update_data)

        # Promote version 2
        promoted = promote_version(prompt.id, 2)

        assert promoted.version == 4
        assert promoted.title == "Version 2"
        assert promoted.content == "Content 2"

    def test_multiple_promotions_in_sequence(self):
        """Test multiple promotions in sequence."""
        # Create initial prompt
        initial_data = PromptCreate(
            title="Version 1",
            content="Content 1"
        )
        prompt = create_prompt_with_version(initial_data)

        # Create version 2
        update_data = PromptUpdate(
            title="Version 2",
            content="Content 2"
        )
        create_version(prompt.id, update_data)

        # Promote version 1
        promote_version(prompt.id, 1)

        # Promote version 2
        promoted_2 = promote_version(prompt.id, 2)

        assert promoted_2.version == 4
        assert promoted_2.title == "Version 2"
        assert promoted_2.content == "Content 2"

        # Get all versions - should have 4 versions total
        versions = get_prompt_versions(prompt.id)
        assert len(versions) == 4
        assert [v.version for v in versions] == [4, 3, 2, 1]

    def test_version_with_special_characters(self):
        """Test creating versions with special characters in content."""
        # Create initial prompt with special characters
        initial_data = PromptCreate(
            title="Special Chars",
            content="Hello {{name}}! How are you? {{age}} years old."
        )
        prompt = create_prompt_with_version(initial_data)

        # Create version with more special characters
        update_data = PromptUpdate(
            title="More Special Chars",
            content="<p>Hello {{user}}!</p> <div>Score: {{score}}</div>"
        )
        version_2 = create_version(prompt.id, update_data)

        assert version_2.version == 2
        assert "<p>" in version_2.content
        assert "</div>" in version_2.content

    def test_version_with_unicode_characters(self):
        """Test creating versions with unicode characters."""
        # Create initial prompt with unicode
        initial_data = PromptCreate(
            title="Unicode Test",
            content="Hello {{café}}, welcome to {{naïve}} world"
        )
        prompt = create_prompt_with_version(initial_data)

        # Create version with more unicode
        update_data = PromptUpdate(
            title="More Unicode",
            content="Welcome {{用户}}, your score is {{分数}"
        )
        version_2 = create_version(prompt.id, update_data)

        assert version_2.version == 2
        assert "用户" in version_2.content
        assert "分数" in version_2.content

    def test_version_with_very_long_content(self):
        """Test creating versions with very long content."""
        # Create initial prompt with long content
        long_content = "A" * 10000
        initial_data = PromptCreate(
            title="Long Content",
            content=long_content
        )
        prompt = create_prompt_with_version(initial_data)

        # Create version with even longer content
        longer_content = "B" * 20000
        update_data = PromptUpdate(
            title="Longer Content",
            content=longer_content
        )
        version_2 = create_version(prompt.id, update_data)

        assert version_2.version == 2
        assert len(version_2.content) == 20000

    def test_version_with_whitespace_content(self):
        """Test creating versions with whitespace in content."""
        # Create initial prompt with whitespace
        initial_data = PromptCreate(
            title="Whitespace Test",
            content="   Hello World   "
        )
        prompt = create_prompt_with_version(initial_data)

        # Create version with more whitespace
        update_data = PromptUpdate(
            title="More Whitespace",
            content="\tHello\tWorld\nWith\tnewlines"
        )
        version_2 = create_version(prompt.id, update_data)

        assert version_2.version == 2
        assert "\t" in version_2.content
        assert "\n" in version_2.content

    def test_version_with_empty_description(self):
        """Test creating versions with empty description."""
        # Create initial prompt with empty description
        initial_data = PromptCreate(
            title="No Description",
            content="Content without description",
            description=""
        )
        prompt = create_prompt_with_version(initial_data)

        # Create version with None description
        update_data = PromptUpdate(
            title="Still No Description",
            content="More content without description",
            description=None
        )
        version_2 = create_version(prompt.id, update_data)

        assert version_2.version == 2
        assert version_2.description is None

if __name__ == "__main__":
    pytest.main()