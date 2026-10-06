---
name: python-type-annotations
description: WHEN writing or updating Python functions in a package to ensure all public functions have full type annotations.
---
## Checklist for Type Annotations
1. Identify all public functions (names not starting with `_`).
2. Add type hints for every parameter (e.g., `item: dict`, `threshold: int`).
3. Add a return type hint to the function signature (e.g., `-> list`, `-> Decimal`).
4. Import required types from `typing` or `decimal` if needed.
5. Run a static type checker (e.g., `mypy`) or test suite to verify compliance.
