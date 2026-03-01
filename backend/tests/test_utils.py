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
        """Prompts are returned newest-first when descending=True."""
        from datetime import timezone
        now = datetime.now(timezone.utc).replace(tzinfo=None)
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
        """Prompts are returned oldest-first when descending=False."""
        from datetime import timezone
        now = datetime.now(timezone.utc).replace(tzinfo=None)
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
        """Sorting an empty list returns an empty list."""
        sorted_prompts = sort_prompts_by_date([], descending=True)
        assert sorted_prompts == []

    def test_sort_single_prompt(self):
        """Sorting a single-element list returns that same element."""
        from datetime import timezone
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        prompt = Prompt(title="Single", content="content", created_at=now)
        sorted_prompts = sort_prompts_by_date([prompt], descending=True)
        assert sorted_prompts == [prompt]

    def test_sort_prompts_with_same_timestamp(self):
        """Sorting prompts with identical timestamps returns all prompts without error.

        Note:
            The sort is stable: prompts with equal timestamps preserve their
            original relative order.
        """
        from datetime import timezone
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        prompts = [
            Prompt(title="First", content="content", created_at=now),
            Prompt(title="Second", content="content", created_at=now),
            Prompt(title="Third", content="content", created_at=now),
        ]

        sorted_prompts = sort_prompts_by_date(prompts, descending=True)
        assert len(sorted_prompts) == 3

    def test_sort_prompts_with_none_created_at(self):
        """sort_prompts_by_date works correctly when all created_at values are valid datetimes.

        Note:
            The Pydantic model does not allow None for created_at. This test
            documents that the function handles valid datetime objects correctly
            and does not need to guard against None values.
        """
        from datetime import timezone
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        prompts = [
            Prompt(title="Valid1", content="content", created_at=now),
            Prompt(title="Valid2", content="content", created_at=now - timedelta(days=1)),
        ]

        sorted_prompts = sort_prompts_by_date(prompts, descending=True)
        assert len(sorted_prompts) == 2
        assert sorted_prompts[0].title == "Valid1"
        assert sorted_prompts[1].title == "Valid2"

    def test_sort_prompts_default_descending(self):
        """The default sort order is descending (newest first) when no argument is given."""
        from datetime import timezone
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        prompts = [
            Prompt(title="Oldest", content="content", created_at=now - timedelta(days=3)),
            Prompt(title="Newest", content="content", created_at=now),
        ]

        sorted_prompts = sort_prompts_by_date(prompts)
        assert sorted_prompts[0].title == "Newest"
        assert sorted_prompts[1].title == "Oldest"

    def test_sort_prompts_large_list(self):
        """Sorting 1000 prompts by date produces the correct order."""
        from datetime import timezone
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        prompts = [
            Prompt(title=f"Prompt {i}", content="content", created_at=now - timedelta(days=i))
            for i in range(1000)
        ]
        sorted_prompts = sort_prompts_by_date(prompts, descending=True)
        assert sorted_prompts[0].title == "Prompt 0"
        assert sorted_prompts[-1].title == "Prompt 999"

    def test_sort_with_identical_timestamps_different_objects(self):
        """When timestamps are equal, all distinct prompt objects are present in the result."""
        from datetime import timezone
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        prompt1 = Prompt(title="First", content="content1", created_at=now)
        prompt2 = Prompt(title="Second", content="content2", created_at=now)

        sorted_prompts = sort_prompts_by_date([prompt1, prompt2], descending=True)
        assert sorted_prompts[0] in [prompt1, prompt2]
        assert sorted_prompts[1] in [prompt1, prompt2]
        assert sorted_prompts[0] != sorted_prompts[1]

