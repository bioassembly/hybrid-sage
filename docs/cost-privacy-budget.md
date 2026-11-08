# Cost, privacy, and context budget

Frontier Codex/Antigravity sessions should spend their context on decomposition,
architecture, integration, and final review. Free-only OpenCode workers handle
most separable implementation/test loops and return compact previews plus local
artifacts. The frontier session reads only the evidence needed for acceptance.

`worker_policy.free_model_ids` is the operator-approved allowlist. The default
`free_only=true` rejects other models; failures never select a paid fallback.
`list_worker_models` reports cached advertised prices separately from live service
availability. Free providers may impose quotas, time limits, or change prices.
Codex consultations use subscription/API quota; Antigravity uses its own account.

Async workers are capped at three concurrent jobs and 900 seconds each by default.
Tune `max_parallel_jobs` and `timeout_sec` for the provider and host; avoid multiple
workers modifying the same files. Parent-side previews are capped at 3000 characters.
The full artifact and verification result remain available for acceptance review.

Free hosted providers are cloud inference. A CLI running locally is not evidence
that raw inputs stay on the host. Keep clinical identifiers, raw patient datasets,
and credentials with verified local providers. Pattern scans and redaction detect
some known signatures but cannot certify de-identification.

Codex consultation sends a bounded text snapshot into a tool-free child outside
the project. Antigravity plan sessions and OpenCode workers retain workspace tools;
scanning listed files does not stop those tools from opening other files. Limit
the workspace and data exposure according to the actual provider's trust boundary.
