# Hybrid SAGE

Hybrid SAGE coordinates **Codex**, **Antigravity**, and **OpenCode** through a
shared MCP router. Frontier models plan, decompose, integrate, and review;
free-model OpenCode workers handle separable implementation and test loops.

## Default workflow

1. The frontier harness inspects `fleet_status` and `list_worker_models`, then
   divides substantial work into bounded tasks with clear file ownership.
2. It launches OpenCode workers with `delegate_local(..., async_mode=true)`.
   Up to three independent jobs can run concurrently by default. Use disjoint
   file scopes or separate worktrees to avoid conflicting edits.
3. It polls each `job_id`, reads the output artifact, checks worker verification,
   integrates the result, and runs the final checks before reporting completion.
4. Workers return results to their caller. `HYBRID_SAGE_CHILD` blocks recursive
   cross-harness delegation. Trivial edits can stay in the frontier harness.

This reduces frontier context use and quota spent on repetitive implementation.
Provider rate limits and availability still apply; “free” does not mean unlimited.

```python
# In a frontier Codex or Antigravity session:
delegate_local(prompt="Implement the parser; own src/parser.py only", mode="code", async_mode=True)
delegate_local(prompt="Add behavior tests; own tests/test_parser.py only", mode="test", async_mode=True)
# Poll both returned jobs:
delegate_local(job_id="job-...")
```

## Tools

| MCP tool | Behavior |
|---|---|
| `fleet_status` | Reports CLI presence, the configured OpenCode provider, worker policy, and bridge telemetry. Authentication and quota remain unverified until execution. |
| `list_worker_models` | Reads cached model metadata without starting OpenCode plugins; falls back to CLI discovery. Distinguishes advertised zero prices from verified service availability. |
| `delegate_local` | Runs an OpenCode implementation, test, review, or explanation task with an explicit model or the configured free worker. Returns bounded text plus an artifact; supports async polling. |
| `consult_codex` | Requests independent review or diagnosis from Codex using a scanned text snapshot. The child has no project tools, MCP servers, plugins, shell, or recursive agents. |
| `escalate_task` | Requests Antigravity plan-mode diagnosis and returns invariants for the caller to implement and verify. |
| `route_task` | Recommends a configured unit using capability tags, available CLIs, context estimates, and sensitive-data hints. It does not authorize provider cost. |
| `manage_handoff` | Exchanges project-scoped task notes and lessons. Recalled lessons must be checked against current code and tests. |
| `airgap_scan` | Screens text/files for configured secret and clinical-identifier patterns and can redact matches. It is a heuristic, not proof of anonymization. |
| `configure_fleet` | Persistent control plane: fleet status, paged model listing, exact model selection (paid/unknown prices need `allow_paid=true`), and enable/disable of new delegation. Toggles never cancel running jobs and never reset user choices. |

Codex and Antigravity can summon OpenCode workers. OpenCode and Antigravity can
consult Codex; OpenCode and Codex can consult Antigravity. Inside an OpenCode
worker, complete the assigned task directly instead of delegating to itself.

## Free worker policy

`delegate_local` is free-only by default. It uses the persisted assistant choice,
then the fleet default, unless an exact model override is supplied. A saved
`allow_paid=true` selection authorizes that model on later tasks; an explicit
`free_only=true` still forces the free allowlist. Unavailable models return an
error without substituting another model.

The initial preferred worker matches this setup's selected model,
`opencode/glm-5.3-flash-free`. The initial allowlist also includes zero-price
catalog entries for MiMo V2.6 Flash, Nemotron 3.5 Lightning, Nemotron 3.5 Super VL,
and DeepSeek V4.1 Flash. Check current provider prices before changing policy.
Cached prices and an operator allowlist cannot guarantee future prices or quota.

Override policy in gitignored `configs/fleet.local.json`, or select a full fleet
with `HYBRID_SAGE_FLEET`:

```json
{
  "worker_policy": {
    "default_model": "opencode/glm-5.3-flash-free",
    "free_model_ids": ["opencode/glm-5.3-flash-free"],
    "max_parallel_jobs": 3,
    "timeout_sec": 900
  }
}
```

A local CLI can use a remote provider. Free hosted workers are cloud inference;
private datasets require a separately configured and verified local provider.

## Persistent fleet controls

Install once with `bash install.sh`, then control SAGE in the harness chat:

```text
/sage
/sage models
/sage models opencode
/sage model opencode/glm-5.3-flash-free
/sage off
/sage on
/sage status
```

