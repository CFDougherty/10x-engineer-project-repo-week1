"""Tests for utility functions in the app.

This file tests the utility functions in app/utils.py to ensure they work correctly
and handle edge cases appropriately.
"""

import pytest
from datetime import datetime, timedelta
from typing import List
from app.models import Prompt
from app.utils import (
    sort_prompts_by_date,
    filter_prompts_by_collection,
    search_prompts,
    validate_prompt_content,
    extract_variables
)

class TestSortPromptsByDate:
    """Test suite for sort_prompts_by_date function."""

    def test_sort_prompts_descending(self):
        """Test sorting prompts in descending order (newest first)."""
        now = datetime.utcnow()
        prompts = [
            Prompt(title="Oldest", content="content", created_at=now - timedelta(days=3)),
            Prompt(title="Middle", content="content", created_at=now - timedelta(days=1)),
            Prompt(title="Newest", content="content", created_at=now),
        ]

        sorted_prompts = sort_prompts_by_date(prompts, descending=True)

        assert sorted_prompts[0].title == "Newest"
        assert sorted_prompts[1].title == "Middle"
        assert sorted_prompts[2].title == "Oldest"

    def test_sort_prompts_ascending(self):
        """Test sorting prompts in ascending order (oldest first)."""
        now = datetime.utcnow()
        prompts = [
            Prompt(title="Oldest", content="content", created_at=now - timedelta(days=3)),
            Prompt(title="Middle", content="content", created_at=now - timedelta(days=1)),
            Prompt(title="Newest", content="content", created_at=now),
        ]

        sorted_prompts = sort_prompts_by_date(prompts, descending=False)

        assert sorted_prompts[0].title == "Oldest"
        assert sorted_prompts[1].title == "Middle"
        assert sorted_prompts[2].title == "Newest"

    def test_sort_empty_list(self):
        """Test sorting an empty list of prompts."""
        sorted_prompts = sort_prompts_by_date([], descending=True)
        assert sorted_prompts == []

    def test_sort_single_prompt(self):
        """Test sorting a single prompt."""
        now = datetime.utcnow()
        prompt = Prompt(title="Single", content="content", created_at=now)
        sorted_prompts = sort_prompts_by_date([prompt], descending=True)
        assert sorted_prompts == [prompt]

    def test_sort_prompts_with_same_timestamp(self):
        """Test sorting prompts with identical timestamps."""
        now = datetime.utcnow()
        prompts = [
            Prompt(title="First", content="content", created_at=now),
            Prompt(title="Second", content="content", created_at=now),
            Prompt(title="Third", content="content", created_at=now),
        ]

        sorted_prompts = sort_prompts_by_date(prompts, descending=True)
        assert len(sorted_prompts) == 3
        # Order should be preserved when timestamps are equal

class TestFilterPromptsByCollection:
    """Test suite for filter_prompts_by_collection function."""

    def test_filter_prompts_by_collection_id(self):
        """Test filtering prompts by a specific collection ID."""
        prompts = [
            Prompt(title="Prompt 1", content="content", collection_id="col1"),
            Prompt(title="Prompt 2", content="content", collection_id="col2"),
            Prompt(title="Prompt 3", content="content", collection_id="col1"),
            Prompt(title="Prompt 4", content="content", collection_id=None),
        ]

        filtered_prompts = filter_prompts_by_collection(prompts, "col1")

        assert len(filtered_prompts) == 2
        assert filtered_prompts[0].title == "Prompt 1"
        assert filtered_prompts[1].title == "Prompt 3"

    def test_filter_prompts_no_match(self):
        """Test filtering when no prompts match the collection ID."""
        prompts = [
            Prompt(title="Prompt 1", content="content", collection_id="col1"),
            Prompt(title="Prompt 2", content="content", collection_id="col2"),
        ]

        filtered_prompts = filter_prompts_by_collection(prompts, "nonexistent")
        assert filtered_prompts == []

    def test_filter_prompts_empty_list(self):
        """Test filtering an empty list of prompts."""
        filtered_prompts = filter_prompts_by_collection([], "col1")
        assert filtered_prompts == []

    def test_filter_prompts_all_none_collection_id(self):
        """Test filtering when all prompts have None as collection_id."""
        prompts = [
            Prompt(title="Prompt 1", content="content", collection_id=None),
            Prompt(title="Prompt 2", content="content", collection_id=None),
        ]

        filtered_prompts = filter_prompts_by_collection(prompts, "col1")
        assert filtered_prompts == []

    def test_filter_prompts_preserves_order(self):
        """Test that filtering preserves the original order of matching prompts."""
        prompts = [
            Prompt(title="First", content="content", collection_id="col1"),
            Prompt(title="Second", content="content", collection_id="col2"),
            Prompt(title="Third", content="content", collection_id="col1"),
        ]

        filtered_prompts = filter_prompts_by_collection(prompts, "col1")
        assert filtered_prompts[0].title == "First"
        assert filtered_prompts[1].title == "Third"

