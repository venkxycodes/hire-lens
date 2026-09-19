---
title: Match Guidance to the Requested Scope
impact: CRITICAL
tags: scope, fragments, files, defaults
---

# Match Guidance to the Requested Scope

Determine whether the target is a fragment or a complete prompt before editing.

## Precedence

1. Explicit user instructions define scope.
2. Explicit context, such as a selected line or marked excerpt, can define a narrower scope.
3. If neither makes the scope narrow, default to complete-prompt guidance.

## Fragment

For a clearly selected line, sentence, or small section:

- Preserve surrounding structure, terminology, and voice.
- Apply the core principles and only relevant topic guidance.
- Do not add a complete prompt architecture, role, examples, schema, or validation section unless the fragment specifically needs one.
- Mention a broader conflict only when it prevents a correct local fix.

```text
Selected line: "Don't make assumptions."
Rewrite: "If evidence is insufficient, state what is unknown and ask for the missing information."
```

## Complete Prompt

For a complete prompt, prompt file, or ambiguous request:

- Read `../AGENTS.md`.
- Consider every section as decision context.
- Keep only techniques tied to the prompt's requirements or observed failure modes.

"Use the full guide" does not mean "insert every technique." It means no category is skipped without considering whether it applies.
