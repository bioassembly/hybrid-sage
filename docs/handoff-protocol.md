# Cross-Unit Handoff & Parallel Execution Protocol

To maximize velocity without repeating context across models (whether you are running 2, 3, or N units in `configs/fleet.json`), follow these four operational workflows.

---

## Workflow 1: Top-Down "Architect-Then-Grind" (`Architect Unit` → `Workhorse Unit`)

Best for: **New features, Nextflow pipeline modules, complex refactors.**

1. **Plan & Red-Team on Your Architect Unit (e.g., `Gemini 4 Argon` in Antigravity)**:
   - Prompt the model to inspect the architecture using Serena (`get_symbols_overview`, `find_symbol`) and run `/red-team` (`skeptic` subagent).
   - Generate the handoff file (or invoke `manage_handoff(action="init-plan")` via MCP):
     ```bash
     bash /path/to/hybrid-sage/scripts/handoff.sh init-plan
     ```
   - Have the Architect unit populate `NOTES.md` with exact file paths, function signatures, edge cases, and the narrowest verification command.
2. **Execute Locally on Your Workhorse Unit (e.g., `Qwen 3.8 Flash Next` in OpenCode)**:
   - Open a terminal in the project root and run:
     ```bash
     opencode run "Read NOTES.md and execute the step-by-step implementation queue. Verify each step with the verification command."
     ```
   - Your local Workhorse writes the implementation and unit tests at ~47 tok/s on Strata (`:8080`) with zero cloud quota consumption.

---

## Workflow 2: Bottom-Up "Local Draft, Cross-Family Audit" (`Workhorse Unit` → `Sprinter / Architect Unit`)

Best for: **Routine bugfixes, data transformation scripts, Quarto reports, CRUD endpoints.**

1. **Draft & Test Locally (`Workhorse Unit`)**:
   - Do all initial coding, docstring generation, and test execution in `opencode`.
2. **Cross-Family Review Upstream (`Sprinter` or `Architect Unit`)**:
   - Before committing, switch to your upstream harness and run `/review`.
   - The read-only `reviewer` subagent audits the git diff with fresh eyes from a different model family.

---

## Workflow 3: The "2-Strike" Escalation Rule (`Workhorse Unit` → `Architect Unit`)

Local models waste time when they enter a repetitive edit-fail-edit loop. Enforce the **2-Strike Rule**:

1. **Strike 1**: Workhorse unit writes a fix; test or compiler fails.
2. **Strike 2**: Workhorse unit reads the error trace and attempts a second fix; test fails again.
3. **Immediate Escalation**:
   - Stop the local session and run (or invoke `manage_handoff(action="init-review")` via MCP):
     ```bash
     bash /path/to/hybrid-sage/scripts/handoff.sh init-review
     ```
   - Switch to your **Architect Unit** and ask it to read `NOTES.md` (or use `/boost` for deep algorithmic debugging). Once the root cause is patched, drop back to your Workhorse unit.

---

## Workflow 4: Parallel Git Worktree Execution (Simultaneous Local + Cloud)

Because your local Workhorse runs on your local GPU (`:8080`) and your upstream units run in the cloud (or on a separate LAN GPU server), **they do not compete for compute**. Run them simultaneously on the same repository using Git worktrees:

```bash
# Create an isolated worktree for local background test/refactor grinding
git worktree add ../project-local-tests -b test/coverage-grind

# Terminal 1 (Local Workhorse — Qwen 3.8 Flash Next):
cd ../project-local-tests && opencode run "Increase pytest coverage on src/parsers/ to 95%"

# Terminal 2 / IDE (Upstream Sprinter / Architect):
# Continue interactive architecture or feature work in the main worktree without file lock collisions!
```
