"""Tests for app/embeddings.py — local embedding generation.

Uses mocks to avoid loading the actual sentence-transformers model during testing.
The global _model is reset before each test so the lazy-load path is exercisable.
"""

from __future__ import annotations

import sys
import asyncio
import pytest
from unittest.mock import MagicMock, patch
import app.embeddings as embeddings_module
from app.embeddings import (
    _get_model,
    generate_embedding,
    generate_query_embedding,
    generate_embeddings_batch,
    agenerate_embedding,
    agenerate_query_embedding,
)


@pytest.fixture(autouse=True)
def reset_model():
    """Reset the cached model before and after each test."""
    original = embeddings_module._model
    embeddings_module._model = None
    yield
    embeddings_module._model = original


def _make_mock_model(return_value=None):
    """Create a mock SentenceTransformer that returns a list from encode()."""
    mock = MagicMock()
    if return_value is None:
        return_value = [0.1] * 384
    # encode() returns something with .tolist()
    encode_result = MagicMock()
    encode_result.tolist.return_value = return_value
    mock.encode.return_value = encode_result
    return mock


def _patch_sentence_transformers(mock_model):
    """Return a context manager that injects a fake sentence_transformers module."""
    mock_module = MagicMock()
    mock_module.SentenceTransformer = MagicMock(return_value=mock_model)
    return patch.dict(sys.modules, {"sentence_transformers": mock_module})


class TestGetModel:
    def test_get_model_loads_on_first_call(self):
        """_get_model() must load SentenceTransformer when _model is None."""
        mock_model = _make_mock_model()
        with _patch_sentence_transformers(mock_model):
            result = _get_model()
            mock_ctor = sys.modules["sentence_transformers"].SentenceTransformer
            mock_ctor.assert_called_once_with("all-MiniLM-L6-v2")
            assert result is mock_model
            assert embeddings_module._model is mock_model

    def test_get_model_cached_on_second_call(self):
        """_get_model() must return the cached model without reloading."""
        mock_model = _make_mock_model()
        with _patch_sentence_transformers(mock_model):
            first = _get_model()
            second = _get_model()
            assert first is second
            mock_ctor = sys.modules["sentence_transformers"].SentenceTransformer
            mock_ctor.assert_called_once()  # constructor only called once

    def test_get_model_returns_existing_model(self):
        """_get_model() must return the pre-cached model without touching SentenceTransformer."""
        existing = _make_mock_model()
        embeddings_module._model = existing
        # Model already cached — SentenceTransformer constructor must NOT be called
        with _patch_sentence_transformers(MagicMock()):
            result = _get_model()
            mock_ctor = sys.modules["sentence_transformers"].SentenceTransformer
            mock_ctor.assert_not_called()
        assert result is existing


class TestGenerateEmbedding:
    def test_without_description(self):
        """generate_embedding with description=None joins title twice + content."""
        vec = [0.1] * 384
        mock_model = _make_mock_model(vec)
        embeddings_module._model = mock_model

        result = generate_embedding("My Title", "My Content")

        assert result == vec
        encode_call_args = mock_model.encode.call_args
        text_arg = encode_call_args[0][0]
        assert text_arg == "My Title\nMy Title\nMy Content"
        assert encode_call_args[1]["normalize_embeddings"] is True

    def test_with_description(self):
        """generate_embedding with description includes it between titles and content."""
        vec = [0.2] * 384
        mock_model = _make_mock_model(vec)
        embeddings_module._model = mock_model

        result = generate_embedding("Title", "Content", description="Desc")

        assert result == vec
        text_arg = mock_model.encode.call_args[0][0]
        assert text_arg == "Title\nTitle\nDesc\nContent"

    def test_empty_description_treated_as_absent(self):
        """generate_embedding with description='' omits it (falsy string)."""
        mock_model = _make_mock_model()
        embeddings_module._model = mock_model

        generate_embedding("Title", "Content", description="")

        text_arg = mock_model.encode.call_args[0][0]
        assert text_arg == "Title\nTitle\nContent"


class TestGenerateQueryEmbedding:
    def test_encodes_query_directly(self):
        """generate_query_embedding encodes the query string without composition."""
        vec = [0.3] * 384
        mock_model = _make_mock_model(vec)
        embeddings_module._model = mock_model

        result = generate_query_embedding("search term")

        assert result == vec
        mock_model.encode.assert_called_once_with("search term", normalize_embeddings=True)


class TestGenerateEmbeddingsBatch:
    def test_batch_with_descriptions(self):
        """generate_embeddings_batch encodes all items in a single call."""
        vecs = [[float(i)] * 384 for i in range(2)]
        mock_model = _make_mock_model(vecs)
        embeddings_module._model = mock_model

        items = [
            ("Title1", "Content1", "Desc1"),
            ("Title2", "Content2", "Desc2"),
        ]
        result = generate_embeddings_batch(items)

        assert result == vecs
        encode_call = mock_model.encode.call_args
        texts = encode_call[0][0]
        assert texts[0] == "Title1\nTitle1\nDesc1\nContent1"
        assert texts[1] == "Title2\nTitle2\nDesc2\nContent2"
        assert encode_call[1]["normalize_embeddings"] is True

    def test_batch_without_description(self):
        """generate_embeddings_batch with None description omits it from text."""
        vecs = [[0.1] * 384]
        mock_model = _make_mock_model(vecs)
        embeddings_module._model = mock_model

        items = [("Title", "Content", None)]
        generate_embeddings_batch(items)

        texts = mock_model.encode.call_args[0][0]
        assert texts[0] == "Title\nTitle\nContent"

    def test_batch_custom_batch_size(self):
        """generate_embeddings_batch passes batch_size to model.encode."""
        vecs = [[0.1] * 384]
        mock_model = _make_mock_model(vecs)
        embeddings_module._model = mock_model

        items = [("T", "C", None)]
        generate_embeddings_batch(items, batch_size=32)

        assert mock_model.encode.call_args[1]["batch_size"] == 32


class TestAsyncWrappers:
    @pytest.mark.asyncio
    async def test_agenerate_embedding_returns_same_as_sync(self):
        """agenerate_embedding wraps generate_embedding and returns its result."""
        vec = [0.5] * 384
        mock_model = _make_mock_model(vec)
        embeddings_module._model = mock_model

        result = await agenerate_embedding("Title", "Content", "Desc")
        assert result == vec

    @pytest.mark.asyncio
    async def test_agenerate_embedding_without_description(self):
        """agenerate_embedding passes None description correctly."""
        vec = [0.6] * 384
        mock_model = _make_mock_model(vec)
        embeddings_module._model = mock_model

        result = await agenerate_embedding("Title", "Content")
        assert result == vec
        text_arg = mock_model.encode.call_args[0][0]
        assert text_arg == "Title\nTitle\nContent"

    @pytest.mark.asyncio
    async def test_agenerate_query_embedding_returns_same_as_sync(self):
        """agenerate_query_embedding wraps generate_query_embedding and returns its result."""
        vec = [0.7] * 384
        mock_model = _make_mock_model(vec)
        embeddings_module._model = mock_model

        result = await agenerate_query_embedding("my query")
        assert result == vec
        mock_model.encode.assert_called_once_with("my query", normalize_embeddings=True)
