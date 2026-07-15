# ai-linkedin-job-searcher

An [Nx](https://nx.dev) monorepo for an AI-assisted LinkedIn job search tool.

## Apps

- **[`apps/app-be`](apps/app-be/README.md)** — Python/FastAPI backend. Handles LinkedIn OAuth and job search, plus AI-assisted matching via OpenAI/Azure AI Foundry. See its README for setup, running, and testing.

See [`CLAUDE.md`](CLAUDE.md) for coding conventions and the architecture used in `apps/app-be`.

## Running tasks

```sh
npx nx <target> <project>
```

For example:

```sh
npx nx serve app-be
npx nx test app-be
```

Targets are defined per-project in each project's `project.json`. Run `npx nx graph` to visually explore the project graph.

[More about running tasks in the Nx docs »](https://nx.dev/features/run-tasks)

## Package managers

- Root workspace: npm (`package-lock.json`).
- `apps/app-be` (Python): [`uv`](https://docs.astral.sh/uv/), wired into Nx via the [`@nxlv/python`](https://github.com/lucasvieirasilva/nx-plugins) plugin — see `apps/app-be/README.md` for details.

## CI / Nx Cloud

Not configured yet. No Nx Cloud connection, no CI workflows.
