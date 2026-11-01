# System Architecture: Hybrid SAGE (Elastic OpenCode + Antigravity Symbiosis)

## Overview

`hybrid-sage` is a cross-harness orchestration and privacy-airgap plugin connecting **OpenCode** (serving any configured local or OpenAI-compatible provider, such as `llama-server`, Ollama, LM Studio, or vLLM) with **Antigravity** (`agy`, serving upstream frontier models such as Gemini 3.8 Flash and Gemini 4 Argon). If no local OpenCode worker is running, cloud sessions degrade gracefully to cloud-only execution.

All active units are declared in [`configs/fleet.json`](../configs/fleet.json). You can scale your fleet down to **1–2 units** (cloud-only or 1 local + 1 cloud) or up to **N units** with zero code changes.

```mermaid
flowchart TD
    User["Developer / Bioinformatician"] --> Router["route_task / sage-route (configs/fleet.json)"]

    Router -->|"Tag: privacy / loop / tdd / batch"| U1["Workhorse Unit (OpenCode CLI — Cost Weight 0)"]
    Router -->|"Tag: web / interactive / subagents"| U2["Sprinter Unit (Gemini 3.8 Flash — Cost Weight 1)"]
    Router -->|"Tag: architecture / red-team / security"| U3["Architect Unit (Gemini 4 Argon — Cost Weight 3)"]

    subgraph LocalNode["Workhorse Harness (Optional Local Hardware)"]
        U1 --> OC["opencode run --agent reviewer|build|plan --format json --auto"]
    end

    subgraph CloudNode["Frontier Harness (Antigravity CLI / IDE)"]
        U2 --> AGY["agy (--mode plan for read-only escalations)"]
        U3 --> AGY
    end

    OC <-->|"Shared Knowledge Graph"| Mem[("~/.config/opencode/memory.json")]
    AGY <-->|"Shared Knowledge Graph"| Mem
    OC <-->|"Episodic Lessons & Specs"| Notes[("lessons.jsonl & Workspace NOTES.md")]
    AGY <-->|"Episodic Lessons & Specs"| Notes
```

## Adapting `configs/fleet.json` to Your Topology

### Scenario A: Cloud-Only (No Local Model Hardware)
If you run Antigravity without a local inference server:
- `fleet_status` reports `opencode_runtime.online: false`, and `delegate_local(skip_if_busy=True)` returns cleanly without blocking so all tasks execute directly on `cloud-sprinter` / `frontier-architect`.

### Scenario B: 2-Unit Topology (1 OpenCode Workhorse + 1 Upstream Cloud)
1. Set `"enabled": false` on `cloud-sprinter` (or `frontier-architect`) in `configs/fleet.json`, and add `"web"`, `"interactive"` tags to your single active cloud unit.
2. `route_task` routes private/loop work to `local-workhorse` and web/architecture/escalation work to your upstream unit.

### Scenario C: 3-Unit Default Symbiosis (`local-workhorse` + `cloud-sprinter` + `frontier-architect`)
- `local-workhorse` (`OpenCode`) handles routine coding, TDD loops, boilerplate, and cross-family diff reviews (`mode="review"`).
- `cloud-sprinter` (`Gemini 3.8 Flash`) handles interactive multi-file implementation, web search, and parallel subagents.
- `frontier-architect` (`Gemini 4 Argon`) handles greenfield architecture, `/red-team`, security audits, and 2-strike `escalate_task` diagnoses.
