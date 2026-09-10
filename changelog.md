# Changelog

All notable repository changes are recorded here, newest first.

## 2026-09-11

### P1-S1 backend layering

- Added the layered `backend/app/` package and API routers.
- Reduced `backend/main.py` to application construction and router wiring.
- Added service and domain modules for the extracted route behavior.
- Added structural tests for the application factory and router layout.
- Installed pytest in `backend/.venv`.
- Fixed router score aggregation and converted the router smoke script into
  pytest-discoverable unit tests.
- Full test command: `backend/.venv/bin/python -m pytest -q`.
