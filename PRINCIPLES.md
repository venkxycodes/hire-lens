# Team review principles (optional)

Copy this file to your project as `PRINCIPLES.md` (project root) or inside the
`adversarial-review` skill directory under `.cursor/skills/`, `.claude/skills/`,
or `.agents/skills/`. `adversarial-review` includes relevant sections when present.

Delete sections you do not need. Keep bullets concrete and testable.

## Correctness

- Every error path must be handled or explicitly documented as unreachable.
- Prefer failing fast with actionable errors over silent defaults.
- Race-prone shared state must use an established concurrency pattern from this repo.

## Security

- Validate and sanitize external input at trust boundaries.
- Secrets never appear in logs, comments, or client-visible responses.
- Auth and authorization checks belong on every mutating entry point.

## Design

- Prefer deep modules: small interfaces hiding non-trivial behavior.
- Do not introduce a seam without two real adapters (e.g. production + test).
- Delete pass-through layers that add no behavior.

## Simplicity

- No speculative abstractions for a single call site.
- Do not refactor unrelated code in the same change as a feature or fix.
- Prefer existing library or project utilities over hand-rolled equivalents.

## Testing

- Behavior changes include tests that assert outcomes, not implementation details.
- Critical paths need regression coverage when bugs are fixed.
