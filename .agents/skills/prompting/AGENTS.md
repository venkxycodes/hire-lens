# Prompting Guide

This is the complete prompting reference. Use it for complete prompts, prompt files, system instructions, agent workflows, or whenever the requested scope is ambiguous.

## Operating Contract

Determine the unit of work before applying techniques:

1. Explicit scope in the user's request or supplied context wins.
2. A clearly selected line, sentence, or small section receives a local edit that preserves the surrounding prompt.
3. A complete prompt or prompt file receives a full review against this guide.
4. Ambiguous scope defaults to a full review.

Use every section as decision context for a full review, but do not mechanically add every technique. A short prompt may already be complete. Architecture, roles, examples, schemas, agent controls, and tool guidance are useful only when the task requires them.

## Core Principles

### Start with success criteria

- Define the outcome, audience, constraints, and done condition before polishing wording.
- If quality matters, create eval cases or representative fixtures first.
- If latency, cost, retrieval, model choice, or product design is the real problem, say so; prompting may not be the right fix.

### Be explicit and direct

- State exactly what to do and lead with action verbs.
- Explain why important constraints exist so the model can generalize.
- Describe desired behavior, not only prohibited behavior.

### Keep context high-signal

- Include facts, domain terms, examples, source material, and assumptions the model cannot infer.
- Omit background that does not change decisions.
- Challenge every paragraph: "Does the model need this?"

### Show, do not only tell

- Use examples when format, tone, judgment boundaries, or edge cases matter.
- Keep examples accurate; models copy small details, including mistakes.

### Treat prompts like code

- Store production prompts in versioned files with typed or validated inputs.
- Pin model versions where stable behavior matters.
- Test prompt changes with fixtures, evals, and regression cases.

## Scope-Sensitive Application

For a narrow edit:

- Preserve the prompt's established structure, terminology, and voice.
- Apply the core principles and only the topic guidance relevant to the selected text.
- Do not add headings, roles, examples, schemas, or validation sections unless the selected text needs them.
- Surface a broader conflict only when it prevents a correct local fix.

For a complete prompt:

- Consider all guidance in this document.
- Keep only techniques that solve a concrete requirement or failure mode.
- Prefer one coherent rewrite over a collection of disconnected patches.

Examples:

```text
Selected line: "Don't make assumptions."
Rewrite: "If evidence is insufficient, state what is unknown and ask for the missing information."
```

```text
Complete-file request: "Review this coding-agent system prompt."
Action: inspect success criteria, architecture, context, autonomy, tools, validation,
failure behavior, output contract, and contradictions before revising the file.
```

## Prompt Architecture

Use explicit structure for complete or multi-part prompts when it makes instruction boundaries easier to follow. Separate instructions, context, examples, input data, and output requirements with headings, labels, fenced blocks, or schemas.

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

This is a menu, not a mandatory template. Omit sections that do not change behavior. For long context, keep reusable instructions stable near the top, place source material before the final task, and ask for cited or quoted evidence when grounding matters.

## Few-Shot Examples

Examples anchor format, tone, and decision boundaries better than abstract descriptions.

- Start with one example and add more only if behavior remains inconsistent.
- Use two to five diverse examples for most production prompts that need few-shot guidance.
- Label examples so the model distinguishes them from instructions and live input.
- Cover important edge cases and judgment boundaries, not only the happy path.
- Verify every detail because models reproduce mistakes in examples.

## Role Assignment

A single sentence focused on behavior is usually enough. Over-constraining a role can reduce helpfulness.

Prefer:

```text
Analyze this portfolio focusing on risk tolerance and long-term growth potential.
```

Over:

```text
You are a senior financial analyst.
```

Use a role when it creates a consistent perspective, expertise boundary, or tone across many outputs.

## Output Control

1. Describe the output to produce, not only what to avoid.
2. Match prompt style to desired output style; Markdown-heavy prompts often produce Markdown-heavy responses.
3. Use a template, schema, or example when exact formatting matters.
4. Specify length, tone, citations, and failure behavior only when they affect success.

When uncertainty matters:

