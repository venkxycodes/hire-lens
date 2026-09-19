# Implementation review

## Intent

Build a simple Django/React recruiter workspace using the requested Django base and Jev: jobs, weighted criteria, bulk resumes, asynchronous scores, recruiter decisions, and outreach drafts.

## Verdict: PASS after fixes

Three independent read-only reviews were completed: Skeptic, Architect, and Minimalist. All identified findings were accepted and addressed before delivery.

## Findings and resolutions

1. **High — Candidate PATCH could overwrite a concurrent evaluation pointer.** Skeptic and Architect, serialize shared-state mutations. Fixed by rebinding the serializer to the row-locked application before saving and capturing old audit values separately. Regression test recreates a stale read followed by enqueue and a stage update, then verifies notes save preserves both.
2. **Medium — Completed demo results could not be replaced by live results.** Skeptic and Architect, correctness of evaluation identity. Provider, model, and prompt version are now part of the evaluation identity and stale predicate. Historical results remain intact; regression coverage verifies mode transition and exclusion from current ranking.
3. **Medium — Review navigation changed during score polling.** Architect and Minimalist, stable workflow. The open review session freezes its candidate ID order.
4. **Medium — Shrinking filtered result sets could strand the user on an invalid page.** Architect. A paginated 404 resets the list to its first page.
5. **Medium — Escape could hide an active upload while leaving it mounted.** Minimalist. The dialog prevents native cancel and delegates closing to the upload's busy guard. Covered in browser flow.
6. **Medium — Extracted names could not be corrected.** Minimalist. Candidate review now permits name/email corrections.
7. **Medium — Navigation could silently discard notes and outreach drafts.** Minimalist. Draft subject/body now persist on the application; unsaved candidate edits guard close/next/previous and browser unload. Browser flow verifies warning and saved draft persistence.
8. **Medium — Transient database failures could stop the worker.** Skeptic. Worker catches database errors, cleans stale connections, and backs off before polling again. A production supervisor remains recommended.

## What went well

- Durable evaluation records, immutable input snapshots, lease ownership, and strict result validation.
- Server-side user scoping with regression tests for foreign IDs and downloads.
- Demo results and outdated criteria are explicitly distinguished from current Jev results.

## Lead judgment

Accepted all eight findings: each described a concrete state transition or user action that could lose work or misrepresent results. No style-only findings were used to expand the product. The simplification pass retained the ORM rather than adding repository abstractions, kept deterministic scoring independent of network I/O, and formatted the touched source.

## Verification scope

Backend regression suite, Django system/migration checks, source lint, TypeScript/production build, formatting, and an end-to-end Chromium recruiter flow. Desktop and mobile screenshots were inspected. Live Jev behavior is validated with HTTP contract fixtures, not a paid live call: no provider key was supplied. PostgreSQL multi-worker load and real-candidate rubric accuracy have not been benchmarked.
