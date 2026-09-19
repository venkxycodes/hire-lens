---
title: Treat Prompts Like Code
impact: HIGH
tags: versioning, evals, regression
---

# Treat Prompts Like Code

Production prompts are behavior-bearing artifacts.

- Store them in version control.
- Validate dynamic inputs with typed or schema-checked interfaces.
- Pin model versions when stable behavior matters.
- Test changes with representative fixtures and edge cases.
- Keep regression cases for previously observed failures.
- Compare behavior before and after a change.

Separate reusable instructions from runtime data so changes are reviewable and prompt caching can remain effective.

A wording improvement is incomplete when important behavior has no validation path. Match validation effort to the prompt's risk and frequency of use.

For a one-line change in a production prompt, run the smallest relevant regression set rather than requiring a full prompt redesign.
