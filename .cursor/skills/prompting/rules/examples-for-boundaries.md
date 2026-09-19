---
title: Use Examples for Boundaries
impact: HIGH
tags: examples, few-shot, edge-cases
---

# Use Examples for Boundaries

Use examples when the desired format, tone, classification boundary, or judgment rule is difficult to specify reliably in prose.

- Start with one example.
- Add examples only when they cover distinct behavior or fix observed inconsistency.
- Cover edge cases and boundaries, not only happy paths.
- Label examples separately from live input.
- Verify every detail because models reproduce example mistakes.

Do not add examples when a direct instruction is already sufficient. Examples consume context and can overfit behavior to incidental details.

For a narrow edit, add or change an example only when the selected text controls a behavior that examples clarify better than prose.
