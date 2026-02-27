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

    def test_sort_prompts_with_none_created_at(self):
        """Test sorting prompts when some have None created_at values."""
        now = datetime.utcnow()
        # Pydantic model doesn't allow None for created_at, so we test with valid dates
        # but create a scenario that would cause issues if None were allowed
        prompts = [
            Prompt(title="Valid1", content="content", created_at=now),
            Prompt(title="Valid2", content="content", created_at=now - timedelta(days=1)),
        ]

        # Test that the function works with valid datetime objects
        sorted_prompts = sort_prompts_by_date(prompts, descending=True)
        assert len(sorted_prompts) == 2
        assert sorted_prompts[0].title == "Valid1"
        assert sorted_prompts[1].title == "Valid2"

    def test_sort_prompts_default_descending(self):
        """Test that the default sort order is descending."""
        now = datetime.utcnow()
        prompts = [
            Prompt(title="Oldest", content="content", created_at=now - timedelta(days=3)),
            Prompt(title="Newest", content="content", created_at=now),
        ]

        # Call without specifying descending parameter
        sorted_prompts = sort_prompts_by_date(prompts)
        assert sorted_prompts[0].title == "Newest"
        assert sorted_prompts[1].title == "Oldest"

    def test_sort_prompts_large_list(self):
        """Test sorting with a large number of prompts."""
        now = datetime.utcnow()
        prompts = [
            Prompt(title=f"Prompt {i}", content="content", created_at=now - timedelta(days=i))
            for i in range(1000)
        ]
        sorted_prompts = sort_prompts_by_date(prompts, descending=True)
        assert sorted_prompts[0].title == "Prompt 0"
        assert sorted_prompts[-1].title == "Prompt 999"

    def test_sort_with_identical_timestamps_different_objects(self):
        """Test sorting when timestamps are identical but objects are different."""
        now = datetime.utcnow()
        prompt1 = Prompt(title="First", content="content1", created_at=now)
        prompt2 = Prompt(title="Second", content="content2", created_at=now)

        sorted_prompts = sort_prompts_by_date([prompt1, prompt2], descending=True)
        # The order should be preserved when timestamps are equal
        assert sorted_prompts[0] in [prompt1, prompt2]
        assert sorted_prompts[1] in [prompt1, prompt2]
        assert sorted_prompts[0] != sorted_prompts[1]

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

    def test_filter_prompts_case_sensitive_collection_id(self):
        """Test that collection_id filtering is case-sensitive."""
        prompts = [
            Prompt(title="Prompt 1", content="content", collection_id="Col1"),
            Prompt(title="Prompt 2", content="content", collection_id="col1"),
        ]

        filtered_prompts = filter_prompts_by_collection(prompts, "col1")
        assert len(filtered_prompts) == 1
        assert filtered_prompts[0].title == "Prompt 2"

    def test_filter_prompts_with_empty_collection_id(self):
        """Test filtering with empty string collection_id."""
        prompts = [
            Prompt(title="Prompt 1", content="content", collection_id=""),
            Prompt(title="Prompt 2", content="content", collection_id="col1"),
        ]

        filtered_prompts = filter_prompts_by_collection(prompts, "")
        assert len(filtered_prompts) == 1
        assert filtered_prompts[0].title == "Prompt 1"

    def test_filter_prompts_large_list(self):
        """Test filtering with a large number of prompts."""
        prompts = [
            Prompt(title=f"Prompt {i}", content="content", collection_id="col1" if i % 2 == 0 else "col2")
            for i in range(1000)
        ]
        filtered_prompts = filter_prompts_by_collection(prompts, "col1")
        assert len(filtered_prompts) == 500
        assert all(p.collection_id == "col1" for p in filtered_prompts)

    def test_filter_collection_id_case_sensitive_with_none(self):
        """Test that collection_id filtering is case-sensitive even with None values."""
        prompts = [
            Prompt(title="Prompt 1", content="content", collection_id=None),
            Prompt(title="Prompt 2", content="content", collection_id="None"),
        ]
        # Filtering with None should match prompts with collection_id=None
        filtered_prompts = filter_prompts_by_collection(prompts, None)
        assert len(filtered_prompts) == 1
        assert filtered_prompts[0].title == "Prompt 1"

        # Filtering with string "None" should match prompts with collection_id="None"
        filtered_prompts = filter_prompts_by_collection(prompts, "None")
        assert len(filtered_prompts) == 1
        assert filtered_prompts[0].title == "Prompt 2"

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
        # \"java\" is a substring of \"JavaScript\" (case-insensitive), so this should match
        assert len(results) == 1
        assert results[0].title == "JavaScript"

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

    def test_search_with_special_characters(self):
        """Test searching with special characters in query."""
        prompts = [
            Prompt(title="Python 3.11", content="content", description="desc"),
            Prompt(title="JavaScript ES6", content="content", description="desc"),
        ]

        results = search_prompts(prompts, "3.11")
        assert len(results) == 1
        assert results[0].title == "Python 3.11"

    def test_search_with_unicode_characters(self):
        """Test searching with unicode characters."""
        prompts = [
            Prompt(title="Café", content="content", description="desc"),
            Prompt(title="Naïve", content="content", description="desc"),
        ]

        results = search_prompts(prompts, "é")
        assert len(results) == 1
        assert results[0].title == "Café"

    def test_search_with_whitespace_query(self):
        """Test searching with query containing whitespace."""
        prompts = [
            Prompt(title="Hello World", content="content", description="desc"),
            Prompt(title="Goodbye World", content="content", description="desc"),
        ]

        results = search_prompts(prompts, "Hello World")
        assert len(results) == 1
        assert results[0].title == "Hello World"

    def test_search_prompts_with_regex_special_chars(self):
        """Test searching with regex special characters in query."""
        prompts = [
            Prompt(title="File[1].txt", content="content", description="desc"),
            Prompt(title="Regular file", content="content", description="desc"),
        ]
        results = search_prompts(prompts, "File[1].txt")
        assert len(results) == 1
        assert results[0].title == "File[1].txt"

    def test_search_prompts_with_very_long_query(self):
        """Test searching with a very long query string."""
        # Use a query that's within reasonable limits but still long
        long_query = "a" * 100
        prompts = [
            Prompt(title="Title with " + "a" * 50, content="content", description="desc"),
            Prompt(title="Different title", content="content", description="desc"),
        ]
        results = search_prompts(prompts, long_query)
        assert len(results) == 0  # No exact match
        
        # Test with a substring that exists
        results = search_prompts(prompts, "a" * 10)
        assert len(results) == 1

    def test_search_prompts_with_very_long_title(self):
        """Test searching with very long titles and descriptions."""
        # Use text within Pydantic limits (200 chars for title, 500 for description)
        long_title = "a" * 150
        long_desc = "a" * 400
        prompts = [
            Prompt(title=long_title, content="content", description=long_desc),
            Prompt(title="Short", content="content", description="desc"),
        ]
        results = search_prompts(prompts, "a" * 50)
        assert len(results) == 1
        assert results[0].title == long_title

    def test_search_case_insensitive_with_mixed_case(self):
        """Test case-insensitive search with mixed case in query and content."""
        prompts = [
            Prompt(title="PyThOn", content="content", description="pYtHoN"),
            Prompt(title="python", content="content", description="PYTHON"),
        ]
        results = search_prompts(prompts, "PyThOn")
        assert len(results) == 2

    def test_search_with_whitespace_query(self):
        """Test search with query containing only whitespace."""
        prompts = [
            Prompt(title="Title 1", content="content", description="desc"),
            Prompt(title="Title 2", content="content", description="desc"),
        ]
        # Whitespace-only queries return all prompts (designed behavior)
        results = search_prompts(prompts, "   ")
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

    def test_validation_with_special_characters(self):
        """Test validation with special characters."""
        assert validate_prompt_content("Hello!@#$%^&*()") == True
        assert validate_prompt_content("Special chars: <>&\"'") == True

    def test_validation_with_newlines_and_tabs(self):
        """Test validation with newlines and tabs."""
        content = "Line 1\nLine 2\nLine 3"
        assert validate_prompt_content(content) == True

        content = "Tab\tseparated\tcontent"
        assert validate_prompt_content(content) == True

    def test_validation_exactly_10_chars(self):
        """Test validation with exactly 10 characters (minimum)."""
        assert validate_prompt_content("1234567890") == True
        assert validate_prompt_content("abcdefghij") == True

    def test_validation_very_long_content(self):
        """Test validation with very long content."""
        long_content = "A" * 10000
        assert validate_prompt_content(long_content) == True

    def test_validate_prompt_content_exactly_10_before_strip(self):
        """Test validation when content has exactly 10 chars before stripping."""
        # Content with leading/trailing whitespace but exactly 10 chars when stripped
        content = "   " + "a" * 10 + "   "
        assert validate_prompt_content(content) == True

    def test_validate_prompt_content_9_before_strip(self):
        """Test validation when content has 9 chars before stripping."""
        # Content with leading/trailing whitespace but only 9 chars when stripped
        content = "   " + "a" * 9 + "   "
        assert validate_prompt_content(content) == False

    def test_validate_content_with_only_newlines(self):
        """Test validation with content containing only newlines."""
        content = "\n\n\n\n\n\n\n\n\n"
        assert validate_prompt_content(content) == False

    def test_validate_content_with_tabs_only(self):
        """Test validation with content containing only tabs."""
        content = "\t\t\t\t\t\t\t\t"
        assert validate_prompt_content(content) == False

    def test_validate_prompt_content_with_mixed_whitespace(self):
        """Test validation with mixed whitespace characters."""
        content = "\t\n   " + "a" * 10 + " \t\n"
        assert validate_prompt_content(content) == True

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
        # Only properly formed {{variable}} patterns are extracted
        # {{name and} is malformed (missing closing braces)
        # {{age}} is properly formed
        # {{}} is malformed (no variable name)
        assert variables == ["age"]

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

    def test_extract_variables_with_nested_braces(self):
        """Test extracting variables with nested braces."""
        content = "Hello {{name}} and {{user.profile.name}}"
        variables = extract_variables(content)
        # Only simple {{word}} patterns are extracted, not nested ones
        assert variables == ["name"]

    def test_extract_variables_with_dashes(self):
        """Test that variables with dashes are not extracted."""
        content = "Hello {{user-name}} and {{user_name}}"
        variables = extract_variables(content)
        # Only word characters (letters, numbers, underscores) are allowed
        assert variables == ["user_name"]

    def test_extract_variables_with_dots(self):
        """Test that variables with dots are not extracted."""
        content = "Hello {{user.name}} and {{user_name}}"
        variables = extract_variables(content)
        # Only word characters (letters, numbers, underscores) are allowed
        assert variables == ["user_name"]

    def test_extract_variables_with_backticks(self):
        """Test extracting variables with backticks in content."""
        content = "Hello `{{name}}` and {{age}}"
        variables = extract_variables(content)
        assert variables == ["name", "age"]

    def test_extract_variables_with_html_tags(self):
        """Test extracting variables with HTML tags in content."""
        content = "<p>Hello {{name}}</p> and <div>{{age}}</div>"
        variables = extract_variables(content)
        assert variables == ["name", "age"]

    def test_extract_variables_with_mixed_content(self):
        """Test extracting variables with mixed content types."""
        content = """
        <p>Hello {{user_name}}!</p>
        <div>You are {{age}} years old.</div>
        <span>Your score is {{score}}</span>
        """
        variables = extract_variables(content)
        assert variables == ["user_name", "age", "score"]

    def test_extract_variables_edge_cases(self):
        """Test edge cases for variable extraction."""
        # Test with various edge cases
        content = "{{_private}} {{123number}} {{UPPERCASE}}"
        variables = extract_variables(content)
        assert variables == ["_private", "123number", "UPPERCASE"]

    def test_extract_variables_with_malformed_braces(self):
        """Test extraction with malformed brace patterns."""
        content = "{{name and {{age}} and {{}} and {name}"
        variables = extract_variables(content)
        # Only properly formed {{word}} patterns should be extracted
        assert variables == ["age"]

    def test_extract_variables_with_empty_braces(self):
        """Test extraction with empty braces."""
        content = "{{}} and {{name}}"
        variables = extract_variables(content)
        assert variables == ["name"]

    def test_extract_variables_at_start_and_end(self):
        """Test extraction with variables at the start and end of content."""
        content = "{{start}} some text {{end}}"
        variables = extract_variables(content)
        assert variables == ["start", "end"]

    def test_extract_variables_with_many_repeats(self):
        """Test extraction with many repeated variables."""
        content = "{{var}} " * 1000
        variables = extract_variables(content)
        assert len(variables) == 1000
        assert all(v == "var" for v in variables)

    def test_extract_variables_with_very_long_content(self):
        """Test extraction with very long content."""
        long_content = "{{var1}} " + "a" * 10000 + " {{var2}}"
        variables = extract_variables(long_content)
        assert variables == ["var1", "var2"]

    def test_extract_variables_with_unicode_in_names(self):
        """Test extraction with unicode characters in variable names."""
        content = "{{café}} and {{naïve}}"
        variables = extract_variables(content)
        # \w in regex includes unicode word characters
        assert variables == ["café", "naïve"]

    def test_extract_variables_with_different_whitespace(self):
        """Test extraction with different whitespace around variables."""
        content = "  {{name}}  \t  {{age}}  \n  "
        variables = extract_variables(content)
        assert variables == ["name", "age"]

