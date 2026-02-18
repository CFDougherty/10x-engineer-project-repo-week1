---
name: Docstring Prompt
description: Adds or replaces a Google-style docstring for a selected Python function
invokable: true
---

Add a Google-style docstring to the selected Python function.

Rules:
- Modify ONLY the function’s docstring.
- Do NOT change logic, formatting, spacing, decorators, or code structure.
- Do NOT rename variables or alter the function signature.
- Preserve all existing type hints exactly as written.
- Do NOT introduce new imports.
- Do NOT wrap or reformat code outside the docstring.
- If a docstring already exists, fully replace it.

Type Handling:
- If type hints are present, do NOT repeat types in the Args or Returns sections.
- If type hints are absent, infer parameter or return types only when unambiguous.
- If the return value is unclear, omit the Returns section.

Docstring Structure (Google style):
- One-line summary in imperative mood (no period).
- Blank line after summary.
- Optional extended description only if needed for clarity (concise).
- Args:
    - List parameters in signature order.
    - Omit `self` and `cls` descriptions unless meaningful.
- Returns:
    - Include only if the function returns a value other than None.
- Raises:
    - Include only for explicitly raised exceptions in the function body.

Quality Guidelines:
- Be precise and concrete.
- Avoid restating obvious parameter names.
- Do not describe implementation details.
- Keep descriptions concise.

Output only the complete updated function definition.