class TestSearchPrompts:
    """Test suite for search_prompts function."""

    def test_search_by_title(self):
        """Test searching prompts by title."""
        prompts = [
            Prompt(title="Hello World", content="content", description="desc"),
            Prompt(title="Goodbye World", content="content", description="desc"),
            Prompt(title="Python Programming", content="content", description="desc"),
        ]

        results = search_prompts(prompts, "world")
        assert len(results) == 2
        assert results[0].title == "Hello World"
        assert results[1].title == "Goodbye World"

    def test_search_by_description(self):
        """Test searching prompts by description."""
        prompts = [
            Prompt(title="Title 1", content="content", description="This is about Python"),
            Prompt(title="Title 2", content="content", description="This is about JavaScript"),
            Prompt(title="Title 3", content="content", description="More Python content"),
        ]

        results = search_prompts(prompts, "python")
        assert len(results) == 2
        assert results[0].title == "Title 1"
        assert results[1].title == "Title 3"

    def test_search_case_insensitive(self):
        """Test that search is case-insensitive."""
        prompts = [
            Prompt(title="Python", content="content", description="desc"),
            Prompt(title="PYTHON", content="content", description="desc"),
            Prompt(title="python", content="content", description="desc"),
        ]

        results = search_prompts(prompts, "PYTHON")
        assert len(results) == 3

    def test_search_empty_query(self):
        """Test searching with empty query string."""
        prompts = [
            Prompt(title="Title 1", content="content", description="desc"),
            Prompt(title="Title 2", content="content", description="desc"),
        ]

        results = search_prompts(prompts, "")
        assert len(results) == 2

    def test_search_no_results(self):
        """Test searching when no prompts match the query."""
        prompts = [
            Prompt(title="Python", content="content", description="desc"),
            Prompt(title="JavaScript", content="content", description="desc"),
        ]

        results = search_prompts(prompts, "java")
        assert results == []

    def test_search_with_none_description(self):
        """Test searching when some prompts have None description."""
        prompts = [
            Prompt(title="Python", content="content", description=None),
            Prompt(title="JavaScript", content="content", description="desc"),
        ]

        results = search_prompts(prompts, "python")
        assert len(results) == 1
        assert results[0].title == "Python"

    def test_search_preserves_order(self):
        """Test that search results preserve the original order."""
        prompts = [
            Prompt(title="First Python", content="content", description="desc"),
            Prompt(title="Second JavaScript", content="content", description="desc"),
            Prompt(title="Third Python", content="content", description="desc"),
        ]

        results = search_prompts(prompts, "python")
        assert results[0].title == "First Python"
        assert results[1].title == "Third Python"

    def test_search_substring_match(self):
        """Test that search matches substrings correctly."""
        prompts = [
            Prompt(title="Hello World", content="content", description="desc"),
            Prompt(title="World Wide Web", content="content", description="desc"),
        ]

        results = search_prompts(prompts, "world")
        assert len(results) == 2