`/sage` shows current mode, selected assistant, and the Models / Select model /
On / Off choices. Controls call `configure_fleet` over the connected MCP directly;
no terminal command or standalone SAGE CLI is needed. Selection persists across
Codex, Antigravity, and OpenCode. Paid/unknown-price selections require explicit
`--allow-paid`. Off blocks new delegation without cancelling running jobs; on
retains the selected model. These settings are read on each call.

OpenCode registers a native `/sage` command. Codex's app exposes the installed
`sage` skill in its slash menu; clients that use skill mentions can invoke `$sage`
or select it via `/skills`. Antigravity loads the same control skill. The MCP also
exposes a `sage` prompt for clients with prompt support; the exact menu label is
owned by the host. MCP registration alone cannot add a custom slash menu entry
in an arbitrary client. Restart the harness once after installation to discover
new skills/commands. The installer retires only its own previous CLI symlinks.

Preferences remain in `~/.config/hybrid-sage/preferences.json` (override with
`HYBRID_SAGE_PREFERENCES`). Agents must honor the saved choice and never re-enable
hybrid mode automatically. If assistant quality is poor, use `/sage off` and the
frontier model continues directly.

The runtime matches the active provider exactly rather than probing an unrelated
configured provider. Alternate worker selection does not depend on the default
local inference endpoint being online.

Worker launches align both the operating-system working directory and logical
`PWD` with the assigned workspace, and include its absolute path in the task
contract. This avoids native CLI sessions inheriting the frontier shell's directory.

## Install

Requires Python 3.10+ and the CLIs for the harnesses you use. Codex consultation
and registration target Codex CLI 0.167+. The OpenCode plugin uses the native v2
`setup` and domain-transform API, with a v1 server adapter retained.

```bash
git clone https://github.com/bioassembly/hybrid-sage.git
cd hybrid-sage
bash install-plugin.sh
```

The installer registers Antigravity and OpenCode plugins, links the routing skill,
installs OpenCode commands, and registers Codex when present. Existing JSON configs
are backed up before edits. OpenCode v2 loads the repository as a plugin package
directory through `plugins`; old single-file registrations are migrated while
preserving unrelated entries. Restart the harnesses to load the configuration.

For Codex only:

```bash
bash install-plugin.sh --codex-only --dry-run
bash install-plugin.sh --codex-only
```

Codex registration uses its native config writer, preserves unrelated settings,
backs up `config.toml`, honors `CODEX_HOME`, and links
`~/.agents/skills/model-router`. The `codex-sage` installer's `--with-hybrid`
profile integration is an alternative.

```toml
[mcp_servers.hybrid-sage]
command = "python3"
args = ["/absolute/path/to/hybrid-sage/plugins/mcp_server.py"]
```

## Execution and privacy boundaries

For async edits, specify owned file paths in the prompt and use `verify_command`
to check required outputs and behavior. `async_mode` with the separate `output_path`
argument is explicitly rejected; synchronous `output_path` retains backup and
response-to-file handling. Local-only routing passes `require_local=true` end to
end and never substitutes a hosted free worker, even for private text without
recognized identifiers.

Async workers have persistent exit results, bounded concurrency, execution
timeouts, verification results, and output artifacts. A crashed or failed worker
is not reported as successful. Concurrent artifact names do not collide.

Codex consultation sends at most 20 text files, 128 KB per file and 256 KB total,
through a scanned snapshot. It runs outside the project with inherited user
configuration and tools disabled; authentication remains in the normal Codex home.
Codex uses your subscription/API quota. No provider fallback runs on failure.

Antigravity plan-mode and OpenCode workers can inspect the project with tools;
scanned excerpts alone are not a privacy boundary. Keep sensitive inputs on
verified local providers and keep credentials out of task notes and shared memory.

## Validate

```bash
python3 -m unittest discover -s tests -v
node --test tests/test-plugin.mjs
bash -n install-plugin.sh
```

Tests cover the stdio MCP interface, worker selection, failed execution, real
supervisor subprocesses, async polling, concurrency, Codex context isolation,
recursion guards, and OpenCode v2 registration. Model calls are mocked; passing
these tests does not establish live model availability or quotas.

See [architecture](docs/architecture.md), [routing](docs/routing-matrix.md),
[handoffs](docs/handoff-protocol.md), and [cost/privacy](docs/cost-privacy-budget.md).
Licensed under [MIT](LICENSE).
