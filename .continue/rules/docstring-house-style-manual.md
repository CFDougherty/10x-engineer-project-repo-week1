---
description: Apply when you want to standardize/validate docstring formatting to
  a consistent Google-style convention across the codebase.
alwaysApply: false
---

When @Docstring House Style (Manual) is referenced, enforce consistent Google-style docstrings across Python files: (1) Docstrings must be the first statement in a module/class/function (no standalone triple-quoted comment blocks); use # comments or fold text into the module docstring instead. (2) Each docstring starts with a one-line summary ending with a period, followed by a blank line, then optional details. (3) Use sections in this order when applicable: Args:, Returns:, Raises:. (4) Omit types in Args/Returns when type hints exist; document meaning/constraints instead. (5) If there are no parameters, omit the Args: section (do not write 'Args: None'). (6) Use a single inline-code convention everywhere: reST literals with double backticks (e.g., ``Prompt.created_at``). (7) Keep formatting (indentation, spacing, blank lines) consistent throughout the file.