---
name: adversarial-review
description: >-
  Adversarial code review using parallel subagents to challenge work from
  distinct critical lenses.
  Produces a synthesized verdict with findings and lead judgment. Triggers: adversarial review, /adversarial-review, $adversarial-review.
---

# Adversarial Review

Spawn independent read-only subagents to challenge work. Reviewers attack from
distinct lenses. The deliverable is a synthesized verdict; do not make changes.

## Step 1 — Load Review Rules

Read `references/reviewer-lenses.md` and `references/verdict-format.md`. If a local
principles file exists (project root `PRINCIPLES.md`, or
`PRINCIPLES.md` inside this skill directory under `.cursor/skills/`,
`.claude/skills/`, or `.agents/skills/`), read it and include only the relevant
principle text in reviewer prompts. If no principles file exists, proceed with the
lens definitions and do not invent principle contents.

## Step 2 — Determine Scope and Intent

Identify what to review from context (recent diffs, referenced plans, user message).

Determine the **intent** — what the author is trying to achieve. This is critical: reviewers
challenge whether the work *achieves the intent well*, not whether the intent is correct.
State the intent explicitly before proceeding.

Assess change size:

| Size | Threshold | Reviewers |
|------|-----------|-----------|
| Small | < 50 lines, 1-2 files | 1 (Skeptic) |
| Medium | 50-200 lines, 3-5 files | 2 (Skeptic + Architect) |
| Large | 200+ lines or 5+ files | 3 (Skeptic + Architect + Minimalist) |

Use `references/reviewer-lenses.md` for lens definitions.

## Step 3 — Spawn Reviewers

Build each reviewer's prompt using the template in `references/reviewer-prompt.md`.
Read `references/subagent-spawn.md` for platform-specific worker launch rules.

Launch all reviewer workers in a single parallel batch when the platform supports it.
Give each worker one lens and the full reviewer prompt.
Ask each worker to return only its review in the requested markdown format.

Use the number of reviewers from Step 2. Do not use shell CLIs or standalone agent commands.

## Step 4 — Verify and Synthesize Verdict

Confirm every launched reviewer returned output. If a reviewer failed, note the failure in
the verdict. Do not silently skip a reviewer.

Deduplicate overlapping findings. Produce a single verdict using the format in
`references/verdict-format.md`.

## Step 5 — Render Judgment

After synthesizing the reviewers, apply your own judgment. Using the stated intent and loaded
review rules as your frame, state which findings you would accept and which you would reject.
Reviewers are adversarial by design; not every finding warrants action. Call out false
positives, overreach, and findings that mistake style for substance.

Append the Lead Judgment section to the verdict (see `references/verdict-format.md`).
