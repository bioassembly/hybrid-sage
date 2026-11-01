---
description: Escalate a 2-strike bug, subtle race condition, or architecture bottleneck to Gemini 4 Argon via escalate_task, then execute the fix locally.
---

Escalate the following task using the `escalate_task` MCP tool (`hybrid-sage`):

Task: $ARGUMENTS

Lifecycle:
1. **Pre-flight Airgap**: Ensure no unredacted credentials or clinical PHI are transmitted (`airgap_scan` runs automatically).
2. **Escalate**: Call `escalate_task(prompt="$ARGUMENTS")` (include relevant `files`, `attempted`, or `failing_command` details).
3. **Review Spec**: Read the read-only diagnosis and invariants returned by the frontier model (and written to `NOTES.md` + `lessons.jsonl`).
4. **Execute & Verify Locally**: Implement the changes directly using OpenCode tools and run verification tests until passing.
