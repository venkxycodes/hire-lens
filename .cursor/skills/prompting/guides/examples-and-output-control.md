---
title: Examples and Output Control
appliesTo: prompts with format, tone, or judgment requirements
tags: few-shot, schema, formatting, uncertainty
---

# Examples and Output Control

Use examples when the model must learn a format, tone, judgment boundary, or edge case that prose instructions do not define reliably.

## Few-Shot Guidance

- Start with one example and add more only if output remains inconsistent.
- Use two to five diverse examples for most production prompts that need few-shot guidance.
- Label examples so they are not confused with live input.
- Cover boundaries and failure cases, not only the happy path.
- Verify every detail because models reproduce mistakes in examples.

Examples are unnecessary when a direct instruction is already unambiguous.

## Output Guidance

- Describe the output to produce, not only what to avoid.
- Match the prompt's style to the desired response style.
- Use a template or schema when exact formatting matters.
- Specify length, tone, citation style, and failure behavior only when they affect success.
- Define what to do when evidence is missing.

```text
If the data is insufficient to draw a conclusion, say so rather than speculating.
```

## Roles

Prefer explicit behavior over decorative personas:

```text
Analyze this portfolio focusing on risk tolerance and long-term growth potential.
```

Use a role only when it creates a consistent perspective, expertise boundary, or tone across outputs.

## Narrow Edits

When revising one line, improve only the behavior that line controls. Do not add examples, schemas, or role framing unless the selected line itself defines output behavior and needs that precision.