class TestFilterPromptsByCollection:
    """Test suite for filter_prompts_by_collection function."""

    def test_filter_prompts_by_collection_id(self):
        """Only prompts whose collection_id matches the given value are returned."""
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
        """An empty list is returned when no prompts match the collection ID."""
        prompts = [
            Prompt(title="Prompt 1", content="content", collection_id="col1"),
            Prompt(title="Prompt 2", content="content", collection_id="col2"),
        ]

        filtered_prompts = filter_prompts_by_collection(prompts, "nonexistent")
        assert filtered_prompts == []

    def test_filter_prompts_empty_list(self):
        """Filtering an empty list of prompts returns an empty list."""
        filtered_prompts = filter_prompts_by_collection([], "col1")
        assert filtered_prompts == []

    def test_filter_prompts_all_none_collection_id(self):
        """An empty list is returned when all prompts have collection_id=None."""
        prompts = [
            Prompt(title="Prompt 1", content="content", collection_id=None),
            Prompt(title="Prompt 2", content="content", collection_id=None),
        ]

        filtered_prompts = filter_prompts_by_collection(prompts, "col1")
        assert filtered_prompts == []

    def test_filter_prompts_preserves_order(self):
        """Filtering preserves the original order of matching prompts."""
        prompts = [
            Prompt(title="First", content="content", collection_id="col1"),
            Prompt(title="Second", content="content", collection_id="col2"),
            Prompt(title="Third", content="content", collection_id="col1"),
        ]

        filtered_prompts = filter_prompts_by_collection(prompts, "col1")
        assert filtered_prompts[0].title == "First"
        assert filtered_prompts[1].title == "Third"

    def test_filter_prompts_case_sensitive_collection_id(self):
        """collection_id filtering is case-sensitive."""
        prompts = [
            Prompt(title="Prompt 1", content="content", collection_id="Col1"),
            Prompt(title="Prompt 2", content="content", collection_id="col1"),
        ]

        filtered_prompts = filter_prompts_by_collection(prompts, "col1")
        assert len(filtered_prompts) == 1
        assert filtered_prompts[0].title == "Prompt 2"

    def test_filter_prompts_with_empty_collection_id(self):
        """Filtering with an empty string matches prompts whose collection_id is also empty."""
        prompts = [
            Prompt(title="Prompt 1", content="content", collection_id=""),
            Prompt(title="Prompt 2", content="content", collection_id="col1"),
        ]

        filtered_prompts = filter_prompts_by_collection(prompts, "")
        assert len(filtered_prompts) == 1
        assert filtered_prompts[0].title == "Prompt 1"

    def test_filter_prompts_large_list(self):
        """Filtering 1000 prompts returns exactly those whose collection_id matches."""
        prompts = [
            Prompt(title=f"Prompt {i}", content="content", collection_id="col1" if i % 2 == 0 else "col2")
            for i in range(1000)
        ]
        filtered_prompts = filter_prompts_by_collection(prompts, "col1")
        assert len(filtered_prompts) == 500
        assert all(p.collection_id == "col1" for p in filtered_prompts)

    def test_filter_collection_id_case_sensitive_with_none(self):
        """Filtering distinguishes between Python None and the string "None" as collection_id values.

        Note:
            Passing None as the filter value matches prompts with collection_id=None.
            Passing the string "None" matches prompts with collection_id="None".
        """
        prompts = [
            Prompt(title="Prompt 1", content="content", collection_id=None),
            Prompt(title="Prompt 2", content="content", collection_id="None"),
        ]
        filtered_prompts = filter_prompts_by_collection(prompts, None)
        assert len(filtered_prompts) == 1
        assert filtered_prompts[0].title == "Prompt 1"

        filtered_prompts = filter_prompts_by_collection(prompts, "None")
        assert len(filtered_prompts) == 1
        assert filtered_prompts[0].title == "Prompt 2"

