---
description: Show live Hybrid SAGE fleet, OpenCode runtime, Antigravity CLI, and ROI savings telemetry.
agent: build
---

Call the native `fleet_status` MCP tool (`hybrid-sage`) and summarize:
- Active fleet units & localities (`local-workhorse`, `cloud-sprinter`, `frontier-architect`)
- OpenCode CLI runtime status: configured model, context window, and slot 0 state (`IDLE` or `BUSY`), or cloud-only fallback if offline
- Antigravity CLI (`agy`) availability, shared memory graph state, and cumulative ROI savings ledger.
