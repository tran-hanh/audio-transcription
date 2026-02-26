# Contributing to Long Audio Transcription Tool

This document defines development standards for this project. All code changes and new features must follow these practices.

## 1. Clean Code Principles

All code must be **easy to maintain and understand**:

- **Meaningful names**: Variables, functions, classes, and modules have clear, descriptive names. Avoid abbreviations unless widely known.
- **Small, focused units**: Functions and methods do one thing; keep them short. Prefer small files and clear module boundaries.
- **No duplication**: Extract common logic; follow DRY. Reuse from `src/` and `backend/` instead of copying.
- **Clear structure**: Use the existing layout—`src/` for core logic, `backend/` for API and services, `frontend/` for UI. Respect separation of concerns (e.g. domain, services, routes).
- **Readable over clever**: Prefer simple, explicit code. Add brief comments only where intent or non-obvious behavior needs explanation.
- **Consistent style**: Follow existing patterns and style in the codebase (e.g. type hints where used, error handling style, logging).

## 2. Test-Driven Development (TDD) and Test Coverage

Whenever you **update code** or **add new features**, you must add or update tests and follow TDD where applicable:

- **TDD practice**: Write or update tests first (or in tight loops: red → green → refactor). Tests define expected behavior; code satisfies them.
- **Test levels**:
  - **Unit tests**: For pure logic, utilities, validators, domain, and service/API logic in isolation (mocks for external calls). Location: `tests/` (e.g. `test_*.py`). Run with `pytest tests/ -v`.
  - **Integration tests**: For components working together (e.g. backend + `src` transcription flow, API + services). Use real or test doubles as defined in the test suite.
  - **E2E tests**: For critical user flows (e.g. upload → transcribe → download). Add or extend E2E when adding or changing user-facing features. Use the project’s chosen E2E framework and document in `tests/README.md`.
- **Coverage**: New or changed code should be covered by tests. Maintain or improve existing coverage goals (e.g. backend API and core logic as in `tests/README.md`). Run coverage locally: `pytest tests/ --cov=...` as documented.
- **CI**: All tests must pass in CI. Do not merge if tests are failing or if new behavior is untested.

## 3. Documentation Updates

Whenever you **update code** or **add new features**, update **all relevant documentation**:

- **README.md**: Update setup, usage, configuration, deployment, or feature list if anything changed. Keep examples and commands accurate.
- **tests/README.md**: Document new test files, how to run new test types (e.g. integration, E2E), and update coverage/CI notes if needed.
- **Docstrings and comments**: Update docstrings for changed or new public functions, classes, and modules. Keep comments in sync with behavior.
- **API or architecture docs**: If the project has additional docs (e.g. in `docs/` or architecture notes), update them when APIs, flows, or design change.
- **CHANGELOG or release notes**: If the project maintains a changelog, add an entry for user-visible or notable changes.

Consider documentation part of the same change set as code and tests; do not leave docs outdated.

## 4. Summary Checklist (per change/feature)

- [ ] Code follows clean code principles (names, size, structure, no unnecessary duplication).
- [ ] Tests added or updated: unit (and integration/E2E as relevant); TDD used where appropriate.
- [ ] All tests pass locally and in CI; coverage maintained or improved.
- [ ] README and other relevant docs updated (setup, usage, features, tests).
- [ ] Docstrings/comments updated for changed or new public APIs.

These standards apply to both human contributors and AI-assisted development (e.g. Cursor, BMAD workflows). The canonical reference is this file (`CONTRIBUTING.md`).
