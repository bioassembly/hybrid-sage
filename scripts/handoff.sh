#!/usr/bin/env bash
# handoff.sh — Safe, non-destructive cross-model handoff manager (NOTES.md).
# Automatically backs up existing NOTES.md to .sage-backups/ before writing,
# and supports direct local execution (`exec`) and verification (`verify`).

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-status}"
WORKDIR="${2:-$(pwd)}"
NOTES_FILE="${WORKDIR}/NOTES.md"
BACKUP_DIR="${WORKDIR}/.sage-backups"
TS="$(date +%Y%m%d-%H%M%S)"
ISO_TS="$(date -Iseconds)"

usage() {
    cat <<EOF
Usage: sage handoff <command> [target_dir]

Commands:
  status        Show current NOTES.md handoff state in target_dir (default: pwd)
  plan          Create an Architect -> Workhorse implementation spec (backs up existing NOTES.md)
  review        Create a Workhorse -> Architect/Sprinter 2-Strike escalation or review packet
  exec          Execute the active NOTES.md plan locally on Qwen 3.8 Flash Next via OpenCode
  verify        Extract and run the '## 3. Verification Command' block from NOTES.md
EOF
}

backup_existing() {
    if [[ -f "${NOTES_FILE}" ]] && [[ -s "${NOTES_FILE}" ]]; then
        mkdir -p "${BACKUP_DIR}"
        local bak="${BACKUP_DIR}/NOTES.${TS}.md"
        cp -p "${NOTES_FILE}" "${bak}"
        echo "✔ Backed up previous NOTES.md -> ${bak}"
    fi
}

case "${MODE}" in
    status)
        if [[ -f "${NOTES_FILE}" ]]; then
            echo "Found active handoff file: ${NOTES_FILE}"
            echo "----------------------------------------------------------------------"
            head -n 40 "${NOTES_FILE}"
        else
            echo "No NOTES.md found in ${WORKDIR}."
            echo "Run 'sage handoff plan' or 'sage handoff review' to create one."
        fi
        ;;
    plan|init-plan)
        backup_existing
        cat > "${NOTES_FILE}" <<EOF
# Cross-Model Handoff State (\`NOTES.md\`)

- **Timestamp**: ${ISO_TS}
- **Source Unit**: Architect / Sprinter Unit (e.g., \`Gemini 4 Argon\` or \`Gemini 3.8 Flash\`)
- **Target Unit**: Workhorse Unit (\`OpenCode\`)
- **Privacy Clearance**: Local-Safe

## 1. Architectural Decisions & Invariants (Locked by Architect Unit)
- [ ] Objective:
- [ ] Non-negotiable constraints:
- [ ] Files to modify (exact paths):

## 2. Step-by-Step Implementation Queue for Workhorse Unit
1. [ ] Write failing test in:
2. [ ] Implement minimal code change in:
3. [ ] Run verification command below.

## 3. Verification Command (Must exit 0 before escalation/review)
\`\`\`bash
pytest -q
\`\`\`
EOF
        echo "✔ Created Architect -> Workhorse handoff template at ${NOTES_FILE}"
        ;;
    review|init-review)
        backup_existing
        GIT_STAT=""
        if git -C "${WORKDIR}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
            GIT_STAT="$(git -C "${WORKDIR}" status --short)"
        fi
        cat > "${NOTES_FILE}" <<EOF
# Cross-Model Escalation / Review Packet (\`NOTES.md\`)

- **Timestamp**: ${ISO_TS}
- **Source Unit**: Workhorse Unit (\`Qwen 3.8 Flash Next\`)
- **Target Unit**: Sprinter / Architect Unit (for fast review, web lookup, or 2-Strike deep debug)
- **Privacy Check**: Confirm NO raw PHI, LIMS IDs, or API keys are pasted below!

## 1. Completed Work / Working Tree Status
\`\`\`text
${GIT_STAT:-No git status available}
\`\`\`

## 2. Blocker or Review Request
- **Symptom / Question**:
- **Executed Evidence / Failing Command Output**:
- **What Workhorse Unit Already Tried (max 2 attempts before escalating)**:
  1.
  2.
EOF
        echo "✔ Created Workhorse -> Architect/Sprinter escalation packet at ${NOTES_FILE}"
        ;;
    verify)
        if [[ ! -f "${NOTES_FILE}" ]]; then
            echo "Error: No ${NOTES_FILE} found to verify." >&2
            exit 1
        fi
        CMD_TO_RUN="$(python3 - "${NOTES_FILE}" <<'PYEOF'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r"##\s*3\.\s*Verification Command.*?```(?:bash|sh)?\n(.*?)```", text, re.DOTALL | re.IGNORECASE)
if m:
    lines = [ln.strip() for ln in m.group(1).splitlines() if ln.strip() and not ln.strip().startswith("#")]
    print("\n".join(lines))
PYEOF
)"
        if [[ -z "${CMD_TO_RUN}" ]]; then
            echo "Error: Could not find an executable command under '## 3. Verification Command' in ${NOTES_FILE}." >&2
            exit 1
        fi
        echo "▶ Running verification command from ${NOTES_FILE}:"
        echo "  $ ${CMD_TO_RUN}"
        (cd "${WORKDIR}" && bash -e -c "${CMD_TO_RUN}")
        ;;
    exec)
        if [[ ! -f "${NOTES_FILE}" ]]; then
            echo "Error: No ${NOTES_FILE} found in ${WORKDIR}." >&2
            exit 1
        fi
        echo "▶ Delegating ${NOTES_FILE} to Local Workhorse (Qwen 3.8 Flash Next via OpenCode)..."
        (cd "${WORKDIR}" && opencode run "Read NOTES.md carefully, execute each unchecked item in '## 2. Step-by-Step Implementation Queue', and run the command in '## 3. Verification Command' until it passes.")
        ;;
    *)
        usage
        exit 1
        ;;
esac
