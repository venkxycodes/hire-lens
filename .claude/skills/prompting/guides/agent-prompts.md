---
title: Agent Prompts
appliesTo: tool-using and multi-step agents
tags: autonomy, persistence, confirmation, stopping
---

# Agent Prompts

Agent prompts need explicit boundaries for tool use, persistence, autonomy, risk, and validation.

Define:

- Available context and authoritative source material.
- Existing patterns, interfaces, or prior decisions to reuse.
- Scope and non-goals.
- Validation and stopping conditions.
- Safe reversible actions the agent may take autonomously.
- Risky or destructive actions that require confirmation.
- When to ask, search, proceed under uncertainty, or stop.

Use a plan when ambiguity or sequencing materially affects safety or correctness. Do not require a plan for a trivial, well-scoped action.

## Persistence

```text
Keep going until the task is fully resolved before yielding to the user.
Decompose the query into sub-tasks and confirm each is completed.
Do not stop after partial completion.
Proceed on safe, reversible actions and document assumptions.
```

## Bounded Exploration

```text
Search depth: low. Maximum 2 tool calls before responding.
If uncertain, report findings and open questions rather than exploring further.
```

Do not combine unbounded persistence with a strict exploration cap unless the prompt defines which rule wins.

## Coding-Agent Additions

```text
Reuse existing patterns in [path/component/module].
Keep changes scoped to [area].
Run [tests/checks].
Do not change [non-goals].
Ask only if [specific blocker].
```

Apply only the controls needed for the task. Extra autonomy rules can obscure the actual goal.
