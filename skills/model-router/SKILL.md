---
name: model-router
description: Dynamically route and execute tasks across your Antigravity + OpenCode fleet via native hybrid-sage MCP tools (`fleet_status`, `route_task`, `delegate_local`, `escalate_task`, `manage_handoff`, `airgap_scan`). Use when partitioning work between frontier models and local OpenCode workers, escalating 2-strike blockers, or enforcing clinical/credential airgaps.
---

# Hybrid SAGE — Bidirectional Symbiosis Protocol

Core principle: **Partition cognitive depth cleanly — frontier models solve high-entropy architecture and 2-strike root causes; OpenCode workers execute high-volume coding, tests, and cross-family reviews at $0 frontier quota; sensitive PHI/credentials stay strictly local. If no local OpenCode worker is online, cloud-only sessions degrade gracefully with zero friction.**

---

## Native MCP Tools (`hybrid-sage` v2.0)

| Tool | Purpose | When to Use |
|---|---|---|
| **`fleet_status`** | Reports live OpenCode runtime & slot-0 availability (`slot_0_busy`), `agy` CLI status, configured fleet units, shared memory graph, and ROI ledger. | Before calling `delegate_local` from cloud sessions to confirm an OpenCode worker is online and idle. |
| **`delegate_local`** | Runs headless `opencode run --agent <reviewer\|build\|plan> --format json --auto` using OpenCode's configured provider. Saves full output to `.sage-outputs/` and returns a clean `<=3000`-char summary (no `<think>` bloat). Supports `output_path`, `verify_command`, `skip_if_busy`, and `async_mode=True` (`job_id` polling). | From Antigravity cloud sessions to offload unit tests (`mode="test"`), boilerplate (`mode="code"`), or read-only cross-family diff reviews (`mode="review"`). |
| **`escalate_task`** | Consults Gemini 4 Argon / 3.8 Flash via read-only `agy --mode plan --model ... --print` with pre-flight airgap protection, records reusable invariants to `~/.config/opencode/lessons.jsonl`, and writes `NOTES.md`. | From OpenCode when hitting a 2-strike bug wall, subtle race condition, or greenfield architecture bottleneck. |
| **`route_task`** | Multi-axis task classifier (privacy airgap, context window, live worker health, loop intensity, reasoning depth) + project lesson recall. | When deciding whether a task belongs on `local-workhorse`, `cloud-sprinter`, or `frontier-architect`. |
| **`manage_handoff`** | Manages `NOTES.md` handoff specs (`status`, `plan`, `review`) and episodic lessons (`learn`, `lessons`). | To share structured specs and durable root-cause lessons across harnesses without weight modification. |
| **`airgap_scan`** | Scans text and files for API keys, private keys, clinical identifiers (`NIK`, `MRN`), and VCF headers (`redact=true` optional). | Before sending unfamiliar logs, configs, or clinical/genomic data to cloud models. |

---

## Bidirectional Workflow

1. **Cloud -> Local Offloading (Inside Antigravity)**:
   - Call `fleet_status()` first. If `opencode_runtime.online` is `false` (no local model configured/running) or `slot_0_busy` is `true`, execute directly in cloud without blocking.
   - When online and idle, call `delegate_local(prompt="...", files=[...], mode="review"|"test"|"code", output_path="...", verify_command="...", skip_if_busy=True)`.
2. **Local -> Cloud Escalation & Passive Enhancement (Inside OpenCode)**:
   - Execute routine coding, refactoring, and test loops directly in OpenCode (never call `delegate_local` on yourself).
   - On 2 failed fix attempts or upfront architectural ambiguity, call `escalate_task(...)` to get a read-only frontier diagnosis, automatically persisting the distilled invariant into `lessons.jsonl` for future sessions.
