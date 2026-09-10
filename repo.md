# LocalGPT Repository Guide

## Required workflow for every code change

1. Read this file and `BACKLOG.md` before editing code.
2. Identify the relevant feature documentation and update it when behavior,
   architecture, or public APIs change.
3. Add or update unit tests for newly built behavior.
4. Run the complete unit test suite after the feature is implemented.
5. Append a dated entry to `changelog.md` describing the change and validation.
6. Keep changes focused and preserve existing behavior unless the backlog item
   explicitly requires a behavior change.

## Project conventions

- Backend code lives under `backend/`; the FastAPI application is created by
  `backend/main.py`.
- New HTTP routes belong in `backend/app/api/`.
- Business logic belongs in `backend/app/services/`.
- Shared request/response models and pure helpers belong in
  `backend/app/domain/`.
- Keep API handlers thin and avoid importing one API router from another.
- Use the existing Python virtual environment at `backend/.venv`.
- Prefer the existing `unittest` style; pytest is the test runner and must
  execute all `backend/test_*.py` files.
- Do not change dependency manifests unless a dependency is required by the
  implementation or test suite.

## Validation commands

```bash
backend/.venv/bin/python -m pytest -q
backend/.venv/bin/python -m compileall -q backend
```

## Documentation ownership

- `BACKLOG.md`: scope, acceptance criteria, and work-item status.
- `repo.md`: mandatory development and documentation workflow.
- `project.md`: current project state, architecture, and feature history.
- `changelog.md`: append-only record of repository changes and validation.
