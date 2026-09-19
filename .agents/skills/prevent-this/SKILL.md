---
name: prevent-this
description: Diagnoses why an agent produced a specific unwanted code output by adversarially reviewing the parent transcript, target code, and available guidance. Use when the user invokes /prevent-this on AI-generated slop and wants evidence-backed recommendations that prevent recurrence without editing files.
disable-model-invocation: true
---

# Prevent This

Stop the active task. Audit the unwanted output and recommend the smallest durable
change that would prevent the same failure. Do not edit code, rules, skills,
documentation, or git state.

## Success Criteria

A run is complete when it:

- reconstructs the failure from transcript and code evidence;
- distinguishes guidance loaded before generation from guidance found afterward;
- names one primary cause and any secondary contributors;
- recommends one earliest effective prevention, or `no change recommended`; and
- states how a future run would verify that prevention.

## Inputs

- Required: the unwanted code or a precise file/range/diff that identifies it.
- Required: the user's explicit statement of what the output should have been.

If either required input is missing or ambiguous, ask for it before reviewing.

## Workflow

1. **Inspect the target** — Read the unwanted code and enough surrounding code to
   identify its responsibility, consumers, and current placement.

2. **Reconstruct the parent run** — Trace:
   user intent → instructions and context available → files and guidance inspected
   → agent decisions → produced output → user correction.
   Record separately:
   - guidance loaded before the unwanted output;
   - guidance that existed but was not loaded; and
   - guidance created only after the output.

   When chronology affects the conclusion, use version history to confirm that
   cited guidance existed when the output was generated.

3. **Inspect prevention context** — Read relevant `AGENTS.md`, `CLAUDE.md`, scoped
   rules, skills, architecture/context documents, lint configuration, and nearby
   precedents. Determine both whether correct guidance exists and whether the agent
   had a reliable trigger to load it.

4. **Launch one adversarial meta-reviewer** — Read
   [reviewer-prompt.md](references/reviewer-prompt.md) and
   [subagent-spawn.md](references/subagent-spawn.md). Fill evidence fields
   with the target, intended behavior, transcript chronology, guidance timing, and
   nearby precedent. Ask it to return only the requested review.

   If the worker fails, retry once with the same evidence. If it fails again,
   report the failure and complete the evidence check yourself.

5. **Verify causality** — Check every reviewer claim against the transcript, target
   code, and authoritative context. Explain the observable decision path; do not
   speculate about hidden model reasoning.

6. **Classify the primary cause** — Choose exactly one:
   - **Missing guidance** — no durable instruction covered the decision when the
     output was generated.
   - **Discovery gap** — correct guidance existed but path/triggering did not
     reliably surface it.
   - **Ambiguous guidance** — relevant guidance allowed the bad interpretation.
   - **Conflicting guidance** — applicable instructions pulled in different
     directions.
   - **Misleading precedent** — nearby code or structure taught the wrong pattern.
   - **Agent noncompliance** — clear, applicable guidance or an explicit user
     instruction was loaded before generation and ignored.
   - **Missing user input** — a required decision could not be inferred.
   - **Tool or environment limit** — unavailable evidence or tooling forced a weak
     path.

   List secondary contributors separately. Do not label absent guidance when the
   real defect is discovery or noncompliance.

   Apply these boundaries:
   - An architecture document contains the answer, but no loaded instruction or
     reliable trigger directed the agent to it → **Discovery gap**.
   - Loaded `AGENTS.md` or a loaded skill explicitly directs the placement decision,
     but the agent skips it → **Agent noncompliance**; do not duplicate the rule.

7. **Recommend one prevention** — Prefer, in order:
   - improve discovery or precision of the existing authoritative source;
   - add a mechanical lint/test check when the invariant is objectively enforceable;
   - otherwise add narrowly scoped guidance at the owning boundary.

   Name the exact target file, proposed change, and one representative next-run
   check. Avoid duplicate documentation, broad always-on rules for app-local
   concerns, compatibility shims, and generic reminders to "be careful." If clear
   loaded guidance already covered a one-off violation, state
   `no change recommended`.

8. **Render the report** — Deduplicate the reviewer's findings and reject
   unsupported claims. Follow the report guidance below.

## Report

Lead with what the agent produced, why it happened, and the smallest useful
prevention. Cover:

- the user's required expected behavior and the discrepancy in the output;
- the observable decision path and strongest supporting evidence;
- one primary cause, with secondary contributors only when useful;
- the exact prevention target and a representative next-run check, or
  `no change recommended`; and
- missing evidence that could change the conclusion.

Use the structure that communicates the diagnosis most clearly.

## Boundaries

- Recommendations only; never implement them during this skill.
- Review one failure and its causal chain, not general code quality.
- Do not treat all bad code as a context defect.
- Cite concrete transcript moments and code locations.
- Recommend modifying an existing authority before creating another source of truth.
