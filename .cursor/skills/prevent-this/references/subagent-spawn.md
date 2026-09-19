# Spawn parallel read-only workers

Use the platform's subagent or delegation API. Launch all workers in one parallel
batch when the tool supports it.

| Platform | Mechanism |
|----------|-----------|
| **Cursor** | `Task` tool, `subagent_type="generalPurpose"`, `readonly=true` when supported |
| **Claude Code** | `Task` / subagent tool with read-only mode when supported |
| **Codex** | Subagents or parallel worker delegation; use `$skill-name` to invoke skills |

If parallel subagents are unavailable, run reviewers sequentially and note that
in the verdict. Do not skip lenses.

Workers must not edit files. Each returns only its review in the requested format.
