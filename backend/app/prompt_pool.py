"""Loads a HuggingFace dataset as a reusable pool for realistic prompt content.

The pool is lazily loaded on first access and cached as a module-level singleton.
The `datasets` library caches downloads in ~/.cache/huggingface/datasets/ so
subsequent starts are instant.
"""

import random
import threading

_DATASET_NAME = "databricks/databricks-dolly-15k"
_DATASET_SPLIT = "train"

_pool_instance: "PromptPool | None" = None
_pool_lock = threading.Lock()


def _format_content(record: dict) -> str:
    """Build prompt content from a dolly dataset record."""
    parts = [record["instruction"]]
    if record.get("context", "").strip():
        parts.append(record["context"].strip())
    if record.get("response", "").strip():
        parts.append(record["response"].strip())
    return "\n\n".join(parts)


def _truncate_title(text: str, max_len: int = 200) -> str:
    """Take the first sentence (or first max_len chars) of text as a title."""
    for sep in (".", "?", "!"):
        idx = text.find(sep)
        if 0 < idx < max_len:
            return text[: idx + 1].strip()
    return text[:max_len].strip()


class PromptPool:
    """Wraps a downloaded HuggingFace dataset as a sampling source."""

    def __init__(self, dataset_name: str = _DATASET_NAME, split: str = _DATASET_SPLIT):
        self._dataset_name = dataset_name
        self._split = split
        self._records: list[dict] | None = None

    def _load(self) -> None:
        from datasets import load_dataset  # deferred so import cost is paid only when used

        ds = load_dataset(self._dataset_name, split=self._split)
        self._records = [
            {
                "title": _truncate_title(r["instruction"]),
                "content": _format_content(r),
                "category": r.get("category", ""),
            }
            for r in ds
        ]

    def _ensure_loaded(self) -> None:
        if self._records is None:
            self._load()

    def sample(self, rng: random.Random, n: int) -> list[dict]:
        """Return n records. Samples without replacement up to pool size, then with replacement."""
        self._ensure_loaded()
        assert self._records is not None
        pool_size = len(self._records)
        if n <= pool_size:
            return rng.sample(self._records, n)
        # need more than we have — sample the full pool once, then fill the rest randomly
        result = list(self._records)
        rng.shuffle(result)
        while len(result) < n:
            result.append(rng.choice(self._records))
        return result[:n]

    @property
    def size(self) -> int:
        self._ensure_loaded()
        assert self._records is not None
        return len(self._records)


def get_pool() -> PromptPool:
    """Return the module-level singleton PromptPool, creating it if needed."""
    global _pool_instance
    if _pool_instance is None:
        with _pool_lock:
            if _pool_instance is None:
                _pool_instance = PromptPool()
    return _pool_instance
