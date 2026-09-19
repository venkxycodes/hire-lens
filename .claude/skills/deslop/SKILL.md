---
name: deslop
description: Detects and removes AI-generated slop from code with certainty-based findings and minimal diffs. Use when cleaning up before a PR, removing debug statements, finding placeholder code, running /deslop, or when the user mentions deslop, repo hygiene, or AI slop. Uses .cursor/repo-intel.json when present for targeted scans.
disable-model-invocation: true
---

# Deslop

Remove AI slop while preserving behavior. Prefer minimal diffs. Default scope is
changed files unless the user asks for a full-repo sweep.

Pair with `code-simplification` after slop removal: deslop deletes debris;
simplification improves structure without changing behavior.

## Modes

| Mode | Behavior |
|------|----------|
| **report** (default) | Findings table only; no edits |
| **apply** | Auto-fix HIGH certainty items, then verify |

Parse user intent from `/deslop`, `/deslop apply`, or natural language.

## Scope

| Scope | When |
|-------|------|
| `diff` (default) | Files changed on current branch |
| `all` | Full repo (user must ask or confirm) |
| `<path>` | Specific directory or file |

## Workflow

### 1. Load repo context

1. Read [detection-patterns.md](references/detection-patterns.md).
2. If `.cursor/deslop/profile.md` exists, read it — it overrides scan priorities
   and lists repo-specific false positives.
3. If `.cursor/repo-intel.json` exists, read [repo-intel.md](references/repo-intel.md)
   and run (when `agent-analyzer` is available):

```bash
MAP=.cursor/repo-intel.json
agent-analyzer repo-intel query slop-fixes   --map-file "$MAP" . 2>/dev/null
agent-analyzer repo-intel query slop-targets --map-file "$MAP" . --limit 20 2>/dev/null
agent-analyzer repo-intel query test-gaps    --map-file "$MAP" . 2>/dev/null
```

   Without the binary, skim `repo-intel.json` for hotspots and symbol data.

4. If repo-intel is missing and scope is not a single file, suggest running
   `deslop/scripts/init-repo-intel.sh` once, then continue with regex detection.

### 2. Determine scan targets

Priority order:

1. `slop-fixes` from repo-intel (after false-positive filter)
2. `slop-targets` files
3. `test-gaps` hot files without tests
4. Diff scope or user path
5. Full tree only when scope is `all`

Skip: `node_modules/`, `.venv/`, `dist/`, `build/`, migrations unless user asks,
generated lockfiles, committed `repo-intel.json`.

### 3. Detect (three phases)

**Phase 1 — Regex (HIGH):** `console.log`, `print()`, `pdb`, `TODO: implement`,
empty `except: pass` / `catch {}`, trailing whitespace.

**Phase 2 — Structural (MEDIUM):** doc/code ratio, stubs, dead code after return,
unused imports, duplicate blocks, defensive cargo cult.

**Phase 3 — Deep (LOW, optional):** run project linter only when user requests
`--thoroughness=deep` or `deep` in the prompt.

Search with ripgrep; read files before claiming a finding.

### 4. Classify and filter

For each finding assign `HIGH` / `MEDIUM` / `LOW`. Drop false positives per
detection-patterns and repo profile. Escalate MEDIUM → HIGH in `test-gaps` files
only when the fix is mechanical (debug log, empty catch).

### 5. Report or apply

**Report mode** — table sorted by certainty, then file:

```markdown
| Certainty | File | Line | Pattern | Suggested fix |
|-----------|------|------|---------|---------------|
```

End with counts: HIGH / MEDIUM / LOW, auto-fixable.

**Apply mode:**

1. Fix HIGH items only, one logical change at a time.
2. Never apply repo-intel `orphan-export` deletes without human review.
3. Run verification from `.cursor/deslop/profile.md` or `AGENTS.md` project specifics.
4. If tests fail, revert the last fix batch and report which finding broke tests.

## Verification

Use repo profile commands when present. Otherwise:

- Python: `pytest` / `uv run pytest` from the project's test root
- TypeScript: `npm run build` or `npm run typecheck` when defined

Do not call work done without running the narrowest relevant check.

## Boundaries

- Do not refactor for style; use `code-simplification` instead.
- Do not delete `TODO` tied to tracked issues unless user confirms.
- Do not remove intentional demo/seed commands (`seed_demo`, fixtures).
- Do not broaden scope beyond the requested diff without asking.

## Related skills

| Skill | When |
|-------|------|
| `code-simplification` | After slop removal, tighten structure |
| `prevent-this` | Diagnose why slop recurred; fix guidance |
| `adversarial-review` | Challenge the cleaned diff before merge |
