---
title: Review and Validation
appliesTo: prompt reviews, debugging, and production changes
tags: review, evals, regression, diagnosis
---

# Review and Validation

Review prompts against explicit success criteria rather than general impressions.

## Decision Framework

1. What behavior defines success?
2. Is the target a fragment or a complete prompt?
3. Does the model lack decision-relevant context?
4. Does format need a template, schema, or example?
5. Does complexity justify sections, prompt chaining, or delegation?
6. Does an agent need autonomy, tool, confirmation, and stopping rules?
7. How will the change be validated?

## Failure Diagnosis

Identify the observed failure before adding instructions:

- Missing knowledge may require retrieval or better context.
- Inconsistent format may require a template, schema, or example.
- Conflicting behavior may come from contradictory instructions or unclear precedence.
- Premature stopping may require a completion condition.
- Excessive exploration may require bounded search and stopping rules.
- Stable prompt failures may actually be model, latency, product, or tool-design problems.

## Validation

- Use representative fixtures for important behavior.
- Add edge cases around judgment boundaries.
- Compare before and after outputs.
- Pin the model version when stable behavior matters.
- Keep regression cases for failures the prompt has already exhibited.

## Final Checklist

- The edit matches the requested scope.
- The outcome and done condition are explicit enough.
- Context is sufficient but not bloated.
- Instructions are direct and non-conflicting.
- Output requirements are precise where needed.
- Examples are accurate and necessary.
- Tool and autonomy rules match task risk.
- Important behavior has a validation method.
- No technique was added without a concrete purpose.