class TestValidatePromptContent:
    """Test suite for validate_prompt_content function."""

    def test_valid_content(self):
        """Test validation of valid prompt content."""
        assert validate_prompt_content("This is valid content") == True
        assert validate_prompt_content("1234567890") == True
        assert validate_prompt_content("Content with 10+ chars") == True

    def test_invalid_empty_content(self):
        """Test validation of empty content."""
        assert validate_prompt_content("") == False

    def test_invalid_whitespace_only(self):
        """Test validation of whitespace-only content."""
        assert validate_prompt_content("   ") == False
        assert validate_prompt_content("\t\n") == False
        assert validate_prompt_content("   \t   \n   ") == False

    def test_invalid_too_short(self):
        """Test validation of content that's too short."""
        assert validate_prompt_content("Short") == False
        assert validate_prompt_content("123456789") == False  # 9 chars
        assert validate_prompt_content("A") == False

    def test_valid_minimum_length(self):
        """Test validation of content with exactly 10 characters."""
        assert validate_prompt_content("1234567890") == True
        assert validate_prompt_content("abcdefghij") == True

    def test_validation_with_leading_whitespace(self):
        """Test validation with leading whitespace."""
        assert validate_prompt_content("   Valid content here") == True

    def test_validation_with_trailing_whitespace(self):
        """Test validation with trailing whitespace."""
        assert validate_prompt_content("Valid content here   ") == True

    def test_validation_with_both_whitespace(self):
        """Test validation with both leading and trailing whitespace."""
        assert validate_prompt_content("   Valid content here   ") == True

    def test_validation_none_input(self):
        """Test validation with None input."""
        assert validate_prompt_content(None) == False

class TestExtractVariables:
    """Test suite for extract_variables function."""

    def test_extract_single_variable(self):
        """Test extracting a single variable."""
        content = "Hello {{name}}!"
        variables = extract_variables(content)
        assert variables == ["name"]

    def test_extract_multiple_variables(self):
        """Test extracting multiple variables."""
        content = "Hello {{name}}, you are {{age}} years old!"
        variables = extract_variables(content)
        assert variables == ["name", "age"]

    def test_extract_repeated_variables(self):
        """Test extracting repeated variables."""
        content = "{{name}} is {{name}} and {{age}} is {{age}}"
        variables = extract_variables(content)
        assert variables == ["name", "name", "age", "age"]

    def test_extract_no_variables(self):
        """Test extracting when no variables are present."""
        content = "Hello World!"
        variables = extract_variables(content)
        assert variables == []

    def test_extract_empty_string(self):
        """Test extracting from empty string."""
        content = ""
        variables = extract_variables(content)
        assert variables == []

    def test_extract_variables_with_underscores(self):
        """Test extracting variables with underscores."""
        content = "Hello {{user_name}} and {{first_name}}!"
        variables = extract_variables(content)
        assert variables == ["user_name", "first_name"]

    def test_extract_variables_with_numbers(self):
        """Test extracting variables with numbers."""
        content = "Hello {{user123}} and {{var_456}}!"
        variables = extract_variables(content)
        assert variables == ["user123", "var_456"]

    def test_extract_malformed_variables(self):
        """Test that malformed variables are not extracted."""
        content = "Hello {{name and {{age}} and {{}}"
        variables = extract_variables(content)
        assert variables == ["name", "age"]

    def test_extract_variables_with_special_chars(self):
        """Test extracting variables with special characters in content."""
        content = "Hello {{name}}! How are you? {{age}} years old."
        variables = extract_variables(content)
        assert variables == ["name", "age"]

    def test_extract_variables_preserves_order(self):
        """Test that variables are extracted in order of appearance."""
        content = "{{third}} {{first}} {{second}}"
        variables = extract_variables(content)
        assert variables == ["third", "first", "second"]

    def test_extract_variables_case_sensitive(self):
        """Test that variable names are case-sensitive."""
        content = "{{Name}} and {{name}}"
        variables = extract_variables(content)
        assert variables == ["Name", "name"]

if __name__ == "__main__":
    pytest.main()
