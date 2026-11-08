#!/usr/bin/env bash
# install.sh — Install the in-harness SAGE controls and MCP integration.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "${REPO_DIR}/install-plugin.sh"

# Retire only CLI links installed by this checkout; preserve unrelated commands.
for name in sage sage-route sage-local; do
  target="${HOME}/.local/bin/$name"
  if [[ -L "$target" && "$(readlink -f "$target")" == "$REPO_DIR/bin/$name" ]]; then
    rm "$target"
  fi
done
