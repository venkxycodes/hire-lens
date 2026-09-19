# Repo-intel for deslop

`repo-intel.json` is a cached static-analysis artifact (git history, AST symbols,
project metadata). Deslop uses it to prioritize files and avoid scanning the whole
repo blindly.

## Location

| Platform | Path |
|----------|------|
| Cursor (this pack) | `.cursor/repo-intel.json` |
| Claude Code (agentsys) | `.claude/repo-intel.json` |

This pack standardizes on `.cursor/repo-intel.json`.

## Generate or refresh

From the repo root:

```bash
# Via helper script (downloads agent-analyzer on first use)
bash path/to/cursor-productivity-skills/deslop/scripts/init-repo-intel.sh .

# Or directly when agent-analyzer is installed
mkdir -p .cursor
agent-analyzer repo-intel init . > .cursor/repo-intel.json
```

Re-run after large refactors or when `repo-intel status` reports staleness.

## Queries deslop uses

All queries require `--map-file .cursor/repo-intel.json`:

```bash
MAP=.cursor/repo-intel.json
agent-analyzer repo-intel query slop-fixes   --map-file "$MAP" .
agent-analyzer repo-intel query slop-targets --map-file "$MAP" . --limit 20
agent-analyzer repo-intel query test-gaps    --map-file "$MAP" .
agent-analyzer repo-intel query hotspots     --map-file "$MAP" . --top 15
```

When `agent-analyzer` is unavailable, read `.cursor/repo-intel.json` directly for
`hotspots`, `symbols`, and `project` sections, then fall back to unguided scanning.

## Repo overlay

If `.cursor/deslop/profile.md` exists, read it before applying fixes. It lists
repo-specific false positives, verification commands, and priority scan paths.
