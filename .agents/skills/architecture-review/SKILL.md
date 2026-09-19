---
name: architecture-review
description: Reviews architecture and module seams to find a drastically simpler design that preserves product intent. Use when explicitly invoked: /architecture-review (Cursor, Claude) or $architecture-review (Codex).
argument-hint: "Optional: branch, service, module, or system (defaults to the current branch and surrounding architecture)"
disable-model-invocation: true
---

# Architecture Review

Find the simplest architecture that preserves the author's product intent and externally observable behavior. Success means the report maps every meaningful seam, researches current alternatives, recommends one target design, and shows which modules and concepts disappear.

This is a read-only review. Do not modify code unless the user separately asks for implementation.

## Scope and invariants

Default to the current branch plus its callers, dependencies, neighboring modules, persisted state, contracts, and operational surfaces. If the user names a service, module, or system, review that instead. Inspect beyond the diff when the branch extends an existing subsystem.

First state what must survive:

- user-visible behavior and the original product idea
- public contracts and persisted data
- performance, security, compliance, and operational constraints supported by evidence

Treat those as invariants. Module boundaries, frameworks, control flow, and the existence of subsystems are open to change. If evidence is insufficient to establish an invariant, label the uncertainty and ask only when the answer would change the recommendation.

## Working vocabulary

- **Module**: anything with an interface and implementation, from a function to a service.
- **Interface**: everything callers must know, including invariants, errors, ordering, configuration, and performance.
- **Seam**: where a module's interface lives and behavior can be replaced.
- **Adapter**: an implementation that satisfies an interface at a seam.
- **Machinery**: code solving a general infrastructure problem rather than domain logic. Machinery is the main replacement target.

If the workspace has the `codebase-design` skill, use its fuller vocabulary for depth, leverage, and locality.

## Review workflow

### 1. Map the seams

For each meaningful seam, determine:

- modules on either side and the single owner of the contract
- data, control, events, errors, or state crossing it
- machinery versus domain logic
- duplicated representations or invariants
- coupling, translation, and change fan-out

Pay special attention to synchronization layers, shape translations with no deliberate owner, and workflow state spread across modules.

### 2. Name each general problem

Name machinery in standard field terminology so its established solutions become findable: templating, durable execution, scheduling, serialization, interface description, validation, authorization, state modeling, telemetry, parsing, migrations, caching, configuration, or retries.

Keep domain-specific rules bespoke unless evidence shows they are actually general machinery.

### 3. Search for the highest-leverage simplification

Evaluate options in this order:

1. Delete the machinery.
2. Use an existing repository or framework facility.
3. Adopt an established standard with generated tooling.
4. Adopt a mature library.
5. Adopt a managed service only when it lowers total operational complexity.

Also test whether the seam should exist. One authoritative contract that generates derived representations is better than a synchronizer. A seam with one adapter and no expected variation is usually indirection.

Read [`references/replacement-catalog.md`](references/replacement-catalog.md) only when its domains overlap the review. Its examples are search prompts, not default recommendations.

### 4. Research current candidates

Confirm every serious candidate in current sources:

- Check the repository's package versions and existing facilities first.
- Use official library documentation, package READMEs, and release notes for version-specific facts.
- Use Context7 MCP, web search, or other documentation tools when available for framework and SDK lookup.
- Use web research for alternative discovery, maintenance health, licensing, limits, and migration evidence when needed.
- Prefer specifications and first-party documentation over blog posts.

For each candidate, cite the version or release checked and sources for the capabilities the recommendation depends on. If a required capability cannot be verified, mark it unverified and do not rely on it.

Research independent candidates in parallel. Sequence package/version discovery before version-specific documentation lookup.

### 5. Compare total complexity

Evaluate:

- behavior fit and uncovered requirements
- adapters or extensions needed to close gaps
- dependency, runtime, build, and testing impact
- deployment, upgrades, failure modes, observability, and on-call burden
- security posture, licensing, maintenance health, lock-in, and exit path
- migration risk and incremental rollout options

Count complexity added outside the reviewed module. Prefer a small bespoke implementation when every prebuilt option adds more total complexity than it removes.

### 6. Recommend one target architecture

Choose one recommendation and one ranked runner-up. Specify:

- surviving and deleted modules
- final seams and contract owners
- expected reduction in code and concepts
- complexity added in exchange
- an incremental migration using Branch by Abstraction, Strangler Fig, or Parallel Change
- characterization tests and contract comparisons that preserve behavior

Keep the system releasable throughout migration. If bespoke remains best, state why it is small, stable, unusual, or cheaper than every verified alternative.

## High-value signals

Prioritize these:

- hand-built templating, parsing, sandboxing, auth, cryptography, scheduling, retries, durable state, serialization, validation, permission evaluation, telemetry, or migrations
- several hand-maintained representations of one contract
- an adapter or drift checker added to synchronize duplicated definitions
- workflow state and transitions with no single owner
- boolean flags allowing impossible state combinations
- reimplementation of an existing framework facility
- vendor-specific plumbing where a supported standard exists
- a branch growing a subsystem whose category is available off the shelf

These are investigation triggers, not automatic findings. The report must prove that a replacement fits better.

## Output contract

Produce these sections in order:

1. **Verdict**: one or two sentences naming what should be replaced, deleted, or retained.
2. **Preserved intent**: the invariants and any material uncertainty.
3. **Seam map**: a compact table with seam, owner, crossing, machinery/domain, and problem.
4. **Findings**: high-conviction architectural issues ordered by impact.
5. **Candidates**: ranked comparison of fit, gaps, total cost, risk, version checked, and source links.
6. **Target architecture**: surviving modules, deleted modules, final seams, and contract owners.
7. **Migration and validation**: releasable steps, migration pattern, characterization tests, and drift checks.
8. **Keep bespoke**: components that should remain and why.

Use direct, evidence-backed language. Prefer a few structural findings over local nits. Finish when all meaningful seams are accounted for, each serious external candidate is verified, and one recommendation has a concrete migration and validation path.
