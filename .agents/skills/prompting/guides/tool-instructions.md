---
title: Tool Instructions
appliesTo: prompts for tool-using agents
tags: tools, side-effects, evidence, parallelism
---

# Tool Instructions

Tool-using agents perform better when each tool has a precise, non-overlapping responsibility.

For each tool, define only what the agent needs:

- Purpose and appropriate use cases.
- Required parameters and input constraints.
- Limits, side effects, and permission boundaries.
- Evidence to gather before acting.
- Expected high-signal result fields.
- Failure behavior and safe alternatives.
- Validation required after a mutation.

Prefer fewer well-scoped tools over overlapping alternatives. When two tools appear suitable, state the decision boundary.

Ask tools to return stable IDs, relevant fields, and concise summaries instead of unbounded raw output.

## Dependencies and Parallelism

```text
If multiple tool calls have no dependencies between them, make all independent
calls in parallel. Never use placeholders for missing parameters. Call
sequentially when outputs depend on prior calls.
```

## Risk

Distinguish read-only operations, reversible mutations, and destructive actions. State which actions are autonomous and which require confirmation.

## Narrow Edits

When revising one tool rule, keep the edit local. Check neighboring tool rules for overlap or contradiction, but do not redesign the complete tool surface unless the selected rule cannot be made correct in isolation.
