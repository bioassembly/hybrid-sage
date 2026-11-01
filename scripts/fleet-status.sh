#!/usr/bin/env bash
# fleet-status.sh — Read-only health & live slot telemetry via OpenCode & Antigravity CLIs.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FLEET_FILE="${REPO_DIR}/configs/fleet.json"

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
CYAN="\033[0;36m"
RESET="\033[0m"

echo -e "${BOLD}======================================================================${RESET}"
echo -e "${BOLD}⚡ HYBRID SAGE — LIVE FLEET, OPENCODE & BRIDGE TELEMETRY${RESET}"
echo -e "${BOLD}======================================================================${RESET}"

# 1. Configured Fleet Units (Dynamic from configs/fleet.json)
echo -e "\n${CYAN}${BOLD}[Configured Fleet Units] (${FLEET_FILE})${RESET}"
"${REPO_DIR}/bin/sage-route" --list-units | sed 's/^/  /'

# 2. Local OpenCode Runtime & FIFO Slot Status (Optional)
echo -e "\n${CYAN}${BOLD}[Workhorse Harness] OpenCode CLI${RESET}"
python3 - "${REPO_DIR}/plugins" <<'PYEOF'
import sys
sys.path.insert(0, sys.argv[1])
import mcp_core

rt = mcp_core.get_opencode_runtime()
if rt.get("online"):
    slot_str = "\033[0;33mBUSY (Generating)\033[0m" if rt.get("slot_0_busy") else "\033[0;32mIDLE (Ready for delegate_local)\033[0m"
    print(f"  • OpenCode CLI   : \033[0;32mONLINE\033[0m ({rt.get('binary')} | model={rt.get('model') or 'default'})")
    print(f"  • FIFO Slot 0    : {slot_str} | Max Context: {rt.get('max_context', 0):,} tokens")
else:
    print(f"  • OpenCode CLI   : \033[0;33mOFFLINE / CLOUD-ONLY\033[0m ({rt.get('selection_reason')})")
PYEOF

# 3. Cloud Harness & Shared Bridge State
echo -e "\n${CYAN}${BOLD}[Cloud Harness & Shared Cross-Unit Bridge]${RESET}"
if command -v agy >/dev/null 2>&1; then
    echo -e "  • Antigravity CLI: ${GREEN}INSTALLED${RESET} ($(command -v agy))"
else
    echo -e "  • Antigravity CLI: ${YELLOW}NOT IN PATH${RESET}"
fi

if [[ -f "${HOME}/.gemini/config/mcp_config.json" ]]; then
    MCP_LIST=$(python3 -c 'import json,sys; print(", ".join(json.load(open(sys.argv[1])).get("mcpServers",{}).keys()))' "${HOME}/.gemini/config/mcp_config.json" 2>/dev/null || echo "none")
    echo -e "  • AGY MCPs       : ${GREEN}${MCP_LIST}${RESET}"
fi

python3 "${REPO_DIR}/scripts/memory-bridge.py" status | sed 's/^/  /'

echo -e "${BOLD}======================================================================${RESET}"
