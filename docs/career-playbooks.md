# Orchestrator and worker playbooks

## Implement a feature

The frontier Codex/Antigravity session inspects the repository, defines acceptance
criteria, and separates work into small tasks. Assign each free OpenCode worker
one output contract and a disjoint set of files. Use async jobs for independent
slices; keep tightly coupled changes sequential.

Poll job status, inspect changed files and output artifacts, and resolve conflicts
in the frontier session. Worker verification is evidence, not final acceptance:
run the integration checks after assembling all slices and review the resulting
diff before committing.

## Investigate a difficult failure

Have a worker reproduce the failure and record the exact command, relevant output,
and attempted fixes. The frontier session reviews the evidence and reduces the
problem before asking `consult_codex` or `escalate_task` for an independent opinion.
Do not repeat the same unsuccessful approach indefinitely. Verify proposed causes
with a small reproduction before changing the implementation.

## Review a change

Request OpenCode `mode="review"` for a bounded diff review, or send relevant text
snapshots to `consult_codex` for independent review. Ask for concrete triggers,
consequences, file references, and evidence. The owning frontier session validates
findings against the code and decides which fixes belong in scope.

## Process scientific inputs

Inspect the actual provider locality before delegating. Free hosted models are
remote and are not suitable for unredacted private clinical inputs. Use
`require_local=true` for a verified local active provider; when none is available,
stop that delegation rather than sending sensitive data to another unit.

Keep raw inputs immutable, run small fixtures before expensive analyses, and
record tool versions, reference builds, filters, denominators, and output paths.
Only reviewed project invariants belong in durable lessons; keep sample identifiers
and credentials out of shared memory.
