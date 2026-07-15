---
paths: ["apps/app-be/tests/**/*.py", "apps/app-be/src/app_be/**/*.py"]
---

# app-be testing

- Test files: `tests/test_*.py`, test functions `test_*`, plain `assert` (no matcher library).
- Endpoint tests use FastAPI's `TestClient` in-process (see `tests/test_main.py`) — no real server/socket needed.
- Shared fixtures go in `tests/conftest.py`, auto-discovered by pytest.
- Run via `npx nx run app-be:test` (wraps `uv run pytest tests/`).
- Coverage/junit output (`coverage/apps/app-be/`, `reports/apps/app-be/`) is regenerated on every run — never hand-edit it.
