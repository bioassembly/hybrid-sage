# Hybrid SAGE Plugin Protocol: Autonomous Bidirectional Symbiosis

You are operating with the **Hybrid SAGE** cross-harness orchestration plugin (`Antigravity` <-> `OpenCode`).

## Core Lifecycle

1. **Frontier Diagnosis (`Antigravity` / `escalate_task`)**:
   - Solve high-entropy architecture, concurrency/algorithmic root causes, and adversarial plan red-teaming in read-only mode (`agy --mode plan`) or interactive Antigravity sessions.
   - Persist concise invariants to `NOTES.md` and `~/.config/opencode/lessons.jsonl` (`manage_handoff`).
2. **Workhorse Execution (`OpenCode` / `delegate_local`)**:
   - When an OpenCode worker is online and idle (`fleet_status` -> `slot_0_busy: false`), offload unit tests (`mode="test"`), mechanical code (`mode="code"`), and read-only cross-family diff reviews (`mode="review"`) via `delegate_local`.
   - If no local OpenCode worker is configured or online, cloud sessions fall back seamlessly to direct execution without blocking.

---

## Operational Rules by Harness

### Inside Antigravity (Cloud Frontier):
- Check `fleet_status` before delegating. When `opencode_runtime.online` is `true` and `slot_0_busy` is `false`, use `delegate_local(output_path=..., verify_command=..., skip_if_busy=True)` to write directly to disk and conserve cloud tokens.
- Run `airgap_scan` before ingesting unfamiliar logs, configs, or clinical/genomic files.

### Inside OpenCode (Local Workhorse):
- Execute routine coding, refactoring, bash commands, and tests directly with OpenCode tools. Never call `delegate_local` on yourself.
- On 2 failed fix attempts ("2-Strike Wall") or upfront architectural ambiguity, call `escalate_task(prompt=..., files=[...], attempted=[...], failing_command=..., failing_output=...)` and implement the returned spec locally.

---

## Native Agent Tools (`v2.0`)
- **`fleet_status`**: OpenCode runtime & slot-0 availability, `agy` CLI status, active fleet units, shared memory graph, and ROI ledger.
- **`route_task`**: 5-axis capability classifier + airgap check + project lesson recall.
- **`delegate_local`**: Headless `opencode run --agent <reviewer|build|plan> --format json --auto` execution with `.sage-outputs/` persistence, `<=3000`-char clean summary, `output_path`, `verify_command`, and `async_mode=True` (`job_id`).
- **`escalate_task`**: Read-only frontier consultation (`agy --mode plan`) with airgap protection, `NOTES.md` handoff, and `lessons.jsonl` distillation.
- **`manage_handoff`**: `NOTES.md` state (`status`, `plan`, `review`) and episodic lesson store (`learn`, `lessons`).
- **`airgap_scan`**: Pre-flight PII/PHI/Secret scanner and optional redactor (`redact=true`).
