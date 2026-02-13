---
name: Docstring Prompt
description: Adds google docstring style comments to selected code
invokable: true
---

Add a Google-style docstring to the selected Python function.

Requirements:
- Only add or replace the function’s docstring.
- Do NOT modify logic, formatting, spacing, or code structure.
- Do NOT rename variables or change signatures.
- Preserve existing type hints.
- If type hints exist, do NOT repeat types in the Args section.
- If no type hints exist, infer parameter types only when obvious.

Docstring format:
- One-line summary in imperative mood.
- Blank line after summary.
- Args section listing all parameters in order.
- Returns section if the function returns a value.
- Raises section only if exceptions are explicitly raised.

Keep descriptions concise and precise.

Output only the updated function.