# django-base-code

Reusable Django boilerplate for building APIs, async services, and background
workers. Clone once, rename apps as needed, and layer your domain code on top.

## Features

- **WSGI** and **ASGI** entrypoints with separate dev commands
- **REST** (`/api/v1/`) and **GraphQL** (`/graphql/`) with example endpoints
- **Background workers** via `run_worker` management command
- **Docker** image with `SERVICE_ROLE` switch (`api`, `async`, `worker`, `migrate`)
- **Example env** in [`.env.example`](.env.example)

## Project layout

```text
manage.py
host/              # Django project (settings, WSGI, ASGI, URLs)
api/
  rest/            # REST API views
  graphql/         # GraphQL schema
workers/           # Background worker entrypoints
docker/            # Dockerfile and entrypoint
tests/
```

## Local development

```bash
cp .env.example .env
docker compose up -d postgres
uv sync --extra dev --extra test
uv run poe dev:migrate
uv run poe dev:api          # WSGI on :8000
uv run poe dev:async        # ASGI on :8001
uv run poe dev:worker       # separate terminal
uv run poe test
```

## Docker

Run the full stack (migrate, API, async, worker):

```bash
docker compose up --build
```

Run a single role:

```bash
docker build -f docker/Dockerfile -t django-base-code .
docker run --rm -e SERVICE_ROLE=api -p 8000:8000 django-base-code
docker run --rm -e SERVICE_ROLE=async -p 8001:8001 django-base-code
docker run --rm -e SERVICE_ROLE=worker django-base-code
```

## API reference

### REST

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/info` | App name, version, environment |
| POST | `/api/v1/echo` | Echo JSON `{"message": "..."}` |

### GraphQL

Open GraphiQL at `http://localhost:8000/graphql/` when `DEBUG=true`.

Example query:

```graphql
{
  health
  version
}
```

Example mutation:

```graphql
mutation {
  echo(message: "hello") {
    message
  }
}
```

## Settings

| Module | Use |
|--------|-----|
| `host.settings.local` | Local development (default) |
| `host.settings.test` | pytest (SQLite in-memory) |
| `host.settings.base` | Production defaults |

Set `DJANGO_SETTINGS_MODULE` to override the resolver.

## Extending

1. Add Django apps under the repo root and register them in `host.settings.base`.
2. Add REST routes in `api/rest/` or new URL modules.
3. Extend `api/graphql/schema.py` with queries and mutations.
4. Replace the idle loop in `workers/runner.py` with your job processor.

## Agentic development

This repo is bootstrapped for **Cursor**, **Codex**, and **Claude Code** via
[cursor-productivity-skills](https://github.com/venkxycodes/cursor-productivity-skills).

| Platform | Skills | Commands / contract |
|----------|--------|---------------------|
| **Cursor** | `.cursor/skills/` | `.cursor/commands/` + [`AGENTS.md`](AGENTS.md) |
| **Codex** | `.agents/skills/` | [`AGENTS.md`](AGENTS.md) |
| **Claude Code** | `.claude/skills/` | [`CLAUDE.md`](CLAUDE.md) |

Start a **new agent session** after install. Claude Code: run `/reload-skills` if
skills were just added.

Refresh skills from the source pack:

```bash
~/Desktop/cursor-productivity-skills/install.sh "$(pwd)"
```

Re-bootstrap agent contracts (only creates missing files):

```bash
~/Desktop/cursor-productivity-skills/install.sh "$(pwd)" --bootstrap
```

Suggested workflow: `/grill` or `/grilling` → implement → `/python-patterns` →
`/simplify-code` → `/adversarial-review` before merge.
