---
description: Classify and route a task across your configured fleet units (privacy, context scale, runtime health, and reasoning depth).
agent: build
---

Call the native `route_task` MCP tool (`hybrid-sage`) for:

Task: $ARGUMENTS

Report:
- Recommended unit (`local-workhorse`, `cloud-sprinter`, or `frontier-architect`) and rationale
- Pre-flight airgap status (whether secrets or clinical PHI require strict local isolation)
- Any matching project-scoped lessons from `lessons.jsonl`
- Exact next step (`direct execution`, `delegate_local`, or `escalate_task`).
