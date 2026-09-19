# Claude Code instructions

Repo-agnostic defaults for Claude Code. Pair with productivity skills installed in
`.claude/skills/` (or `~/.claude/skills/`).

Codex reads `AGENTS.md`; Claude reads this file. Keep both in sync when you customize
project commands below, or point Claude at `AGENTS.md` for shared policy.

Customize this file for your project: stack, test commands, conventions, and paths.

## Goals

- **Correctness first** — preserve behavior, invariants, and error semantics.
- **Small diffs** — solve the asked problem; no drive-by refactors.
- **Reuse before invent** — match neighboring code and existing project abstractions.
- **Verify** — run relevant tests or static checks before calling work done.

## Before you build

| When | Claude invocation |
|------|-------------------|
| Requirements or design unclear | `/grilling` |
| Where should this logic live? | mention `codebase-design` or ask about seams |
| Choosing API / module shape | `/design-an-interface` |
| Replacing bespoke machinery | `/architecture-review` (read-only) |

Do not start large implementations while material decisions are still assumed.

## While implementing

1. Read files around the change — conventions are local, not universal.
2. Prefer the simplest design that satisfies current requirements.
3. Inject dependencies; keep I/O out of pure business logic.
4. Python: `/python-design-patterns` or mention structural issues in Python files.
5. After AI-generated code lands, run `/code-simplification` on the touched scope only.

Do not commit unless the user explicitly asks.

## Before merge

| Step | Claude invocation |
|------|-------------------|
| Remove AI debris | `/deslop` |
| Size and orient reviewers | `/summarize-diff` |
| Challenge the diff (read-only) | `/adversarial-review` |
| Tighten without behavior change | `/code-simplification` |

Treat high-severity adversarial findings as blocking until addressed or explicitly accepted.

## When output is wrong

Run `/prevent-this` on unwanted output. Fix the **guidance or check** that failed,
not only the file.

## Prompts and agent rules

Use `/prompting` to review or author system prompts, skills, and tool instructions.

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

## Skill slash commands (Claude Code)

Claude invokes skills by **directory name**:

| Slash | Skill |
|-------|-------|
| `/grilling` | Stress-test a design |
| `/design-an-interface` | Parallel API design exploration |
| `/architecture-review` | Simpler architecture (read-only) |
| `/summarize-diff` | PR/branch breakdown |
| `/prompting` | Prompt and agent-rule review |
| `/python-design-patterns` | Python structure |
| `/code-simplification` | Behavior-preserving clarity |
| `/deslop` | Remove AI slop (uses `.cursor/repo-intel.json` when present) |
| `/adversarial-review` | Multi-lens review |
| `/prevent-this` | Diagnose slop; prevent recurrence |

Run `/reload-skills` after installing or updating skills.
