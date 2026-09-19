---
title: Prompt Architecture
appliesTo: complete prompts and multi-part workflows
tags: structure, delimiters, templates, grounding
---

# Prompt Architecture

Use explicit architecture when a complete prompt has multiple instruction types or substantial source context. Do not impose this structure on an isolated line or small local edit.

Separate instructions, context, examples, input data, and output requirements with clear headings, labels, fenced blocks, or schemas.

Recommended order when every section is needed:

```text
1. Role and goal       - who the model is, what outcome matters
2. Constraints         - rules, non-goals, safety boundaries
3. Tool guidance       - when and how to use each tool
4. Examples            - input/output pairs or decision examples
5. Source context      - documents, retrieved content, variable input
6. Task                - current request, question, or data to process
7. Output contract     - exact format, length, tone, schema, citations
```

Treat this as a menu, not a mandatory template. Omit sections that do not change behavior.

For long prompts:

- Keep reusable instructions stable near the top.
- Place source material before the final task.
- Delimit untrusted or variable input from instructions.
- Ask for cited or quoted evidence before conclusions when grounding matters.
- Keep the final task and output contract close to the end.

For a narrow edit, preserve the surrounding architecture. Add or move a section only when the selected text cannot be interpreted correctly in its current location.
