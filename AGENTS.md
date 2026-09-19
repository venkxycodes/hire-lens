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
| Remove AI debris | `deslop` |
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

Stack: Django/DRF, React/TypeScript/Vite, TypeSafe Jev.
Backend: `backend/`; frontend: `frontend/`; contracts: `docs/design.md`.
Install: `cd backend && uv sync --extra dev --extra test`; `cd frontend && npm ci`.
Checks: backend `uv run pytest`, `uv run ruff check recruiting tests/test_recruiting.py`, `uv run python manage.py check`; frontend `npm run build`, `npm run format:check`.
Browser tests: `E2E_PASSWORD=... npm run test:e2e` with demo services running.
Local app: `./scripts/dev.sh`, UI port 5188, API port 8018.
Keep real provider credentials in backend/.env. Never expose them to the frontend.
Demo scores must always be labeled; stale scores must not rank as current.
Do not send candidate emails or auto-reject based on a model score.

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
| Deslop | `/deslop` | `/deslop` | `$deslop` |
| Adversarial review | `/adversarial-review` | `/adversarial-review` | `$adversarial-review` |
| Prevent slop | `/prevent-this` | `/prevent-this` | `$prevent-this` |

Skills also load from their `description` when your request matches. Explicit-only
skills (`prevent-this`, `code-simplification`, `deslop`, `architecture-review`) require invocation.
