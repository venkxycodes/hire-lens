---
title: Keep Context High-Signal
impact: HIGH
tags: context, relevance, retrieval
---

# Keep Context High-Signal

Include information the model cannot infer and that changes a decision:

- Domain facts and terminology.
- Authoritative source material.
- Relevant examples.
- Assumptions and prior decisions.
- Current task state.

Remove background that does not affect the output. Ask of each paragraph:

```text
What decision will this information change?
```

Use retrieval or progressive disclosure for details that are only conditionally relevant.

Keep instructions distinct from untrusted, retrieved, or user-provided content. Delimit source material so it cannot be mistaken for instructions.

For a selected-line edit, consult surrounding context to preserve meaning but keep the requested change local.
