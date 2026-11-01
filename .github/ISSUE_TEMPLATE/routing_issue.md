---
name: Routing Misclassification or Fleet Issue
about: Report a task that routed to the wrong model unit or failed handoff
title: "[ROUTING] "
labels: ["triage", "routing"]
---

## Task Prompt / Scenario
Describe the task or prompt that was misrouted:

## Expected Fleet Unit (`configs/fleet.json`)
- [ ] `local-workhorse` (`OpenCode` CLI harness)
- [ ] `cloud-sprinter` (`Gemini 3.8 Flash` via Antigravity)
- [ ] `frontier-architect` (`Gemini 4 Argon` via Antigravity)
- [ ] Custom unit in `configs/fleet.json`:

## Fleet Output
Paste output of `bash scripts/fleet-status.sh`:
