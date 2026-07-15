---
---

# Secrets and environment variables

- All env vars are read exactly once, in `apps/app-be/src/app_be/config.py`. Everywhere else must `import` from there — never call `os.getenv` directly.
- Root `.env` (gitignored) holds: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `CLIENT_ID`, `CLIENT_SECRET`, `REDIRECT_URI`, `LI_AT_COOKIE`, `JSESSIONID`, `FOUNDRY_API_KEY`. Never print, log, or commit these values.
- `config.py` raises `RuntimeError` at import time if any of these vars is missing — keep that list in sync if you add a new one.
