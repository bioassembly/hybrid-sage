# Task routing

The frontier orchestrator owns decomposition, integration, final review, and the
acceptance checks. It proactively assigns separable implementation/test loops to
free-only OpenCode workers. Tasks with shared mutable state stay sequential or
use separate worktrees.

| Task | Default execution | Acceptance owner |
|---|---|---|
| Independent implementation slice | `delegate_local(mode="code", async_mode=true)` | Calling Codex/Antigravity session |
| Test implementation and iteration | `delegate_local(mode="test", async_mode=true)` | Calling frontier session verifies tests |
| Independent diff review | OpenCode `mode="review"` or `consult_codex` | Caller evaluates each finding |
| Ambiguous architecture or failed assumptions | Frontier analysis; `consult_codex` or `escalate_task` for a second opinion | Calling frontier session |
| Private genomic inputs or credentials | Verified local provider, or stop when none is available | Caller owns privacy boundary |
| Tiny coupled edit | Direct execution in current harness | Current harness |

`configs/fleet.json` declares units and capability tags, including Codex, hosted
free OpenCode workers, optional local inference, and Antigravity tiers. `route_task`
recommends a unit; it does not establish authentication, pricing, or permission.

A CLI on this machine is not evidence of local inference. Free hosted workers are
remote. The free-only allowlist prevents implicit paid fallback; cached zero-price
metadata does not establish rate limits or perpetual free access. Sensitive-data
pattern screening is heuristic and cannot establish anonymity.
