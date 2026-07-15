---
description: >
  Use when GET /linkedin/jobs (or any LinkedIn endpoint) returns a 502, or
  the user mentions LinkedIn cookies expiring, LI_AT_COOKIE, JSESSIONID, or
  "refresh LinkedIn auth". Walks through pulling fresh li_at/JSESSIONID
  cookie values from a logged-in browser session and updating them in the
  root .env file.
user-invocable: true
---

1. Confirm the failure looks like an auth issue (502, or a `RuntimeError` about expired cookies) coming from `services/linkedin_service.py` → `api_clients/linkedin_client.py` — not a code bug.
2. This step is manual and can't be automated: ask the user to log into linkedin.com in a browser, open DevTools → Application (or Storage) → Cookies → `https://www.linkedin.com`, and copy the current values of the `li_at` and `JSESSIONID` cookies.
3. Update the root `.env` file: `LI_AT_COOKIE=<li_at value>` and `JSESSIONID=<JSESSIONID value>`. `.env` is gitignored — never echo the actual cookie values into chat or logs.
4. Restart the server. `config.py` calls `load_dotenv()` at import time, so `uvicorn --reload`'s file-watch reload does **not** pick up new env values — stop the running process and re-run `npx nx run app-be:serve`.
5. Verify by calling `GET /linkedin/jobs?keywords=...` and confirming a 200 with job results instead of a 502.
6. Remember: `config.py`'s startup check raises `RuntimeError` if either var is blank — don't leave one unset.