class TestSearchPrompts:
    """Test suite for search_prompts function."""

    def test_search_by_title(self):
        """search_prompts returns prompts whose title contains the query substring."""
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
        """search_prompts returns prompts whose description contains the query substring."""
        prompts = [
            Prompt(title="Title 1", content="content", description="This is about Python"),
            Prompt(title="Title 2", content="content", description="This is about JavaScript"),
            Prompt(title="Title 3", content="content", description="More Python content"),
        ]

        results = search_prompts(prompts, "python")
        assert len(results) == 2
        titles = [r.title for r in results]
        assert "Title 1" in titles
        assert "Title 3" in titles

    def test_search_case_insensitive(self):
        """search_prompts matches regardless of case differences between query and content."""
        prompts = [
            Prompt(title="Python", content="content", description="desc"),
            Prompt(title="PYTHON", content="content", description="desc"),
            Prompt(title="python", content="content", description="desc"),
        ]

        results = search_prompts(prompts, "PYTHON")
        assert len(results) == 3

    def test_search_empty_query(self):
        """An empty query string returns all prompts unchanged."""
        prompts = [
            Prompt(title="Title 1", content="content", description="desc"),
            Prompt(title="Title 2", content="content", description="desc"),
        ]

        results = search_prompts(prompts, "")
        assert len(results) == 2

    def test_search_no_results(self):
        """search_prompts matches "java" as a case-insensitive substring of "JavaScript"."""
        prompts = [
            Prompt(title="Python", content="content", description="desc"),
            Prompt(title="JavaScript", content="content", description="desc"),
        ]

        results = search_prompts(prompts, "java")
        assert len(results) == 1
        assert results[0].title == "JavaScript"

    def test_search_with_none_description(self):
        """search_prompts handles prompts with None description without error."""
        prompts = [
            Prompt(title="Python", content="content", description=None),
            Prompt(title="JavaScript", content="content", description="desc"),
        ]

        results = search_prompts(prompts, "python")
        assert len(results) == 1
        assert results[0].title == "Python"

    def test_search_preserves_order(self):
        """search_prompts preserves the original relative order of matching results."""
        prompts = [
            Prompt(title="First Python", content="content", description="desc"),
            Prompt(title="Second JavaScript", content="content", description="desc"),
            Prompt(title="Third Python", content="content", description="desc"),
        ]

        results = search_prompts(prompts, "python")
        assert results[0].title == "First Python"
        assert results[1].title == "Third Python"

    def test_search_substring_match(self):
        """search_prompts matches partial substrings within titles."""
        prompts = [
            Prompt(title="Hello World", content="content", description="desc"),
            Prompt(title="World Wide Web", content="content", description="desc"),
        ]

        results = search_prompts(prompts, "world")
        assert len(results) == 2

    def test_search_with_special_characters(self):
        """search_prompts handles special characters like dots in the query."""
        prompts = [
            Prompt(title="Python 3.11", content="content", description="desc"),
            Prompt(title="JavaScript ES6", content="content", description="desc"),
        ]

        results = search_prompts(prompts, "3.11")
        assert len(results) == 1
        assert results[0].title == "Python 3.11"

    def test_search_with_unicode_characters(self):
        """search_prompts correctly matches unicode characters in titles."""
        prompts = [
            Prompt(title="Café", content="content", description="desc"),
            Prompt(title="Naïve", content="content", description="desc"),
            Prompt(title="Python", content="content", description="desc"),
        ]

        results = search_prompts(prompts, "é")
        assert len(results) == 1
        assert results[0].title == "Café"

        results = search_prompts(prompts, "ï")
        assert len(results) == 1
        assert results[0].title == "Naïve"

    def test_search_with_whitespace_query(self):
        """search_prompts matches multi-word queries as a substring."""
        prompts = [
            Prompt(title="Hello World", content="content", description="desc"),
            Prompt(title="Goodbye World", content="content", description="desc"),
        ]

        results = search_prompts(prompts, "Hello World")
        assert len(results) == 1
        assert results[0].title == "Hello World"

    def test_search_prompts_with_regex_special_chars(self):
        """search_prompts treats query characters like brackets as literals, not regex."""
        prompts = [
            Prompt(title="File[1].txt", content="content", description="desc"),
            Prompt(title="Regular file", content="content", description="desc"),
        ]
        results = search_prompts(prompts, "File[1].txt")
        assert len(results) == 1
        assert results[0].title == "File[1].txt"

    def test_search_prompts_with_very_long_query(self):
        """search_prompts handles a long query string without error.

        Note:
            A query longer than any field value will produce no matches.
            A shorter repeated substring will match the relevant prompt.
        """
        long_query = "a" * 100
        prompts = [
            Prompt(title="Title with " + "a" * 50, content="content", description="desc"),
            Prompt(title="Different title", content="content", description="desc"),
        ]
        results = search_prompts(prompts, long_query)
        assert len(results) == 0

        results = search_prompts(prompts, "a" * 10)
        assert len(results) == 1

    def test_search_prompts_with_very_long_title(self):
        """search_prompts works correctly when titles and descriptions are near their maximum lengths.

        Note:
            Title max is 200 characters; description max is 500 characters.
        """
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
        """search_prompts matches all prompts that contain the query regardless of casing."""
        prompts = [
            Prompt(title="PyThOn", content="content", description="pYtHoN"),
            Prompt(title="python", content="content", description="PYTHON"),
        ]
        results = search_prompts(prompts, "PyThOn")
        assert len(results) == 2

    def test_search_with_whitespace_only_query(self):
        """A whitespace-only query string returns all prompts unchanged.

        Note:
            search_prompts treats any query that is empty or consists entirely
            of whitespace as a no-op and returns the full input list.
        """
        prompts = [
            Prompt(title="Title 1", content="content", description="desc"),
            Prompt(title="Title 2", content="content", description="desc"),
        ]
        results = search_prompts(prompts, "   ")
        assert len(results) == 2

