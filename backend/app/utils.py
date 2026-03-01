"""Utility functions for PromptLab."""

import re
from typing import List, Optional
from app.models import Prompt
from app.storage import storage
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

async def search_prompts(prompts: List[Prompt], query: str, fuzzy: bool = True, search_field: Optional[str] = None) -> List[Prompt]:
    """Search prompts by title, content, description, tags, and collection.

    Uses fuzzysearch for real-time search with good performance.

    Args:
        prompts: List of Prompt instances to search.
        query: Search text to look for within each prompt's fields.
        fuzzy: If True, uses fuzzy matching. If False, uses exact substring matching.
        search_field: Optional field to search in ('all', 'title', 'content', 'description', 'tags', 'collection').
            If None (default), searches all fields.

    Returns:
        A list of Prompt instances that match the query, sorted by match quality
        (if fuzzy search is enabled) or in the original order (if exact matching).
    """
    if not query or not query.strip():
        return prompts

    query_lower = query.lower().strip()

    # Determine which fields to search based on search_field parameter
    fields_to_search = []

    if search_field == 'title':
        fields_to_search = ['title']
    elif search_field == 'content':
        fields_to_search = ['content']
    elif search_field == 'description':
        fields_to_search = ['description']
    elif search_field == 'tags':
        fields_to_search = ['tags']
    elif search_field == 'collection':
        fields_to_search = ['collection']
    else:  # 'all' or None - search all fields
        fields_to_search = ['title', 'content', 'description', 'tags', 'collection']

    # Load collections once if needed — avoids a redundant storage call per prompt.
    needs_collection_lookup = 'collection' in fields_to_search
    all_collections = await storage.get_all_collections() if needs_collection_lookup else []

    if not fuzzy:
        # Exact substring matching
        results = []
        for p in prompts:
            match = False
            if 'title' in fields_to_search and query_lower in p.title.lower():
                match = True
            if not match and 'content' in fields_to_search and query_lower in p.content.lower():
                match = True
            if not match and 'description' in fields_to_search and p.description and query_lower in p.description.lower():
                match = True
            if not match and 'tags' in fields_to_search and p.tags and any(query_lower in tag.lower() for tag in p.tags):
                match = True
            if not match and 'collection' in fields_to_search and p.collection_id:
                if any(c.id == p.collection_id and query_lower in c.name.lower() for c in all_collections):
                    match = True
            if match:
                results.append(p)
        return results

    # Fuzzy search using fuzzysearch
    # For each prompt, check all searchable fields
    matches = []

    for p in prompts:
        fields_to_check = []

        if 'title' in fields_to_search:
            fields_to_check.append(('title', p.title.lower()))
        if 'content' in fields_to_search:
            fields_to_check.append(('content', p.content.lower()))
        if 'description' in fields_to_search and p.description:
            fields_to_check.append(('description', p.description.lower()))
        if 'tags' in fields_to_search and p.tags:
            fields_to_check.append(('tags', " ".join(p.tags).lower()))
        if 'collection' in fields_to_search and p.collection_id:
            collection_names = [c.name.lower() for c in all_collections if c.id == p.collection_id]
            if collection_names:
                fields_to_check.append(('collection', collection_names[0]))

        # Find matches in each field
        for field_name, field in fields_to_check:
            # Use a more strict distance threshold
            # For single-character queries, use max_dist=0 for exact match
            # For longer queries, use max_dist=half the query length
            query_len = len(query_lower)
            max_dist = 0 if query_len == 1 else max(1, query_len // 2)
            near_matches = find_near_matches(
                query_lower,
                field,
                max_l_dist=max_dist
            )

            if near_matches:
                # Only consider matches with reasonable distance
                # For single-character queries, distance should be 0 (exact match)
                # For longer queries, distance should be small relative to query length
                if query_len == 1:
                    # For single character, require exact match (distance 0)
                    good_matches = [m for m in near_matches if m.dist == 0]
                else:
                    # For longer queries, allow small distance
                    max_allowed_dist = min(2, query_len // 2)
                    good_matches = [m for m in near_matches if m.dist <= max_allowed_dist]

                if good_matches:
                    best_match = min(good_matches, key=lambda m: m.start)
                    # Score formula: base 100 per field weight, penalised by match position
                    # (start * 2) and edit distance (dist * 5).  Title matches get weight 2
                    # so they rank above body/tag/collection matches at equal distance.
                    # Matches scoring below 30 are considered too weak and are filtered out.
                    field_weight = 2.0 if field_name == 'title' else 1.0
                    score = 100 * field_weight - (best_match.start * 2) - (best_match.dist * 5)
                    # Ensure score doesn't go below 0
                    score = max(0, score)
                    matches.append((score, p))
                    break  # Stop after finding first match in the specified field

    # Sort by score (descending) to get best matches first
    matches.sort(reverse=True, key=lambda x: x[0])
    # Filter out very low-quality matches (score < 30)
    return [p for score, p in matches if score >= 30]

def validate_prompt_content(content: str) -> bool:
    """Validates that a prompt's content is non-empty and meets a minimum length.

    The input is considered valid if, after stripping leading/trailing
    whitespace, it is not empty and contains at least 10 characters.

    Note:
        This function is a standalone utility and is not called by the API layer,
        which relies solely on Pydantic model validation. It is available for
        use in scripts or future middleware.

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
    if content is None:
        return []
    pattern = r'\{\{(\w+)\}\}'
    return re.findall(pattern, content)
