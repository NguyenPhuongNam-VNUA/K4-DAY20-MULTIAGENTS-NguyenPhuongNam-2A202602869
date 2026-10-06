---
name: comprehensive-bug-fix-testing-and-changelog
description: WHEN fixing code bugs or implementing features that require regression tests and changelog entries.
---
## Bug Fix and Documentation Procedure
1. **Regression Tests**:
   - Create or update `tests/test_regressions.py`.
   - Add at least one distinct test function per bug fixed.
   - Run the full test suite (`pytest`) to ensure all tests pass successfully.
2. **Changelog Maintenance**:
   - Open `CHANGELOG.md`.
   - Locate or create the `## Unreleased` section heading.
   - Add a descriptive bullet point for each fix following the format: `- fix(<function name>): <short description>`.