class TestValidatePromptContent:
    """Test suite for validate_prompt_content function.

    Note:
        validate_prompt_content requires at least 10 non-whitespace characters
        after stripping leading and trailing whitespace. The Pydantic model only
        enforces a 1-character minimum, so there is a deliberate gap between
        model-level and utility-level validation.
    """

    def test_valid_content(self):
        """Content with 10 or more stripped characters returns True."""
        assert validate_prompt_content("This is valid content") == True
        assert validate_prompt_content("1234567890") == True
        assert validate_prompt_content("Content with 10+ chars") == True

    def test_invalid_empty_content(self):
        """Empty string returns False."""
        assert validate_prompt_content("") == False

    def test_invalid_whitespace_only(self):
        """Whitespace-only strings of any composition return False."""
        assert validate_prompt_content("   ") == False
        assert validate_prompt_content("\t\n") == False
        assert validate_prompt_content("   \t   \n   ") == False

    def test_invalid_too_short(self):
        """Content with fewer than 10 stripped characters returns False."""
        assert validate_prompt_content("Short") == False
        assert validate_prompt_content("123456789") == False
        assert validate_prompt_content("A") == False

    def test_valid_minimum_length(self):
        """Content with exactly 10 stripped characters returns True."""
        assert validate_prompt_content("1234567890") == True
        assert validate_prompt_content("abcdefghij") == True

    def test_validation_with_leading_whitespace(self):
        """Leading whitespace is stripped before the length check."""
        assert validate_prompt_content("   Valid content here") == True

    def test_validation_with_trailing_whitespace(self):
        """Trailing whitespace is stripped before the length check."""
        assert validate_prompt_content("Valid content here   ") == True

    def test_validation_with_both_whitespace(self):
        """Both leading and trailing whitespace are stripped before the length check."""
        assert validate_prompt_content("   Valid content here   ") == True

    def test_validation_none_input(self):
        """None input returns False."""
        assert validate_prompt_content(None) == False

    def test_validation_with_special_characters(self):
        """Content composed of special characters passes when 10+ stripped chars are present."""
        assert validate_prompt_content("Hello!@#$%^&*()") == True
        assert validate_prompt_content("Special chars: <>&\"'") == True

    def test_validation_with_newlines_and_tabs(self):
        """Embedded newlines and tabs count toward the stripped character length."""
        content = "Line 1\nLine 2\nLine 3"
        assert validate_prompt_content(content) == True

        content = "Tab\tseparated\tcontent"
        assert validate_prompt_content(content) == True

    def test_validation_exactly_10_chars(self):
        """Content at exactly 10 stripped characters passes validation."""
        assert validate_prompt_content("1234567890") == True
        assert validate_prompt_content("abcdefghij") == True

    def test_validation_very_long_content(self):
        """Very long content passes validation."""
        long_content = "A" * 10000
        assert validate_prompt_content(long_content) == True

    def test_validate_prompt_content_exactly_10_before_strip(self):
        """Content that has exactly 10 chars after stripping surrounding whitespace passes."""
        content = "   " + "a" * 10 + "   "
        assert validate_prompt_content(content) == True

    def test_validate_prompt_content_9_before_strip(self):
        """Content that has only 9 chars after stripping surrounding whitespace fails."""
        content = "   " + "a" * 9 + "   "
        assert validate_prompt_content(content) == False

    def test_validate_content_with_only_newlines(self):
        """Content consisting only of newlines returns False."""
        content = "\n\n\n\n\n\n\n\n\n"
        assert validate_prompt_content(content) == False

    def test_validate_content_with_tabs_only(self):
        """Content consisting only of tabs returns False."""
        content = "\t\t\t\t\t\t\t\t"
        assert validate_prompt_content(content) == False

    def test_validate_prompt_content_with_mixed_whitespace(self):
        """Mixed surrounding whitespace characters are stripped before the length check."""
        content = "\t\n   " + "a" * 10 + " \t\n"
        assert validate_prompt_content(content) == True

