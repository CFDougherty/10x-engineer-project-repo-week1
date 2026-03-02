"""Local embedding generation using sentence-transformers/all-MiniLM-L6-v2 (384 dims).

Model is loaded lazily on first call and cached for the process lifetime.
CPU-bound encoding is offloaded to a thread pool to avoid blocking the async event loop.
"""
from __future__ import annotations

import asyncio
import logging
import threading
from typing import List, Optional

logger = logging.getLogger(__name__)

_model = None
_model_lock = threading.Lock()
_MODEL_NAME = "all-MiniLM-L6-v2"


def _get_model():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer
                logger.info("Loading embedding model: %s", _MODEL_NAME)
                _model = SentenceTransformer(_MODEL_NAME)
                logger.info("Embedding model loaded.")
    return _model


def generate_embedding(title: str, content: str, description: Optional[str] = None) -> List[float]:
    """Generate a 384-dim embedding for storing with a prompt (document encoding).

    Title is repeated to increase its semantic weight relative to long content.
    Order: title, title, description, content — survives the 256-token truncation window.
    """
    model = _get_model()
    parts = [title, title]
    if description:
        parts.append(description)
    parts.append(content)
    text = "\n".join(parts)
    return model.encode(text, normalize_embeddings=True).tolist()


def generate_query_embedding(query: str) -> List[float]:
    """Generate a 384-dim embedding for a search query (raw text, no composition)."""
    model = _get_model()
    return model.encode(query, normalize_embeddings=True).tolist()


async def agenerate_embedding(title: str, content: str, description: Optional[str] = None) -> List[float]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, generate_embedding, title, content, description)


async def agenerate_query_embedding(query: str) -> List[float]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, generate_query_embedding, query)
