# app-be

A Python **FastAPI** backend managed inside this Nx monorepo using the [`@nxlv/python`](https://github.com/lucasvieirasilva/nx-plugins) Nx plugin and [`uv`](https://docs.astral.sh/uv/) as the Python package manager.

This README is written for someone new to Python — it explains the tools, where things live on disk, and how to run/write tests.

## Project structure

```
apps/app-be/
├── src/
│   └── app_be/            # your actual Python package (the code you write)
│       ├── __init__.py
│       ├── main.py        # FastAPI app + routes (the "entry" layer)
│       ├── services/      # business logic (the "what to do" layer)
│       ├── api_clients/   # calls to external providers, e.g. LinkedIn (the "how to talk to it" layer)
│       ├── config.py      # the only place that reads environment variables
│       ├── scripts/       # one-off tasks: cron jobs, manual scripts
│       ├── utils/         # reusable, cross-cutting code (e.g. logger.py)
│       └── README.md      # architecture rules for this package — read this before adding code
├── tests/                # pytest test files
│   ├── __init__.py
│   ├── conftest.py       # shared pytest fixtures/config for this project
│   └── test_main.py
├── pyproject.toml        # Python project config: deps, pytest, ruff, build
├── project.json          # Nx config: defines the `nx run app-be:<target>` commands
├── .python-version       # pins the Python version (3.11.15) for this project
└── uv.lock               # exact locked versions of every dependency (auto-generated, commit it)
```

`app_be` is the *importable* package name (Python identifiers can't contain hyphens), while `app-be` is the Nx project name you use in `nx` commands.

## Architecture: `main` → `services` → `api_clients`

Every feature in this backend flows through three layers, each with a single responsibility:

```
main.py  ──▶  services/  ──▶  api_clients/  ──▶  external provider (LinkedIn, OpenAI, Stripe...)
(routes)      (business        (HTTP calls to
               logic)           external APIs)
```

| Layer | Folder | Responsibility |
|---|---|---|
| Entry | `main.py` | Defines endpoints, validates the request (Pydantic), calls the matching service, turns the result into an HTTP response |
| Business | `services/` | Decides *what* to do and in what order; combines data from one or more `api_clients` |
| Integration | `api_clients/` | Knows how to talk to *one* external provider: builds the request, authenticates, parses the response |

The point of the split: if you swap providers (e.g. a different payment processor), you only touch the corresponding module in `api_clients/` — `main.py` and `services/` don't know or care which provider is behind the interface.

See [`src/app_be/README.md`](src/app_be/README.md) for the full rules on what goes in each layer (also meant to guide AI-generated code in this package). The LinkedIn endpoints below (`services/linkedin_service.py` → `api_clients/linkedin_client.py`) are the reference implementation of this pattern.

## 0. Running the API

```bash
npx nx run app-be:serve
```

This starts [`uvicorn`](https://www.uvicorn.org/) (an ASGI server — the Python equivalent of Node's HTTP server) with `--reload` enabled, serving on **http://localhost:8000**. Visit `http://localhost:8000/` and you'll get:

```json
{"message": "Hello World"}
```

`--reload` means the server watches `src/` for file changes and automatically restarts itself whenever you save — you never have to stop/start it manually while developing. It keeps running in your terminal until you press `Ctrl+C`.

FastAPI also gives you free interactive API docs while the server is running: **http://localhost:8000/docs**.

The route itself lives in [`src/app_be/main.py`](src/app_be/main.py):

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root() -> dict[str, str]:
    """Return a friendly greeting."""
    return {"message": "Hello World"}
```

To add a new endpoint, add another `@app.get(...)` (or `@app.post`, `@app.put`, ...) function in this file — FastAPI auto-discovers it as soon as the file is saved (thanks to `--reload`).

## 1. What is `uv`?

[`uv`](https://docs.astral.sh/uv/) is a fast, all-in-one tool that replaces `pip` + `venv` + `pip-tools` + more. Think of it as the Python equivalent of `npm`/`pnpm`: it manages a project's dependencies, a lockfile, and an isolated environment for you.

**You do not install packages manually.** You declare dependencies (or let a generator/`nx` command do it) and `uv` figures out and installs exact versions.

### Where is the virtual environment?

Every Python project needs an isolated place to install its dependencies without polluting your system Python — that's a **virtual environment** (a "venv"). For this project it lives at:

```
apps/app-be/.venv/
```

It's created automatically the first time you sync/install (see below), and it's git-ignored — never commit it. If you ever want to nuke it and rebuild from scratch, it's always safe to delete:

```bash
rm -rf apps/app-be/.venv
```

### Do I need to install `uv` myself?

It's already installed on this machine at `~/.local/bin/uv` (and on `PATH` via `~/.zshrc`). You don't need to reinstall it — just make sure a new shell/terminal picks up `~/.local/bin` on `PATH` (restart your terminal once if `uv --version` doesn't work).

### Key `uv` concepts

| Concept | File | Purpose |
|---|---|---|
| Dependencies | `pyproject.toml` → `[project.dependencies]` / `[dependency-groups]` | What your app needs (runtime vs dev-only, like `devDependencies` in `package.json`) |
| Lockfile | `uv.lock` | Exact resolved versions of everything — commit this, like `package-lock.json` |
| Virtual env | `.venv/` | Where packages actually get installed — never commit this |
| Python pin | `.python-version` | Which Python interpreter version this project targets |

You'll almost never call `uv` directly here — Nx wraps it (next section). But for reference, the raw commands are:

```bash
cd apps/app-be
uv sync              # install everything from uv.lock into .venv
uv add requests       # add a new runtime dependency (updates pyproject.toml + uv.lock)
uv add --dev mypy     # add a dev-only dependency
uv run pytest         # run a command inside the venv, without manually activating it
```

## 2. `@nxlv/python` — the Nx plugin

Nx doesn't understand Python natively, so [`@nxlv/python`](https://www.npmjs.com/package/@nxlv/python) bridges the two: it generates Python projects and exposes their common actions (install, test, lint, build...) as standard `nx run` **targets**, so Python projects feel consistent with any JS/Angular projects that get added to this workspace later.

### Where it's configured

- **Workspace-wide** in [`nx.json`](../../nx.json):
  ```json
  "plugins": [
    { "plugin": "@nxlv/python", "options": { "packageManager": "uv" } }
  ]
  ```
  This just says "when I ask for a Python project, default to `uv`" — it has no effect on any JS/Angular projects in this repo.

- **Per-project** in [`project.json`](project.json): defines the actual `targets` (commands) available for `app-be`, each one backed by an "executor" from the plugin (e.g. `@nxlv/python:install` runs `uv sync` under the hood).

### Available commands (targets)

Run any of these from the **workspace root** (not from inside `apps/app-be`):

```bash
npx nx run app-be:serve     # run the FastAPI app with hot-reload (see section 0)
npx nx run app-be:install   # uv sync — install/update the venv from uv.lock
npx nx run app-be:test      # run the pytest suite (see section 3)
npx nx run app-be:lint      # ruff check — static lint
npx nx run app-be:format    # ruff format — auto-format code
npx nx run app-be:build     # build a wheel + sdist into apps/app-be/dist/
npx nx run app-be:add       # add a new dependency (prompts for name)
npx nx run app-be:update    # update a dependency
npx nx run app-be:remove    # remove a dependency
npx nx run app-be:lock      # regenerate uv.lock without installing
```

Nx also lets you drop the project name shorthand-style: `npx nx test app-be`, `npx nx lint app-be`, etc. — `test`/`lint`/`build` are common target names Nx recognizes directly.

### Adding / removing a dependency (the recommended way)

```bash
npx nx run app-be:add requests            # runtime dependency (positional arg = package name)
npx nx run app-be:add mypy --group=dev     # dev-only dependency (a "dependency group")
npx nx run app-be:remove --name=requests   # remove a dependency (note: --name, not positional here)
```

This updates `pyproject.toml` and `uv.lock` and installs/uninstalls it in `.venv`, all in one step.

### Nx caching

Notice `test`, `lint`, and `build` targets have `"cache": true` in `project.json`. Nx will skip re-running them if nothing relevant changed since the last run (you'll see `[existing outputs match the cache, left as is]`). This is the same caching behavior as any other Nx project — nothing Python-specific to learn there.

## 3. How Python tests work here

This project uses [`pytest`](https://docs.pytest.org/), the standard Python testing framework — roughly the Python equivalent of Jest/Mocha.

### The basics

- Test files live in `tests/` and are named `test_*.py`.
- Test functions inside those files are named `test_*`.
- You assert with the plain `assert` keyword — no special matcher library needed.

Example — [`tests/test_main.py`](tests/test_main.py):

```python
from fastapi.testclient import TestClient

from app_be.main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
```

FastAPI's `TestClient` simulates HTTP requests against your `app` in-process — no real server/socket needed, so tests stay fast. If the assertion is false, pytest fails the test and shows you exactly which values didn't match.

### Running the tests

```bash
npx nx run app-be:test
```

Under the hood ([`project.json`](project.json)) this runs:

```bash
uv run pytest tests/
```

`uv run` makes sure it executes inside the project's `.venv`, so you don't have to activate anything manually.

### What you get in the output

Configured in [`pyproject.toml`](pyproject.toml) under `[tool.pytest.ini_options]`, every test run also produces:

- **Coverage report** — how much of your code the tests actually exercise:
  - HTML: `coverage/apps/app-be/html/index.html` (open in a browser)
  - XML: `coverage/apps/app-be/coverage.xml` (for CI tooling)
- **JUnit XML report**: `reports/apps/app-be/unittests/junit.xml` (for CI test reporting)
- **HTML test report**: `reports/apps/app-be/unittests/html/index.html`

### Writing a new test

Say you add a new endpoint to `src/app_be/main.py`:

```python
@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
```

Add a test in `tests/test_main.py` (or a new `tests/test_<something>.py` file):

```python
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

Then rerun:

```bash
npx nx run app-be:test
```

### Fixtures (`conftest.py`)

[`tests/conftest.py`](tests/conftest.py) is where you put shared setup/fixtures reused across multiple test files — pytest auto-discovers it, you never import from it directly. It's currently empty (just a docstring); you'd add something like:

```python
import pytest


@pytest.fixture
def sample_data():
    return {"id": 1, "name": "example"}


def test_something(sample_data):
    assert sample_data["id"] == 1
```

Any test function that takes `sample_data` as an argument automatically receives the fixture's return value.

## LinkedIn job search (`GET /jobs/linkedin`)

LinkedIn has no public API for job search, so this endpoint authenticates using your own logged-in browser session instead of the OAuth token (which only grants identity scopes). This is unofficial (against LinkedIn's Terms of Service) — use at your own risk.

Add these to the root `.env` file, copied from your browser after logging into linkedin.com (DevTools → Application/Storage → Cookies → `https://www.linkedin.com`):

```
LI_AT_COOKIE=<value of the li_at cookie>
JSESSIONID=<value of the JSESSIONID cookie>
```

These cookies expire periodically (typically after about a year, sooner if LinkedIn flags unusual activity) — if the endpoint starts returning a 502, refresh both values from your browser.

Calling `GET /jobs/linkedin` (params: `keywords`, `geo_id`, `distance`, `hours`, `remote`, `salary_bucket`) fetches matching jobs and writes prettified JSON to `apps/app-be/src/app_be/data/linkedin_data.json` (gitignored), as well as returning it in the response.

## Cheat sheet

```bash
npx nx run app-be:serve     # run the API with hot-reload at http://localhost:8000
npx nx run app-be:install   # first thing to run after cloning / adding a dependency by hand
npx nx run app-be:test      # run tests + coverage
npx nx run app-be:lint      # check code style
npx nx run app-be:format    # auto-fix code style
npx nx run app-be:build     # produce a distributable wheel
npx nx run app-be:add <package>                  # add a runtime dependency
npx nx run app-be:add <package> --group=dev       # add a dev-only dependency
npx nx run app-be:remove --name=<package>         # remove a dependency
```
