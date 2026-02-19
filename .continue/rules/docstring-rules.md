---
description: Enforce consistent Google-style docstrings across all Python modules to meet Week 2 documentation standards.
alwaysApply: false
---

When @Docstring House Style (Manual) is referenced, enforce the following rules across all Python files (`models.py`, `api.py`, `storage.py`, `utils.py`):

1. **Placement**
   - The docstring must be the first statement inside a module, class, or function.
   - Do not use standalone triple-quoted comment blocks.
   - Use `#` comments for inline notes, or incorporate explanatory text into the module docstring.

2. **Structure**
   - Begin with a single-line summary in imperative mood ending with a period.
   - Follow with a blank line.
   - Include additional details only if necessary.

3. **Section Order**
   Use sections in this order when applicable:
   - `Args:`
   - `Returns:`
   - `Raises:`

4. **Type Handling**
   - If type hints are present, do not repeat types in `Args:` or `Returns:`.
   - Describe behavior, meaning, constraints, and edge cases instead.
   - If no parameters exist, omit the `Args:` section entirely (do not write `Args: None`).

5. **Formatting Conventions**
   - Use reStructuredText inline literals with double backticks (e.g., ``Prompt.created_at``).
   - Maintain consistent indentation, spacing, and blank lines throughout the file.
   - Do not modify function signatures, logic, or formatting outside the docstring.

6. **Scope**
   - Apply to all public and internal functions.
   - Ensure consistency with `docs/API_REFERENCE.md` where endpoints are documented.
