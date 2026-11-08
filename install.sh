#!/usr/bin/env bash
# install.sh — Install the Hybrid SAGE plugin, skills, and CLI symlinks.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "${REPO_DIR}/install-plugin.sh"

LOCAL_BIN="${HOME}/.local/bin"
mkdir -p "${LOCAL_BIN}"
chmod +x "${REPO_DIR}/bin/sage" "${REPO_DIR}/bin/sage-route" "${REPO_DIR}/bin/sage-local"

ln -sfn "${REPO_DIR}/bin/sage" "${LOCAL_BIN}/sage"
ln -sfn "${REPO_DIR}/bin/sage-route" "${LOCAL_BIN}/sage-route"
ln -sfn "${REPO_DIR}/bin/sage-local" "${LOCAL_BIN}/sage-local"
