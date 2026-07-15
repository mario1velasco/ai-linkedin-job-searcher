# `app_be` architecture

This document explains **how code is meant to flow through this backend** and what goes in each folder. It's written so both a junior developer and an AI generating code here can understand it: if you're unsure where something new belongs, the answer is in this file.

## The flow: `main` → `service` → `api_client`

```
main.py  ──▶  services/  ──▶  api_clients/  ──▶  external provider (Stripe, LinkedIn, OpenAI...)
(routes)      (business         (HTTP calls to
               logic)            external APIs)
```

Each layer has **a single responsibility** and may only call the layer directly below it:

| Layer | Folder | Responsibility | What it does NOT do |
|---|---|---|---|
| **Entry** | `main.py` | Defines endpoints (`@app.get`, `@app.post`...), validates the request with Pydantic, calls the matching service, and translates the result into an HTTP response (status codes, etc.) | Contains no business logic and knows nothing about the external provider |
| **Business** | `services/` | Orchestrates the feature: what to do, in what order, how to combine data from one or more `api_clients`, which rules to apply | Doesn't speak HTTP (that's `main.py`'s job) and doesn't know the external API's details (that's `api_clients`' job) |
| **Integration** | `api_clients/` | Knows how to talk to **one** specific external provider: builds the request, authenticates, parses the response | Doesn't decide *when* or *why* it gets called — the service decides that |

### Example: a payment endpoint

```
POST /pay
  └─▶ main.py: receives the request, validates the data
        └─▶ services/payment_service.py: decides what to do (compute amount, apply discounts...)
              └─▶ api_clients/stripe_client.py: calls the Stripe API
```

If we switch payment providers tomorrow, **we only touch `api_clients/stripe_client.py`** (or replace it with `api_clients/new_provider_client.py`). `main.py` and `services/payment_service.py` don't change, because they don't know or care which provider is behind it.

### Worked example in this codebase: LinkedIn job search

```
GET /linkedin/jobs
  └─▶ main.py: parses query params, turns a RuntimeError into a 502
        └─▶ services/linkedin_service.py: runs the search, writes the results to data/linkedin_data.json
              └─▶ api_clients/linkedin_client.py: builds the Voyager request, authenticates with session cookies
```

Every LinkedIn endpoint in `main.py` (`/linkedin/login`, `/callback`, `/linkedin/userinfo`, `/linkedin/jobs`) calls `services/linkedin_service.py`, never `api_clients/linkedin_client.py` directly — this is the reference to copy for new features.

### Practical rule when adding new code

- Is it a new HTTP route? → add it in `main.py`, but have it only call a service.
- Is it business logic ("what to do with the data")? → goes in `services/`.
- Is it a call to a specific external API (LinkedIn, OpenAI, Stripe...)? → goes in `api_clients/`.
- Client modules are named `<provider>_client.py` (e.g. `linkedin_client.py`, `stripe_client.py`).
- If a function in `services/` needs another external provider, create/use another module inside `api_clients/` — don't put third-party HTTP calls directly in `services/` or `main.py`.

## The rest of the folders

| Folder / file | What it's for |
|---|---|
| `config.py` | The only place that reads environment variables (via `dotenv`, from the `.env` file at the repo root). Everything else **imports** the variables from here — never call `os.getenv(...)` outside this file. |
| `scripts/` | One-off tasks that aren't endpoints: scripts run by hand, cron jobs, one-time migrations, etc. |
| `utils/` | Reusable, cross-cutting code that doesn't belong to any single layer (e.g. `logger.py`). Any layer (`main`, `services`, `api_clients`) can import from `utils/`. |
| `data/` | Runtime-generated output (e.g. `linkedin_data.json`). It's in `.gitignore` and never committed. |

## Summary for an AI generating code in this repo

1. Never call `requests`/third-party SDKs from `main.py` or `services/` — that lives in `api_clients/`.
2. Never put business logic in `main.py` — only request parsing/validation and HTTP responses.
3. Never read environment variables with `os.getenv` outside `config.py` — import them from there.
4. When adding a client for a new provider, name the file `<provider>_client.py` and wire it up through a `services/<provider>_service.py`, not directly from `main.py`.
