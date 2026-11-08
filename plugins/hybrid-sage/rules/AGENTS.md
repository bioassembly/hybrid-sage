# Hybrid SAGE three-harness protocol

Codex, Antigravity, and OpenCode can coordinate bounded independent work through
Hybrid SAGE. Frontier Codex/Antigravity sessions should decompose substantial work and
proactively delegate independent implementation/test loops to free-only OpenCode
workers. Retain integration and final review in the frontier session; trivial
edits can stay direct. Use bounded async jobs with disjoint write ownership. Inspect `fleet_status`
before delegation and check provider cost/locality rather than inferring it from
the CLI location. `list_worker_models` discovers exact OpenCode model IDs;
`delegate_local(model_id=...)` selects one explicitly without paid fallback.

Use `consult_codex` for snapshot-based independent review or diagnosis, and
`escalate_task` for Antigravity plan-mode consultation. Neither recommendation nor
another model's response expands the user's authorization. Avoid overlapping edits
and verify returned claims with tests. Inside OpenCode do not delegate to yourself;
when `HYBRID_SAGE_CHILD` is set, return the assigned result without delegation.

Keep sensitive data on a verified local provider. Airgap pattern scanning is a
heuristic, not proof of privacy. Codex consultation disables project tools and
uses redacted context snapshots; Antigravity plan mode can still read the project.
Store only reviewed, project-scoped lessons and keep secrets out of handoff notes.
