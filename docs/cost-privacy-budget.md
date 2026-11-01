# Quota, Latency & Privacy Economics

## 1. Workload Allocation Across Your Fleet

To get maximum ROI from both your **local GPU hardware** (Workstation RTX 3090 / LAN GPU server) and any **upstream cloud subscriptions**:

| Functional Role | Target Share of Total Tokens | Typical Tasks | Why This Ratio Works |
|---|---|---|---|
| **Workhorse (`cost_weight: 0`, Local)** | **~75%** | Code generation, unit tests, refactoring, log parsing, local vision, private data | Coding loops are token-heavy (reading files + tool outputs + test traces). Offloading 75% of raw tokens to Strata keeps your upstream cloud quota virtually untouched. |
| **Sprinter (`cost_weight: 1`, Fast Upstream)** | **~20%** *(or merged into Workhorse/Architect in a 2-unit fleet)* | Interactive multi-file edits, web search, doc lookup, parallel subagents, diff reviews | High speed, low quota weight, and native cloud tools (`search_web`, `deepwiki`, `context7`, `serena`). |
| **Architect (`cost_weight: 3`, Frontier Upstream)** | **~5%** | Architecture specs, `/red-team` critiques, OWASP audits, 2-strike bug escalations | Every token spent on your highest-tier model is high-leverage decision-making rather than boilerplate typing. |

---

## 2. Context Window & VRAM Hygiene on Local Strata

Your local Strata instance (`Qwen 3.8 Flash Next IQ3_S`) is tuned with:
- `--max-context 162000` (`int8` KV cache)
- `--kv-resident 32768` (fast VRAM-resident KV window before PCIe offloading kicks in)
- `--spec 4 --mtp` (~47 tok/s with speculative decoding)

### Golden Rules for Local Workhorse Speed:
1. **Keep active sessions under 32k tokens whenever possible**: Within the 32,768 resident KV window, Strata runs at peak ~47 tok/s. Beyond 32k, PCIe expert/KV streaming gracefully handles up to 162k tokens, but prefill latency increases.
2. **Use `compaction.prune: true` in OpenCode**: Automatically prunes stale tool outputs after 12 turns so your session stays inside the fast 32k resident window.
3. **Never run competing CUDA processes**: While Strata is serving on `:8080`, VRAM is ~23.9 / 24.6 GB utilized. Always use `bash scripts/fleet-status.sh` (read-only) before any GPU task.

---

## 3. Data Privacy Classification Matrix

| Data Type | Allowed on `privacy_cleared: true` (Local Units) | Allowed on `privacy_cleared: false` (Cloud Units) | Required Action Before Cloud Use |
|---|---|---|---|
| Public open-source code, nf-core modules | ✅ Yes | ✅ Yes | None |
| Internal pipeline logic (non-clinical) | ✅ Yes | ✅ Yes | Strip credentials and secrets |
| Anonymized QC metrics (MultiQC summary stats) | ✅ Yes | ✅ Yes | Verify sample IDs are de-identified |
| **Patient / Clinical Metadata (NIK, Name, Hospital MRN)** | ✅ **Yes (Local Only)** | ❌ **NEVER** | Must be processed 100% on local units or replaced with synthetic mock data |
| **Live API Keys, `.env`, SSH Keys, LIMS Credentials** | ✅ **Yes (Local Only)** | ❌ **NEVER** | Redact with `__API_KEY__` placeholders |
