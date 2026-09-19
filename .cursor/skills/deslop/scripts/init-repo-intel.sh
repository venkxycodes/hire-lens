#!/usr/bin/env bash
set -euo pipefail

# Generate or refresh .cursor/repo-intel.json for deslop targeting.
# Requires agent-analyzer: https://github.com/agent-sh/agent-analyzer

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
REPO_ROOT="${1:-$(pwd)}"
REPO_ROOT="$(cd "$REPO_ROOT" && pwd)"
OUT="${REPO_ROOT}/.cursor/repo-intel.json"
BIN="${AGENT_ANALYZER_BIN:-${HOME}/.agent-sh/bin/agent-analyzer}"

if [[ ! -d "${REPO_ROOT}/.git" ]]; then
  echo "error: not a git repository: ${REPO_ROOT}" >&2
  exit 1
fi

if [[ ! -x "$BIN" ]]; then
  echo "Downloading agent-analyzer to ${HOME}/.agent-sh/bin/ ..." >&2
  mkdir -p "${HOME}/.agent-sh/bin"
  ARCH="$(uname -m)"
  OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
  case "${OS}-${ARCH}" in
    darwin-arm64) ASSET="agent-analyzer-aarch64-apple-darwin.tar.gz" ;;
    darwin-x86_64) ASSET="agent-analyzer-x86_64-apple-darwin.tar.gz" ;;
    linux-x86_64) ASSET="agent-analyzer-x86_64-unknown-linux-gnu.tar.gz" ;;
    linux-aarch64|linux-arm64) ASSET="agent-analyzer-aarch64-unknown-linux-gnu.tar.gz" ;;
    *)
      echo "error: unsupported platform ${OS}-${ARCH}; install agent-analyzer manually" >&2
      exit 1
      ;;
  esac
  TAG="$(curl -fsSL https://api.github.com/repos/agent-sh/agent-analyzer/releases/latest | sed -n 's/.*"tag_name": "\([^"]*\)".*/\1/p' | head -1)"
  curl -fsSL -o /tmp/agent-analyzer.tar.gz \
    "https://github.com/agent-sh/agent-analyzer/releases/download/${TAG}/${ASSET}"
  tar xzf /tmp/agent-analyzer.tar.gz -C "${HOME}/.agent-sh/bin"
  chmod +x "${HOME}/.agent-sh/bin/agent-analyzer"
  BIN="${HOME}/.agent-sh/bin/agent-analyzer"
fi

mkdir -p "${REPO_ROOT}/.cursor"
cd "${REPO_ROOT}"
"$BIN" repo-intel init . > "${OUT}"

echo "Wrote ${OUT} ($(wc -c < "${OUT}" | tr -d ' ') bytes)"
echo "Refresh after major history changes: deslop/scripts/init-repo-intel.sh ${REPO_ROOT}"