```text
If the data is insufficient to draw a conclusion, say so rather than speculating.
```

## Agent Prompts

Agent prompts need explicit boundaries for tool use, persistence, autonomy, and validation.

- Define available context and authoritative source material.
- Name existing patterns, interfaces, or decisions to reuse.
- State scope, non-goals, validation, and stopping conditions.
- Distinguish safe reversible actions from risky actions that require confirmation.
- Say when to ask, when to search, and when to proceed under uncertainty.
- For ambiguous or multi-step work, require a plan when planning materially reduces risk.

Persistence:

```text
Keep going until the task is fully resolved before yielding to the user.
Decompose the query into sub-tasks and confirm each is completed.
Do not stop after partial completion.
Proceed on safe, reversible actions and document assumptions.
```

Bounded exploration:

```text
Search depth: low. Maximum 2 tool calls before responding.
If uncertain, report findings and open questions rather than exploring further.
```

Do not combine unbounded persistence with strict exploration limits unless the prompt defines which rule wins.

## Tool Instructions

Tool-using agents perform better when tool responsibilities are precise and non-overlapping.

- Describe each tool's purpose, parameters, limits, side effects, and failure modes.
- Prefer fewer well-scoped tools over overlapping alternatives.
- State what evidence the agent must gather before acting.
- Ask tools to return stable IDs, relevant fields, and concise high-signal results.
- Specify validation such as tests, screenshots, citations, or metrics.
- Parallelize only independent calls; sequence calls with data dependencies.

```text
If multiple tool calls have no dependencies between them, make all independent
calls in parallel. Never use placeholders for missing parameters. Call
sequentially when outputs depend on prior calls.
```

## Prompt Template

Use this shape when a complete prompt benefits from explicit sections:

```text
Role: [specific role or behavior]
Goal: [concrete outcome]
Context: [facts, source material, constraints]
Instructions:
1. [decision rule or step]
2. [decision rule or step]
Validation: [checks or stopping condition]
Output: [format, length, tone, schema]
```

For coding agents, add only the controls the task needs:

```text
Reuse existing patterns in [path/component/module].
Keep changes scoped to [area].
Run [tests/checks].
Do not change [non-goals].
Ask only if [specific blocker].
```

## Context Engineering

Prompt engineering is one part of curating the model's working context.

- Treat context as finite; every token competes for attention.
- Retrieve detailed context just in time.
- Summarize long sessions while preserving decisions, bugs, and implementation state.
- Persist progress externally for long-running work.
- Delegate focused subtasks when isolated context improves quality.
- Keep reusable prefixes stable when prompt caching matters and place volatile input later.

## Anti-Patterns

- Contradictory instructions: define precedence or remove the conflict.
- Applying every prompting technique: add only techniques tied to a requirement or observed failure.
- Vague shared context: state facts the model cannot reliably infer.
- Brittle prompt-level if/else trees: prefer principles and decision rules.
- Excessive "CRITICAL", "MUST", or "NEVER": reserve emphasis for true invariants.
- Inlining all possible context: use progressive disclosure and retrieval.
- Negative-only constraints: pair prohibitions with the desired alternative.
- Re-architecting a selected line: preserve the artifact's scope unless a broader defect blocks the fix.

## Decision Framework

Before writing or revising:

1. What does success look like?
2. Is the target a fragment or a complete prompt?
3. Does the model lack decision-relevant context?
4. Does format need a template, schema, or example?
5. Does complexity justify sections, prompt chaining, or delegation?
6. Does an agent need autonomy, tool, confirmation, and stopping rules?
7. How will the change be validated?

## Review Checklist

- The edit matches the requested scope.
- Outcome and success criteria are explicit enough for the task.
- Context is sufficient but not bloated.
- Instructions are direct and constraints have clear alternatives.
- Output requirements are unambiguous where precision matters.
- Examples cover important variation when examples are necessary.
- Instructions do not conflict or leave precedence unclear.
- Tool and autonomy rules match task risk.
- Important behavior has a validation method.
- No technique was added without a concrete purpose.
