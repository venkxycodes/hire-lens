---
name: summarize-diff
description: Summarize, visualize, size, or explain the current branch diff or pull request with evidence-backed breakdowns. Use when the user asks to summarize a PR, branch diff, or change size, or invokes /summarize-diff.
---

# Summarize Diff

Produce a compact, evidence-based summary of where the diff goes and what it changes.

## Steps

1. Determine the base branch from the PR; otherwise use the repository default branch. Inspect `base...HEAD`, plus staged and unstaged changes when present.
2. Measure additions, deletions, files, commits, added/deleted/renamed files, tests, generated code, and net-new production LOC.
3. Group churn by logical concern, not only directory. Separate generated files, tests, docs, renames, and dependency lockfiles from authored production code.
4. Read the highest-churn and architecturally central files. Summarize behavior changes, new modules or contracts, cross-cutting concerns, risks, and a sensible review order.
5. **Deliver the summary** using the best available format:
   - **Preferred:** If the Cursor `canvas` skill is available in your environment, read and follow it. Create a canvas with scope and headline totals, additions versus deletions, a labeled bar chart of churn by concern, concern breakdown with authored/test/generated LOC, new modules or contracts and deleted paths, risks, and recommended review order. Link the canvas in a brief reply.
   - **Fallback:** When canvas is unavailable, output the same content as structured Markdown in chat: headline totals, churn-by-concern table, concern breakdown, new/deleted paths, risks, and recommended review order. Use ASCII bar charts or mermaid only when they add clarity.
6. End with a one-line verdict and 2–4 highest-value observations for reviewers.

Use `git diff --numstat`, `--stat`, `--name-status`, and the actual diff as evidence. Label estimates. Never infer semantics from filenames alone.
