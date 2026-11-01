# Hybrid SAGE

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **Hybrid SAGE (State-of-the-Art Agentic Genomics & Engineering Orchestrator)**: Bidirectional MCP router & plugin bridging **OpenCode** (local or self-hosted workhorse) and **Antigravity** (frontier cloud architect) with passive episodic lesson transfer and an integrated PII/PHI/Secret airgap firewall.

---

## 🌟 Key Capabilities (v2.0 Open-Core Plugin)

1. **6 Native Agent MCP Tools (CLI-to-CLI Symbiosis)**:
   - **`fleet_status`**: Live OpenCode CLI readiness, FIFO slot-0 idle status, configured fleet units, episodic lessons count, and cumulative ROI ledger (`tokens_offloaded`, `cloud_echo_tokens_saved`, `estimated_cloud_savings_usd`).
   - **`route_task`**: Upfront 5-axis classifier + pre-flight airgap scanner + project lesson recall determining whether a task belongs on local OpenCode or upstream Antigravity.
   - **`delegate_local`**: Offloads code generation, unit tests (`mode="test"`), docstrings, or cross-family read-only review (`mode="review"`) directly through headless **OpenCode** (`opencode run --agent reviewer|build|plan --format json --auto`) for **$0 cloud quota** with unlimited local token/reasoning budget, `output_path` direct-to-disk write, and `verify_command`.
   - **`escalate_task`**: Escalates complex architectural decisions, race conditions, or 2-strike blockers from OpenCode to **Antigravity** in strictly read-only Senior Architect mode (`agy --mode plan --model ... --print`), recording reusable invariants into `NOTES.md` and `lessons.jsonl`.
   - **`manage_handoff`**: Manages `NOTES.md` handoff specs and project-scoped episodic lessons (`action="learn"` / `action="recall"`).
   - **`airgap_scan`**: Pre-flight PII/PHI/Secret firewall scanning prompts and files for API keys, private keys, clinical identifiers (`NIK`, `MRN`), and genomic VCF headers, with prompt + file redaction (`redact=true`).
2. **Unified Harness Configuration**:
   - Local tasks execute through `opencode`, inheriting your existing `~/.config/opencode/opencode.json` provider, LSPs, skills, and permissions. Cloud escalations execute through `agy --mode plan`.
3. **Zero-Weight-Touch Passive Enhancement**:
   - Frontier diagnoses automatically distill into `flock`-protected, repo-scoped episodic lessons (`~/.config/opencode/lessons.jsonl`) injected into OpenCode's system prompt—improving local reasoning without LoRA catastrophic forgetting or quantization degradation.

---

## ⚡ Quickstart (Install as Plugin Across Devices)

```bash
git clone https://github.com/bioassembly/hybrid-sage.git
cd hybrid-sage
bash install-plugin.sh
```

Or install as a standard PEP 621 Python package:
```bash
pip install -e . --break-system-packages
```

---

## 🗂️ Repository Layout

```text
hybrid-sage/
├── .opencode/
│   ├── command/                        # OpenCode slash commands (/fleet, /route, /escalate)
│   └── plugins/hybrid-sage.mjs         # OpenCode plugin & project-scoped lesson prompt injector
├── bin/
│   ├── sage                            # Optional unified CLI wrapper
│   ├── sage-local                      # CLI bridge to headless OpenCode
│   └── sage-route                      # 5-axis capability, context & privacy classifier
├── configs/
│   └── fleet.json                      # Declarative unit topology (opencode <-> agy)
├── docs/                               # Architecture, playbooks, routing matrix & privacy budget docs
├── plugins/
│   ├── hybrid-sage/                    # Antigravity plugin manifest & Return-to-Local rules
│   ├── mcp_core.py                     # Open-Core Engine (OpenCode bridge, airgap firewall, lessons, ROI)
│   └── mcp_server.py                   # Atomic hot-reloading JSON-RPC stdio MCP server
├── scripts/                            # Handoff, status & flock-protected shared memory utilities
├── skills/model-router/SKILL.md        # Native agent routing & local OpenCode offloading skill
├── tests/test_hybrid_sage_v2.py        # Deterministic unit test suite
├── install-plugin.sh                   # Cross-device plugin installer for Antigravity & OpenCode
├── pyproject.toml                      # PEP 621 Open-Core Python package definition
└── README.md                           # Overview & quickstart
```
