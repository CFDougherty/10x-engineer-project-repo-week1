"""Utility functions for PromptLab."""

from typing import List
from app.models import Prompt


def sort_prompts_by_date(prompts: List[Prompt], descending: bool = True) -> List[Prompt]:
    """Sorts a list of prompts by their creation timestamp.

    Prompts are ordered using the ``Prompt.created_at`` field (a ``datetime`` on
    the `Prompt` model). By default, the most recently created prompts appear
    first.

    Args:
        prompts: List of `Prompt` instances to sort.
        descending: If True (default), sorts newest-to-oldest. If False, sorts
            oldest-to-newest.

    Returns:
        A new list of `Prompt` instances sorted by ``created_at``.
    """
    return sorted(prompts, key=lambda p: p.created_at, reverse=descending)


def filter_prompts_by_collection(prompts: List[Prompt], collection_id: str) -> List[Prompt]:
    """Filters a list of prompts to those that belong to a specific collection.

    This function matches against the ``Prompt.collection_id`` field (defined on
    ``PromptBase`` / ``Prompt`` in ``app.models``). Prompts whose
    ``collection_id`` is ``None`` will not match and are therefore excluded.

    Args:
        prompts: List of ``Prompt`` instances to filter.
        collection_id: The collection identifier to match (typically
            ``Collection.id``).

    Returns:
        A new list of ``Prompt`` instances, preserving the input order, that have
        ``collection_id`` equal to the provided ``collection_id``.
    """
    return [p for p in prompts if p.collection_id == collection_id]


def search_prompts(prompts: List[Prompt], query: str) -> List[Prompt]:
    """Search prompts by a case-insensitive substring match on title/description.

    This helper scans the provided `prompts` and returns only those where `query`
    is contained in either `Prompt.title` or (if present) `Prompt.description`.
    Matching is case-insensitive and the relative order of matching prompts is
    preserved.

    Notes:
        - `Prompt.description` is optional (see `app.models.PromptBase`); prompts
          with `description=None` are still eligible to match by title.
        - An empty `query` will match all prompts because the empty string is a
          substring of any string.

    Args:
        prompts: List of `Prompt` instances to search.
        query: Search text to look for within each prompt's title and optional
            description.
    Returns:
        A list of `Prompt` instances whose title or description contains `query`
        (case-insensitive), in the same order as the input list.
    """
    query_lower = query.lower()
    return [
        p for p in prompts 
        if query_lower in p.title.lower() or 
           (p.description and query_lower in p.description.lower())
    ]


def validate_prompt_content(content: str) -> bool:
    """Validates that a prompt's content is non-empty and meets a minimum length.

    The input is considered valid if, after stripping leading/trailing
    whitespace, it is not empty and contains at least 10 characters.

    Args:
        content: The raw prompt text to validate.

    Returns:
        True if ``content`` is non-empty after trimming whitespace and its
        trimmed length is at least 10 characters; otherwise False.
    """
    # Check if prompt content is valid.
    #
    # A valid prompt should:
    # - Not be empty
    # - Not be just whitespace
    # - Be at least 10 characters
    if not content or not content.strip():
        return False
    return len(content.strip()) >= 10


def extract_variables(content: str) -> List[str]:
    """Extracts template variable names from prompt content.
    
    This function scans `content` for template variables written in the form
    ``{{variable_name}}`` and returns the variable names without the surrounding
    braces.

    Notes:
        - Variable names are matched using the regex ``r'\\{\\{(\\w+)\\}\\}'``, so
          they may contain letters, digits, and underscores (i.e., ``\\w``).
        - The returned list preserves the order of appearance in `content`.
        - If a variable appears multiple times, it will appear multiple times in
          the returned list.

    Args:
        content: The text to scan for template variables.

    Returns:
        A list of variable names found in `content` (without ``{{`` and ``}}``).
        If no variables are found, returns an empty list.
    """
    import re
    pattern = r'\{\{(\w+)\}\}'
    return re.findall(pattern, content)
