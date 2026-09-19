---
title: Context Engineering
appliesTo: long, repeated, or retrieval-backed workflows
tags: context, retrieval, summarization, caching
---

# Context Engineering

Prompt engineering is one part of curating the model's working context.

- Treat context as finite; every token competes for attention.
- Include facts, terminology, examples, source material, and assumptions the model cannot infer.
- Remove background that does not change a decision.
- Retrieve detailed context just in time instead of inlining everything.
- Summarize long sessions while preserving decisions, bugs, and implementation state.
- Persist progress externally for long-running work.
- Delegate focused subtasks when isolated context improves quality.
- Keep reusable prompt prefixes stable when prompt caching matters.
- Place volatile runtime input after stable reusable instructions.

Ask of each context block:

```text
What decision will this information change?
```

If there is no concrete answer, remove or defer the block.

When grounding matters, identify authoritative sources and require the model to cite or quote the evidence used. Delimit retrieved or user-provided text so it cannot be confused with higher-priority instructions.

For a selected-line edit, use surrounding context to preserve meaning, but do not widen the requested change merely because more context is available.