class TestExtractVariables:
    """Test suite for extract_variables function.

    Note:
        The function uses the regex pattern ``{{\\w+}}`` to extract variable
        placeholders from template content. Only double-brace-wrapped sequences
        of word characters (letters, digits, underscores, and unicode word chars)
        are extracted. Patterns with non-word characters inside the braces
        (dashes, dots, spaces) are not matched. Empty ``{{}}`` patterns are
        also not matched.
    """

    def test_extract_single_variable(self):
        """A single well-formed {{variable}} placeholder is extracted."""
        content = "Hello {{name}}!"
        variables = extract_variables(content)
        assert variables == ["name"]

    def test_extract_multiple_variables(self):
        """Multiple well-formed placeholders are all extracted."""
        content = "Hello {{name}}, you are {{age}} years old!"
        variables = extract_variables(content)
        assert variables == ["name", "age"]

    def test_extract_repeated_variables(self):
        """Repeated occurrences of the same placeholder are each extracted individually."""
        content = "{{name}} is {{name}} and {{age}} is {{age}}"
        variables = extract_variables(content)
        assert variables == ["name", "name", "age", "age"]

    def test_extract_no_variables(self):
        """Content with no placeholders yields an empty list."""
        content = "Hello World!"
        variables = extract_variables(content)
        assert variables == []

    def test_extract_empty_string(self):
        """An empty string yields an empty list."""
        content = ""
        variables = extract_variables(content)
        assert variables == []

    def test_extract_variables_with_underscores(self):
        """Underscores in variable names are valid and extracted correctly."""
        content = "Hello {{user_name}} and {{first_name}}!"
        variables = extract_variables(content)
        assert variables == ["user_name", "first_name"]

    def test_extract_variables_with_numbers(self):
        """Digits in variable names are valid and extracted correctly."""
        content = "Hello {{user123}} and {{var_456}}!"
        variables = extract_variables(content)
        assert variables == ["user123", "var_456"]

    def test_extract_malformed_variables(self):
        """Malformed placeholders are not extracted; only well-formed ones are.

        Note:
            ``{{name and`` is malformed (missing closing braces) and is skipped.
            ``{{}}`` is malformed (no variable name) and is skipped.
            ``{{age}}`` is well-formed and is extracted.
        """
        content = "Hello {{name and {{age}} and {{}}"
        variables = extract_variables(content)
        assert variables == ["age"]

    def test_extract_variables_with_special_chars(self):
        """Special characters in surrounding content do not affect extraction."""
        content = "Hello {{name}}! How are you? {{age}} years old."
        variables = extract_variables(content)
        assert variables == ["name", "age"]

    def test_extract_variables_preserves_order(self):
        """Variables are extracted in order of appearance in the content."""
        content = "{{third}} {{first}} {{second}}"
        variables = extract_variables(content)
        assert variables == ["third", "first", "second"]

    def test_extract_variables_case_sensitive(self):
        """Variable names are case-sensitive; {{Name}} and {{name}} are distinct."""
        content = "{{Name}} and {{name}}"
        variables = extract_variables(content)
        assert variables == ["Name", "name"]

    def test_extract_variables_with_nested_braces(self):
        """Dot-separated paths inside braces are not matched by the word-character pattern.

        Note:
            ``{{user.profile.name}}`` is not extracted because dots are not word
            characters. Only simple ``{{word}}`` patterns are matched.
        """
        content = "Hello {{name}} and {{user.profile.name}}"
        variables = extract_variables(content)
        assert variables == ["name"]

    def test_extract_variables_with_dashes(self):
        """Variables containing dashes are not extracted; only word characters are allowed.

        Note:
            ``{{user-name}}`` is not matched because dashes are not word characters.
            ``{{user_name}}`` is matched because underscores are word characters.
        """
        content = "Hello {{user-name}} and {{user_name}}"
        variables = extract_variables(content)
        assert variables == ["user_name"]

    def test_extract_variables_with_dots(self):
        """Variables containing dots are not extracted; only word characters are allowed.

        Note:
            ``{{user.name}}`` is not matched because dots are not word characters.
        """
        content = "Hello {{user.name}} and {{user_name}}"
        variables = extract_variables(content)
        assert variables == ["user_name"]

    def test_extract_variables_with_backticks(self):
        """Backtick-delimited content around placeholders does not affect extraction."""
        content = "Hello `{{name}}` and {{age}}"
        variables = extract_variables(content)
        assert variables == ["name", "age"]

    def test_extract_variables_with_html_tags(self):
        """HTML tags surrounding placeholders do not affect extraction."""
        content = "<p>Hello {{name}}</p> and <div>{{age}}</div>"
        variables = extract_variables(content)
        assert variables == ["name", "age"]

    def test_extract_variables_with_mixed_content(self):
        """Extraction works correctly in realistic multi-line HTML template content."""
        content = """
        <p>Hello {{user_name}}!</p>
        <div>You are {{age}} years old.</div>
        <span>Your score is {{score}}</span>
        """
        variables = extract_variables(content)
        assert variables == ["user_name", "age", "score"]

    def test_extract_variables_edge_cases(self):
        """Leading underscores, digit-prefixed names, and uppercase names are all valid."""
        content = "{{_private}} {{123number}} {{UPPERCASE}}"
        variables = extract_variables(content)
        assert variables == ["_private", "123number", "UPPERCASE"]

    def test_extract_variables_with_malformed_braces(self):
        """Only properly formed {{word}} patterns are extracted from content with mixed brace styles."""
        content = "{{name and {{age}} and {{}} and {name}"
        variables = extract_variables(content)
        assert variables == ["age"]

    def test_extract_variables_with_empty_braces(self):
        """Empty braces {{}} are not extracted; adjacent well-formed patterns still are."""
        content = "{{}} and {{name}}"
        variables = extract_variables(content)
        assert variables == ["name"]

    def test_extract_variables_at_start_and_end(self):
        """Placeholders at the very start and end of content are extracted correctly."""
        content = "{{start}} some text {{end}}"
        variables = extract_variables(content)
        assert variables == ["start", "end"]

    def test_extract_variables_with_many_repeats(self):
        """1000 repeated occurrences of a placeholder are each extracted individually."""
        content = "{{var}} " * 1000
        variables = extract_variables(content)
        assert len(variables) == 1000
        assert all(v == "var" for v in variables)

    def test_extract_variables_with_very_long_content(self):
        """Extraction works correctly in very long content strings."""
        long_content = "{{var1}} " + "a" * 10000 + " {{var2}}"
        variables = extract_variables(long_content)
        assert variables == ["var1", "var2"]

    def test_extract_variables_with_unicode_in_names(self):
        """Unicode word characters in variable names are extracted correctly.

        Note:
            Python's ``\\w`` in regex matches unicode word characters by default,
            so accented letters like ``é`` and ``ï`` are valid in variable names.
        """
        content = "{{café}} and {{naïve}}"
        variables = extract_variables(content)
        assert variables == ["café", "naïve"]

    def test_extract_variables_with_different_whitespace(self):
        """Whitespace surrounding placeholders does not affect extraction."""
        content = "  {{name}}  \t  {{age}}  \n  "
        variables = extract_variables(content)
        assert variables == ["name", "age"]