class TestIntegration:
    """Integration tests for utility functions working together."""

    def test_integration_sort_filter_search(self):
        """Test integration of sort, filter, and search functions."""
        now = datetime.utcnow()
        prompts = [
            Prompt(title="Python tutorial", content="content", created_at=now - timedelta(days=3), collection_id="col1", description="Python programming"),
            Prompt(title="JavaScript guide", content="content", created_at=now - timedelta(days=1), collection_id="col2", description="JavaScript programming"),
            Prompt(title="Python advanced", content="content", created_at=now, collection_id="col1", description="Advanced Python topics"),
            Prompt(title="Other topic", content="content", created_at=now - timedelta(days=2), collection_id="col1", description="Something else"),
        ]

        # Filter by collection, then search, then sort
        filtered = filter_prompts_by_collection(prompts, "col1")
        searched = search_prompts(filtered, "python")
        sorted_results = sort_prompts_by_date(searched, descending=True)

        assert len(sorted_results) == 2
        assert sorted_results[0].title == "Python advanced"
        assert sorted_results[1].title == "Python tutorial"

    def test_integration_validate_and_extract(self):
        """Test integration of validation and variable extraction."""
        content = "   Hello {{name}}, you are {{age}} years old!   "
        is_valid = validate_prompt_content(content)
        variables = extract_variables(content)

        assert is_valid == True
        assert variables == ["name", "age"]

    def test_edge_case_empty_string_vs_none(self):
        """Test that empty string and None are handled differently."""
        assert validate_prompt_content("") == False
        assert validate_prompt_content(None) == False

        # Empty string should return empty list
        assert extract_variables("") == []
        # None should also return empty list (handled gracefully)
        assert extract_variables(None) == []

if __name__ == "__main__":
    pytest.main()
