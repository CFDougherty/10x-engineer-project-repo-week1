"""Utility functions for PromptLab."""

from typing import List, Tuple
from app.models import Prompt
from fuzzysearch import find_near_matches

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

    Uses fuzzysearch for real-time search with good performance.

    Args:
        prompts: List of Prompt instances to search.
        query: Search text to look for within each prompt's fields.
        fuzzy: If True, uses fuzzy matching. If False, uses exact substring matching.

    Returns:
        A list of Prompt instances that match the query, sorted by match quality
        (if fuzzy search is enabled) or in the original order (if exact matching).
    """
    if not query or not query.strip():
        return prompts

    query_lower = query.lower().strip()

    if not fuzzy:
        # Exact substring matching
        return [
            p for p in prompts
            if query_lower in p.title.lower() or
               query_lower in p.content.lower() or
               (p.description and query_lower in p.description.lower()) or
               (p.tags and any(query_lower in tag.lower() for tag in p.tags))
        ]

    # Fuzzy search using fuzzysearch
    # For each prompt, check all searchable fields
    matches = []

    for p in prompts:
        # Check each field individually for better matching
        fields_to_check = [
            p.title.lower(),
            p.content.lower(),
        ]
        if p.description:
            fields_to_check.append(p.description.lower())
        if p.tags:
            fields_to_check.append(" ".join(p.tags).lower())

        # Find matches in each field
        for field in fields_to_check:
            # Use a more strict distance threshold
            max_dist = max(1, len(query_lower) // 2)  # At most half the query length
            near_matches = find_near_matches(
                query_lower,
                field,
                max_l_dist=max_dist
            )

            if near_matches:
                # Only consider matches with reasonable distance
                # Distance should be less than or equal to 2 for good matches
                good_matches = [m for m in near_matches if m.dist <= 2]
                if good_matches:
                    best_match = min(good_matches, key=lambda m: m.start)
                    # Better scoring: prioritize earlier matches and shorter distance
                    # Title matches get a bonus to appear first
                    field_weight = 2.0 if field == p.title.lower() else 1.0
                    score = 100 * field_weight - (best_match.start * 2) - (best_match.dist * 5)
                    # Ensure score doesn't go below 0
                    score = max(0, score)
                    matches.append((score, p))
                    break  # Only use the best field match for this prompt

    # Sort by score (descending) to get best matches first
    matches.sort(reverse=True, key=lambda x: x[0])
    # Filter out very low-quality matches (score < 30)
    return [p for score, p in matches if score >= 30]

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