class TestIntegration:
    """Integration tests for utility functions working together."""

    def test_integration_sort_filter_search(self):
        """Chaining filter, search, and sort produces correctly ordered, filtered results."""
        from datetime import timezone
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        prompts = [
            Prompt(title="Python tutorial", content="content", created_at=now - timedelta(days=3), collection_id="col1", description="Python programming"),
            Prompt(title="JavaScript guide", content="content", created_at=now - timedelta(days=1), collection_id="col2", description="JavaScript programming"),
            Prompt(title="Python advanced", content="content", created_at=now, collection_id="col1", description="Advanced Python topics"),
            Prompt(title="Other topic", content="content", created_at=now - timedelta(days=2), collection_id="col1", description="Something else"),
        ]

        filtered = filter_prompts_by_collection(prompts, "col1")
        searched = search_prompts(filtered, "python")
        sorted_results = sort_prompts_by_date(searched, descending=True)

        assert len(sorted_results) == 2
        assert sorted_results[0].title == "Python advanced"
        assert sorted_results[1].title == "Python tutorial"

    def test_integration_validate_and_extract(self):
        """validate_prompt_content and extract_variables both work correctly on the same input."""
        content = "   Hello {{name}}, you are {{age}} years old!   "
        is_valid = validate_prompt_content(content)
        variables = extract_variables(content)

        assert is_valid == True
        assert variables == ["name", "age"]

    def test_edge_case_empty_string_vs_none(self):
        """Empty string and None are each handled correctly by validate and extract."""
        assert validate_prompt_content("") == False
        assert validate_prompt_content(None) == False

        assert extract_variables("") == []
        assert extract_variables(None) == []


