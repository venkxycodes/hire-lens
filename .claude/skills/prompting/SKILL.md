---
name: prompting
description: Design, review, and improve prompts for LLMs, coding agents, system prompts, custom instructions, tool instructions, eval-ready prompts, and repeatable AI workflows. Use when writing prompt templates, reviewing model instructions, creating agent behavior rules, debugging prompt failures, making prompts more testable, or invoking /prompting.
---

# Prompting

Write prompts that are clear, structured, minimal, and testable. A good prompt is the smallest high-signal instruction set that reliably produces desired behavior.

## Scope First

Determine the unit of work before choosing techniques.

1. Explicit scope in the user's request or supplied context wins.
2. For a clearly selected line, sentence, or small section, preserve the surrounding prompt and apply only relevant principles. Do not impose a full prompt architecture.
3. For a complete prompt or prompt file, read `AGENTS.md` in this skill directory and use the full guide as decision context.
4. If scope is ambiguous, default to the complete guide.

Applying the full guide means considering every section, not mechanically adding every technique. Examples, schemas, roles, tool rules, and multi-section architecture remain conditional on the prompt's job.

Read `rules/scope-sensitive-application.md` whenever the requested scope could be unclear.

## Atomic Rules

Use these for narrow edits or focused review:

- `rules/scope-sensitive-application.md` — match the edit to the actual artifact
- `rules/success-criteria.md` — define the outcome and done condition
- `rules/explicit-positive-instructions.md` — state desired behavior directly
- `rules/high-signal-context.md` — include only decision-relevant context
- `rules/examples-for-boundaries.md` — demonstrate formats and judgment edges
- `rules/prompts-as-code.md` — version and validate production prompts
- `rules/avoid-overengineering.md` — add techniques only for observed needs

## Topic Guides

Read focused guides when their topic is relevant:

- `guides/prompt-architecture.md` — structure complete or multi-part prompts
- `guides/examples-and-output-control.md` — control format, tone, and edge cases
- `guides/agent-prompts.md` — set autonomy, persistence, risk, and stopping rules
- `guides/tool-instructions.md` — define precise, non-overlapping tool behavior
- `guides/context-engineering.md` — curate context across long or repeated workflows
- `guides/review-and-validation.md` — diagnose failures and verify prompt changes

## Usage Modes

### Complete prompt or file

Read `AGENTS.md` in this skill directory. Review the entire artifact against the compiled guidance, then make the smallest coherent change that meets the success criteria.

### Selected line or section

Read the scope rule, the relevant atomic rules, and only the topic guides needed for that fragment. Keep the local edit local unless the fragment exposes a broader contradiction that prevents a correct fix.

Example:

```text
Selected line: "Don't make assumptions."
Focused rewrite: "If evidence is insufficient, state what is unknown and ask for the missing information."
```

The focused rewrite applies explicit, positive behavior without wrapping one line in a full prompt template.
