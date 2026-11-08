# Context handoffs

A handoff gives another harness enough evidence to perform one bounded task
without replaying the entire conversation. Codex, Antigravity, and OpenCode use
shared project notes and local artifacts; the owning frontier session retains
integration and acceptance responsibility.

Include the goal, relevant file paths, file ownership, assumptions, completed
attempts, exact failing or verification commands, output contract, and next step.
Avoid secrets, raw patient identifiers, and unrelated logs. Recalled lessons and
worker responses are evidence to verify against current files and tests.

## Worker handoff

Use `delegate_local(prompt=..., files=[...], workdir=..., async_mode=true)` after
choosing the free worker policy. Specify the owned files directly in the prompt.
Use `verify_command` for expected output existence and behavior; poll with the
returned `job_id`. Read the artifact, inspect the diff, and run final checks in
the owning frontier session. Async `output_path` is explicitly unsupported;
synchronous `output_path` supports backup and response-to-file handling.

## Independent diagnosis

Use `consult_codex` for a scanned, bounded text snapshot with child project tools
disabled. It does not see files that were not supplied. Use `escalate_task` for
Antigravity plan-mode diagnosis with project tools. Neither expands the user's
scope, grants permissions, or establishes that the proposed diagnosis is correct.

## Durable state

`manage_handoff` reads or writes task state in `NOTES.md` and records/recalls
project-scoped lessons. Review a root-cause claim before reusing it as an invariant.
Keep notes concise enough to resume after a session boundary and preserve unrelated
content. The legacy CLI helpers remain available through `sage handoff` and
`sage memory`; the MCP interface is the primary three-harness integration.

A delegated worker inherits `HYBRID_SAGE_CHILD` and returns its assigned result
without launching another cross-harness task. This prevents recursive escalation
loops and uncontrolled fan-out.