class TestFuzzySearchEdgeCases:
    """Edge cases for the fuzzy search scoring and single-character query logic.

    Note:
        Fuzzy search uses the fuzzysearch library. A match is included only when
        its score is >= 30. The score formula is:
            score = 100 * field_weight - (start * 2) - (dist * 5)
        where field_weight=2 for title and field_weight=1 for description,
        start is the character offset of the match, and dist is the edit distance.

        For single-character queries, max_dist=0 is enforced, meaning only exact
        character matches are considered (no fuzzy tolerance).

        A whitespace-only or empty query bypasses all matching logic and returns
        the full input list unchanged.
    """

    def test_fuzzy_single_char_no_match_returns_empty(self):
        """A single-char fuzzy query returns empty when the character is absent from all prompts."""
        prompts = [Prompt(title="xyz", content="xyz")]
        results = search_prompts(prompts, "a", fuzzy=True)
        assert results == []

    def test_fuzzy_single_char_exact_match_returns_result(self):
        """A single-char fuzzy query finds prompts whose title contains that exact character."""
        prompts = [
            Prompt(title="alpha", content="content"),
            Prompt(title="xyz", content="xyz"),
        ]
        results = search_prompts(prompts, "a", fuzzy=True)
        assert len(results) == 1
        assert results[0].title == "alpha"

    def test_fuzzy_results_sorted_best_match_first(self):
        """Fuzzy results rank earlier matches (lower start index) before later ones.

        Note:
            A match at position 0 scores higher than the same match further into
            the string because the score formula subtracts start * 2 from the base.
        """
        prompts = [
            Prompt(title="a very long title string where the word match appears near the end", content="c"),
            Prompt(title="match is the very first word", content="c"),
        ]
        results = search_prompts(prompts, "match", fuzzy=True)
        assert len(results) >= 1
        if len(results) == 2:
            assert results[0].title == "match is the very first word"

    def test_exact_search_title_match_sufficient_for_inclusion(self):
        """Exact search includes a prompt when its title matches, regardless of description."""
        prompts = [
            Prompt(title="Python Guide", content="content", description="Unrelated topic"),
        ]
        results = search_prompts(prompts, "python", fuzzy=False)
        assert len(results) == 1

    def test_exact_search_no_match_returns_empty(self):
        """Exact search returns an empty list when the query is absent from all fields."""
        prompts = [
            Prompt(title="JavaScript Guide", content="js content", description="About JS"),
        ]
        results = search_prompts(prompts, "python", fuzzy=False)
        assert results == []

    def test_exact_search_is_case_insensitive(self):
        """Exact search matches regardless of case differences."""
        prompts = [Prompt(title="PYTHON Guide", content="content")]
        results = search_prompts(prompts, "python", fuzzy=False)
        assert len(results) == 1

    def test_whitespace_only_query_returns_all_prompts(self):
        """A whitespace-only query string returns all prompts unchanged."""
        prompts = [
            Prompt(title="Prompt A", content="content"),
            Prompt(title="Prompt B", content="content"),
        ]
        results = search_prompts(prompts, "   ", fuzzy=False)
        assert len(results) == 2

    def test_tab_only_query_returns_all_prompts(self):
        """A tab-only query string returns all prompts unchanged."""
        prompts = [
            Prompt(title="Prompt A", content="content"),
            Prompt(title="Prompt B", content="content"),
        ]
        results = search_prompts(prompts, "\t", fuzzy=False)
        assert len(results) == 2

    def test_validate_prompt_content_9_chars_fails(self):
        """validate_prompt_content returns False for 9 stripped chars and True for 10."""
        assert validate_prompt_content("123456789") == False
        assert validate_prompt_content("1234567890") == True

    def test_validate_prompt_content_9_chars_with_surrounding_whitespace(self):
        """Surrounding whitespace is stripped before the length check; 9 stripped chars fails."""
        assert validate_prompt_content("  123456789  ") == False

    def test_search_field_tags_returns_only_matching_prompts(self):
        """search_field='tags' filters on the tags list, not on title or description."""
        prompts = [
            Prompt(title="Python Tutorial", content="c", tags=["python", "coding"]),
            Prompt(title="JavaScript", content="c", tags=["javascript", "frontend"]),
        ]
        results = search_prompts(prompts, "python", fuzzy=False, search_field="tags")
        assert len(results) == 1
        assert "python" in results[0].tags

    def test_exact_search_description_only_match(self):
        """Exact search must return a prompt matched only via description (utils.py line 89).

        The query must not appear in title or content so that only the description
        branch is hit during non-fuzzy search.
        """
        prompts = [
            Prompt(title="Alpha Title", content="alpha content", description="unique-desc-term"),
            Prompt(title="Beta Title", content="beta content", description=None),
        ]
        results = search_prompts(prompts, "unique-desc-term", fuzzy=False, search_field="all")
        assert len(results) == 1
        assert results[0].description == "unique-desc-term"


if __name__ == "__main__":
    pytest.main()
