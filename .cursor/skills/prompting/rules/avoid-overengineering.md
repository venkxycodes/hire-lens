---
title: Add Only Techniques That Solve a Need
impact: HIGH
tags: simplicity, architecture, anti-patterns
---

# Add Only Techniques That Solve a Need

Use the smallest instruction set that reliably produces the desired behavior.

Do not mechanically add:

- Roles that do not create a useful perspective.
- Headings for a one-line prompt.
- Examples when the instruction is already precise.
- Schemas when approximate formatting is acceptable.
- Agent persistence or tool rules for a non-agent task.
- Repeated prohibitions that do not define an alternative.
- Prompt-level condition trees where a principle would generalize better.

For complete prompts, consider all available guidance and include only what serves the success criteria.

For a selected line or section, preserve the surrounding architecture. A local improvement should remain local unless a broader contradiction makes that impossible.
