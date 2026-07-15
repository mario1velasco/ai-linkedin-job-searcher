---
paths: ["apps/app-be/src/app_be/**/*.py"]
---

# app-be architecture

Flow: `main.py` (routes, request validation, HTTP responses only) → `services/` (business logic, orchestration) → `api_clients/` (one external provider each).

- Client files are named `<provider>_client.py` (e.g. `linkedin_client.py`).
- Never call `requests`/third-party SDKs from `main.py` or `services/` — that lives in `api_clients/`.
- Never put business logic in `main.py` — only request parsing/validation and HTTP responses.
- Reference implementation to copy: `services/linkedin_service.py` → `api_clients/linkedin_client.py`.

Full rationale and the "what goes where" table: `apps/app-be/src/app_be/README.md`.
