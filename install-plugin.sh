#!/usr/bin/env bash
# install-plugin.sh — Cross-device installer for the Hybrid SAGE Plugin.
# Dynamically resolves paths for the current device/OS and installs into both
# Antigravity (~/.gemini/) and OpenCode (~/.config/opencode/).

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_SERVER_SCRIPT="${REPO_DIR}/plugins/mcp_server.py"
chmod +x "${MCP_SERVER_SCRIPT}"

# 1. Generate machine-local mcp_config.json inside plugins/hybrid-sage/
cat > "${REPO_DIR}/plugins/hybrid-sage/mcp_config.json" <<EOF
{
  "mcpServers": {
    "hybrid-sage": {
      "command": "python3",
      "args": [
        "${MCP_SERVER_SCRIPT}"
      ]
    }
  }
}
EOF

# 2. Antigravity Plugin & Skill Installation
AGY_PLUGINS_DIR="${HOME}/.gemini/antigravity-cli/plugins"
mkdir -p "${AGY_PLUGINS_DIR}"
ln -sfn "${REPO_DIR}/plugins/hybrid-sage" "${AGY_PLUGINS_DIR}/hybrid-sage"
echo "✔ Installed Antigravity plugin: ${AGY_PLUGINS_DIR}/hybrid-sage"

mkdir -p "${HOME}/.gemini/config/skills"
ln -sfn "${REPO_DIR}/skills/model-router" "${HOME}/.gemini/config/skills/model-router"
echo "✔ Linked Antigravity skill  : ${HOME}/.gemini/config/skills/model-router"

AGY_MCP_CONFIG="${HOME}/.gemini/config/mcp_config.json"
if [[ -f "${AGY_MCP_CONFIG}" ]]; then
    python3 - "${AGY_MCP_CONFIG}" "${MCP_SERVER_SCRIPT}" <<'PYEOF'
import json, sys
cfg_path, server_script = sys.argv[1], sys.argv[2]
try:
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    servers = cfg.setdefault("mcpServers", {})
    servers["hybrid-sage"] = {
        "command": "python3",
        "args": [server_script]
    }
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")
    print(f"✔ Registered hybrid-sage MCP in Antigravity: {cfg_path}")
except Exception as e:
    print(f"Warning: could not update {cfg_path}: {e}")
PYEOF
fi

# 3. OpenCode Plugin, Skill & Slash Commands Installation
OC_PLUGINS_DIR="${HOME}/.config/opencode/plugins"
OC_COMMAND_DIR="${HOME}/.config/opencode/command"
mkdir -p "${OC_PLUGINS_DIR}" "${OC_COMMAND_DIR}" "${HOME}/.config/opencode/skills"

ln -sfn "${REPO_DIR}/.opencode/plugins/hybrid-sage.mjs" "${OC_PLUGINS_DIR}/hybrid-sage.mjs"
ln -sfn "${REPO_DIR}/skills/model-router" "${HOME}/.config/opencode/skills/model-router"
rm -f "${OC_COMMAND_DIR}/local.md"
cp -p "${REPO_DIR}/.opencode/command/"*.md "${OC_COMMAND_DIR}/"

echo "✔ Installed OpenCode plugin   : ${OC_PLUGINS_DIR}/hybrid-sage.mjs"
echo "✔ Installed OpenCode commands : /fleet, /route, /escalate"

OC_CONFIG="${HOME}/.config/opencode/opencode.json"
if [[ -f "${OC_CONFIG}" ]]; then
    python3 - "${OC_CONFIG}" "${OC_PLUGINS_DIR}/hybrid-sage.mjs" "${MCP_SERVER_SCRIPT}" <<'PYEOF'
import json, sys
cfg_path, plugin_path, server_script = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    plugins = cfg.setdefault("plugin", [])
    if plugin_path not in plugins and "hybrid-sage" not in plugins:
        plugins.append(plugin_path)
    mcp = cfg.setdefault("mcp", {})
    mcp["hybrid-sage"] = {
        "type": "local",
        "command": ["python3", server_script],
        "enabled": True
    }
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")
    print(f"✔ Registered hybrid-sage plugin & MCP in OpenCode: {cfg_path}")
except Exception as e:
    print(f"Warning: could not update {cfg_path}: {e}")
PYEOF
fi

# 4. Sync Antigravity Lazy MCP Tool Schemas (~/.gemini/antigravity-cli/mcp/hybrid-sage/*.json)
AGY_MCP_SCHEMA_DIR="${HOME}/.gemini/antigravity-cli/mcp/hybrid-sage"
mkdir -p "${AGY_MCP_SCHEMA_DIR}"
python3 - "${REPO_DIR}/plugins" "${AGY_MCP_SCHEMA_DIR}" <<'PYEOF'
import json, pathlib, sys
sys.path.insert(0, sys.argv[1])
import mcp_core
schema_dir = pathlib.Path(sys.argv[2])
for tool in mcp_core.TOOLS:
    out = {
        "name": tool["name"],
        "description": tool["description"],
        "parameters": tool["inputSchema"],
    }
    (schema_dir / f"{tool['name']}.json").write_text(json.dumps(out), encoding="utf-8")
print(f"✔ Synced {len(mcp_core.TOOLS)} MCP tool schemas to: {schema_dir}")
PYEOF

echo ""
echo "======================================================================"
echo "⚡ Hybrid SAGE v2.0 Open-Core Plugin Installed (Cross-Device Ready)"
echo "======================================================================"
