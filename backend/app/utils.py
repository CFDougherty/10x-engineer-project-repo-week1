"""Utility functions for PromptLab."""

from typing import List, Tuple
from app.models import Prompt
from rapidfuzz import fuzz, process

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

def search_prompts(prompts: List[Prompt], query: str, fuzzy: bool = True) -> List[Prompt]:
    """Search prompts by title, content, description, and tags.

    This helper scans the provided `prompts` and returns only those where `query`
    matches against the prompt's title, content, description, or tags.

    Args:
        prompts: List of `Prompt` instances to search.
        query: Search text to look for within each prompt's fields.
        fuzzy: If True (default), uses fuzzy string matching. If False, uses exact substring matching.

    Returns:
        A list of `Prompt` instances that match the query, sorted by relevance score
        (if fuzzy search is enabled) or in the original order (if exact matching).
    """
    if not query or not query.strip():
        return prompts

    query_lower = query.lower().strip()

    if not fuzzy:
        # Exact substring matching (original behavior)
        return [
            p for p in prompts
            if query_lower in p.title.lower() or
               query_lower in p.content.lower() or
               (p.description and query_lower in p.description.lower()) or
               (p.tags and any(query_lower in tag.lower() for tag in p.tags))
        ]

    # Fuzzy search using rapidfuzz
    # Combine all searchable fields into a single string for each prompt
    searchable_prompts = []
    for p in prompts:
        # Build a composite search string from all fields
        fields = [
            p.title,
            p.content,
        ]
        # Only add description if it's not None
        if p.description is not None:
            fields.append(p.description)
        # Only add tags if they exist
        if p.tags:
            fields.append(" ".join(p.tags))
        search_string = " ".join(fields).lower()
        searchable_prompts.append(search_string)

    # Use rapidfuzz to find best matches with scores
    # For very short queries (1-2 chars), use a lower cutoff to allow character matching
    # For short single-word queries (3-20 chars), use a higher cutoff to avoid false positives
    # For longer queries, use a lower cutoff to allow for more flexibility
    if len(query_lower) <= 2:
        # Very short query (1-2 characters) - allow character matching
        score_cutoff = 55
    elif len(query_lower.split()) == 1 and len(query_lower) < 20:
        # Single word query (3-20 chars) - be more strict
        score_cutoff = 65
    else:
        # Multi-word or longer query - be more lenient
        score_cutoff = 60

    results = process.extract(query_lower, searchable_prompts, scorer=fuzz.WRatio, score_cutoff=score_cutoff)

    # Create a dictionary mapping search strings to prompts for lookup
    search_string_to_prompt = {search_string: p for search_string, p in zip(searchable_prompts, prompts)}

    # Extract prompts in order of best match
    matched_prompts = []
    for match in results:
        search_string = match[0]
        if search_string in search_string_to_prompt:
            matched_prompts.append(search_string_to_prompt[search_string])

    return matched_prompts

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
    if content is None:
        return []
    pattern = r'\{\{(\w+)\}\}'
    return re.findall(pattern, content)