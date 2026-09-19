---
title: Write Explicit Positive Instructions
impact: HIGH
tags: clarity, constraints, behavior
---

# Write Explicit Positive Instructions

State exactly what the model should do. Lead with action verbs and define the desired alternative to prohibited behavior.

Weak:

```text
Do not use bullet points.
```

Better:

```text
Write in flowing prose paragraphs.
```

Explain why a high-impact constraint exists when the reason helps the model generalize to cases the prompt does not enumerate.

Reserve "MUST", "NEVER", and similar emphasis for true invariants. Excessive emphasis creates noisy priority signals and can hide genuine precedence.

For a narrow edit, replace vague or negative-only language without changing unrelated behavior.
