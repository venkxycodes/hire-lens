# Agent instructions

Repo-agnostic defaults for coding agents. Pair with productivity skills from this pack.

| Platform | Personal skills | Project skills | Agent contract |
|----------|-----------------|----------------|----------------|
| **Cursor** | `~/.cursor/skills/` | `.cursor/skills/` | this file (`AGENTS.md`) |
| **Codex** | `~/.agents/skills/` | `.agents/skills/` | this file (`AGENTS.md`) |
| **Claude Code** | `~/.claude/skills/` | `.claude/skills/` | `CLAUDE.md` (use `CLAUDE.template.md`) |

Install all three: `./install.sh --personal` and `./install.sh . --bootstrap`

Customize below for your stack, test commands, and conventions.

## Goals

- **Correctness first** — preserve behavior, invariants, and error semantics.
- **Small diffs** — solve the asked problem; no drive-by refactors.
- **Reuse before invent** — match neighboring code and existing project abstractions.
- **Verify** — run relevant tests or static checks before calling work done.

## Before you build

| When | Invoke |
|------|--------|
| Requirements or design unclear | grill / grilling skill |
| Where should this logic live? | `codebase-design` vocabulary |
| Choosing API / module shape | `design-an-interface` |
| Replacing bespoke machinery | `architecture-review` (read-only) |

Do not start large implementations while material decisions are still assumed.

## While implementing

1. Read files around the change — conventions are local, not universal.
2. Prefer the simplest design that satisfies current requirements.
3. Inject dependencies; keep I/O out of pure business logic.
4. Python: `python-design-patterns` skill (Cursor may auto-attach on `**/*.py`).
5. After AI-generated code lands, run `code-simplification` on the touched scope only.

Do not commit unless the user explicitly asks.

## Before merge

| Step | Skill |
|------|-------|
| Size and orient reviewers | `summarize-diff` |
| Challenge the diff (read-only) | `adversarial-review` |
| Tighten without behavior change | `code-simplification` |

Treat high-severity adversarial findings as blocking until addressed or explicitly accepted.

## When output is wrong

Use `prevent-this` on unwanted output. Fix the **guidance or check** that failed,
not only the file.

## Prompts and agent rules

Use the `prompting` skill to review or author system prompts, skills, and tool instructions.

## Project specifics

```text
Stack:       Django 5, DRF, graphene-django, PostgreSQL, WSGI (gunicorn), ASGI (uvicorn)
Install:     uv sync --extra dev --extra test
Lint:        TBD (add ruff when needed)
Test:        uv run poe test
Typecheck:   TBD (optional)
```

Notable paths, env setup, or conventions:

```text
Django project:  host/ (settings, WSGI, ASGI, URLs)
REST API:        api/rest/
GraphQL:         api/graphql/schema.py
Workers:         workers/ (run_worker management command)
Docker:          docker/Dockerfile, docker/entrypoint.sh (SERVICE_ROLE=api|async|worker|migrate)
Env:             cp .env.example .env
Dev commands:    uv run poe dev:api | dev:async | dev:worker | dev:migrate
Skills source:   ~/Desktop/cursor-productivity-skills — re-run install.sh to refresh
```

## Optional team standards

If `PRINCIPLES.md` exists at the repo root, `adversarial-review` includes relevant
sections in reviewer prompts.

## How to invoke skills

| Skill | Cursor | Claude Code | Codex |
|-------|--------|-------------|-------|
| Grill design | `/grill` | `/grilling` | `$grilling` or describe task |
| Design interfaces | `/design-interface` | `/design-an-interface` | `$design-an-interface` |
| Architecture review | `/architecture-review` | `/architecture-review` | `$architecture-review` |
| Summarize diff | `/summarize-diff` | `/summarize-diff` | `$summarize-diff` |
| Prompting | `/prompting` | `/prompting` | `$prompting` |
| Python patterns | `/python-patterns` | `/python-design-patterns` | `$python-design-patterns` |
| Simplify code | `/simplify-code` | `/code-simplification` | `$code-simplification` |
| Adversarial review | `/adversarial-review` | `/adversarial-review` | `$adversarial-review` |
| Prevent slop | `/prevent-this` | `/prevent-this` | `$prevent-this` |

Skills also load from their `description` when your request matches. Explicit-only
skills (`prevent-this`, `code-simplification`, `architecture-review`) require invocation.
