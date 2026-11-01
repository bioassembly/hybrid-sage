# Capability-Based Task Routing Matrix

Instead of hardcoding a fixed model hierarchy, `hybrid-sage` routes tasks by **functional capability tags** defined in [`configs/fleet.json`](../configs/fleet.json), falling back cleanly when no local worker is online.

## Master Capability Routing Table

| Workflow / Task Category | Required Capability Tag(s) | Default Unit (`fleet.json`) | Rationale |
|---|---|---|---|
| **Clinical / Patient Genomics (PHI, LIMS, NIK, Hospital IDs)** | `privacy_cleared: true` | **`local-workhorse`** (`OpenCode`) | Sensitive clinical & credential data stays strictly on-premise (enforced by `airgap_scan`). |
| **Unit Tests, Pytest, `nf-test`, Nextflow `-stub-run` Loops** | `loop` / `tdd` (`cost_weight: 0`) | **`local-workhorse`** | Iterating on test suites via `delegate_local` saves frontier cloud quota. |
| **Boilerplate, CRUD, Docstrings, Type Hints, Linting Fixes** | `boilerplate` (`cost_weight: 0`) | **`local-workhorse`** | Coupled with OpenCode's LSP diagnostics (`pyright`, `eslint`, etc.), routine edits run locally at $0 cloud cost. |
| **Log Parsing, Regex, Bash/Awk Scripts, Batch Data Cleaning** | `batch` / `loop` | **`local-workhorse`** | High token volume, low architectural ambiguity. |
| **Interactive Multi-File Feature Implementation** | `interactive` | **`cloud-sprinter`** (`Gemini 3.8 Flash`) | Fast multi-tool orchestration, Serena LSP navigation, and responsive pair programming. |
| **Live Web Research, PubMed/DOI Lookup, Latest Library Docs** | `web` | **`cloud-sprinter`** (`Gemini 3.8 Flash`) | Antigravity provides native `search_web` and documentation grounding. |
| **Parallel Subagent Fan-Out (`research`, `bioinformatician`)** | `subagents` | **`cloud-sprinter`** (`Gemini 3.8 Flash`) | Cloud concurrency runs parallel subagents without local queue contention. |
| **Cross-Family Diff Review (`/review` / `mode="review"`)** | `review` | **`local-workhorse`** / **`cloud-sprinter`** | Independent cross-family review (`reviewer` agent with `permission.edit: "deny"`) catches correlated blind spots. |
| **Greenfield System Architecture & Pipeline Design** | `architecture` | **`frontier-architect`** (`Gemini 4 Argon`) | Frontier reasoning prevents structural mistakes before code is written. |
| **Adversarial Plan Red-Teaming (`/red-team` / `skeptic`)** | `red-team` | **`frontier-architect`** (`Gemini 4 Argon`) | Exposes hidden assumptions, race conditions, and edge cases pre-implementation. |
| **Security Auditing (OWASP Top 10, Auth, SQLi, Secrets)** | `security` | **`frontier-architect`** (`Gemini 4 Argon`) | High-stakes vulnerability analysis benefits from maximum frontier capability. |
| **"2-Strike" Escalation (Unresolved After 2 Local Attempts)** | `deep-debug` | **`frontier-architect`** (`Gemini 4 Argon`) | `escalate_task` resolves subtle concurrency/state bugs via read-only `agy --mode plan` and saves lessons to `lessons.jsonl`. |
| **Massive Cross-Repo Context (>160k Tokens)** | `long-context` | **`cloud-sprinter`** / **`frontier-architect`** | Long-context cloud units handle 200k–1M+ token codebase sweeps. |
