"""Tests for app/prompt_pool.py — HuggingFace dataset prompt pool.

Uses mocks to avoid downloading the actual dataset during testing.
"""

from __future__ import annotations

import sys
import random
import pytest
from unittest.mock import patch, MagicMock
import app.prompt_pool as pool_module
from app.prompt_pool import (
    _format_content,
    _truncate_title,
    PromptPool,
    get_pool,
)


@pytest.fixture(autouse=True)
def reset_pool_singleton():
    """Reset the module-level singleton before and after each test."""
    original = pool_module._pool_instance
    pool_module._pool_instance = None
    yield
    pool_module._pool_instance = original


def _mock_dataset(records: list[dict]):
    """Return a mock that load_dataset() will return."""
    mock_ds = MagicMock()
    mock_ds.__iter__ = MagicMock(return_value=iter(records))
    return mock_ds


SAMPLE_RECORDS = [
    {"instruction": "What is Python?", "context": "A programming language.", "response": "Python is great.", "category": "coding"},
    {"instruction": "Explain recursion", "context": "", "response": "Recursion is...", "category": "cs"},
    {"instruction": "Write a poem", "context": "About spring", "response": "Flowers bloom.", "category": "creative"},
    {"instruction": "No extras here", "context": "", "response": "", "category": ""},
    {"instruction": "Another prompt", "context": "Some context", "response": "", "category": "misc"},
]


class TestFormatContent:
    def test_instruction_only(self):
        """Records with empty context and response use only instruction."""
        record = {"instruction": "Do something", "context": "", "response": ""}
        result = _format_content(record)
        assert result == "Do something"

    def test_instruction_and_context(self):
        """Records with context include it after instruction."""
        record = {"instruction": "Do something", "context": "with care", "response": ""}
        result = _format_content(record)
        assert result == "Do something\n\nwith care"

    def test_instruction_and_response(self):
        """Records with response include it after instruction."""
        record = {"instruction": "Do something", "context": "", "response": "Done!"}
        result = _format_content(record)
        assert result == "Do something\n\nDone!"

    def test_all_fields(self):
        """Records with all fields include all three parts."""
        record = {"instruction": "Do something", "context": "with care", "response": "Done!"}
        result = _format_content(record)
        assert result == "Do something\n\nwith care\n\nDone!"

    def test_whitespace_only_context_excluded(self):
        """Whitespace-only context is treated as absent."""
        record = {"instruction": "Do something", "context": "   ", "response": ""}
        result = _format_content(record)
        assert result == "Do something"


class TestTruncateTitle:
    def test_period_before_max_len(self):
        """First sentence ending with period is used as title."""
        text = "Hello world. This is the rest."
        result = _truncate_title(text)
        assert result == "Hello world."

    def test_question_mark_before_max_len(self):
        """First sentence ending with ? is used as title (no prior period in text)."""
        # Must not contain a period so the '.' check falls through to '?'
        text = "What is Python? It is great"
        result = _truncate_title(text)
        assert result == "What is Python?"

    def test_exclamation_before_max_len(self):
        """First sentence ending with ! is used as title (no prior period or ? in text)."""
        # Must not contain '.' or '?' so both earlier checks fall through to '!'
        text = "Amazing! Nothing else here"
        result = _truncate_title(text)
        assert result == "Amazing!"

    def test_falls_back_to_max_len(self):
        """Text without sentence terminators is truncated at max_len."""
        text = "A" * 300  # No sentence terminator
        result = _truncate_title(text)
        assert len(result) == 200
        assert result == "A" * 200

    def test_separator_after_max_len_uses_truncation(self):
        """A period after max_len triggers the max_len fallback."""
        text = "A" * 201 + ". trailing"
        result = _truncate_title(text)
        assert len(result) <= 200

    def test_short_text_returned_as_is(self):
        """Short text with no sentence terminator is returned stripped."""
        text = "Short prompt"
        result = _truncate_title(text)
        assert result == "Short prompt"


class TestPromptPool:
    def _make_pool_with_records(self, records: list[dict]) -> PromptPool:
        """Create a PromptPool whose _load() uses mocked records."""
        pool = PromptPool.__new__(PromptPool)
        pool._dataset_name = "mock/dataset"
        pool._split = "train"
        pool._records = None

        mock_ds = _mock_dataset(records)
        mock_datasets_module = MagicMock()
        mock_datasets_module.load_dataset = MagicMock(return_value=mock_ds)
        with patch.dict(sys.modules, {"datasets": mock_datasets_module}):
            pool._load()
        return pool

    def test_load_builds_records(self):
        """_load() must build a record list from the dataset."""
        pool = self._make_pool_with_records(SAMPLE_RECORDS)
        assert pool._records is not None
        assert len(pool._records) == len(SAMPLE_RECORDS)

    def test_load_record_has_required_keys(self):
        """Each record built by _load() must have title, content, category, instruction."""
        pool = self._make_pool_with_records(SAMPLE_RECORDS[:1])
        r = pool._records[0]
        assert "title" in r
        assert "content" in r
        assert "category" in r
        assert "instruction" in r

    def test_size_property(self):
        """size property returns the number of loaded records."""
        pool = self._make_pool_with_records(SAMPLE_RECORDS)
        assert pool.size == len(SAMPLE_RECORDS)

    def test_sample_less_than_pool(self):
        """sample(n) with n < pool_size returns n unique records without replacement."""
        pool = self._make_pool_with_records(SAMPLE_RECORDS)
        rng = random.Random(42)
        result = pool.sample(rng, 3)
        assert len(result) == 3
        # All should be from original pool
        pool_titles = {r["title"] for r in pool._records}
        for r in result:
            assert r["title"] in pool_titles

    def test_sample_exact_pool_size(self):
        """sample(n) with n == pool_size returns all records (shuffled)."""
        pool = self._make_pool_with_records(SAMPLE_RECORDS)
        rng = random.Random(99)
        result = pool.sample(rng, len(SAMPLE_RECORDS))
        assert len(result) == len(SAMPLE_RECORDS)

    def test_sample_more_than_pool(self):
        """sample(n) with n > pool_size fills with replacement to reach n."""
        pool = self._make_pool_with_records(SAMPLE_RECORDS)  # 5 records
        rng = random.Random(7)
        result = pool.sample(rng, 10)
        assert len(result) == 10

    def test_ensure_loaded_calls_load_once(self):
        """_ensure_loaded() calls _load() only when _records is None."""
        pool = PromptPool.__new__(PromptPool)
        pool._dataset_name = "mock/dataset"
        pool._split = "train"
        pool._records = None

        mock_ds = _mock_dataset(SAMPLE_RECORDS[:2])
        mock_datasets_module = MagicMock()
        mock_datasets_module.load_dataset = MagicMock(return_value=mock_ds)
        with patch.dict(sys.modules, {"datasets": mock_datasets_module}):
            pool._ensure_loaded()
            pool._ensure_loaded()  # second call should not re-load
            mock_datasets_module.load_dataset.assert_called_once()


class TestGetPool:
    def test_get_pool_returns_prompt_pool_instance(self):
        """get_pool() must return a PromptPool."""
        result = get_pool()
        assert isinstance(result, PromptPool)

    def test_get_pool_singleton(self):
        """get_pool() must return the same instance on repeated calls."""
        first = get_pool()
        second = get_pool()
        assert first is second

    def test_get_pool_creates_new_when_reset(self):
        """get_pool() creates a fresh instance when the singleton is cleared."""
        pool_module._pool_instance = None
        result = get_pool()
        assert result is not None
        assert pool_module._pool_instance is result
