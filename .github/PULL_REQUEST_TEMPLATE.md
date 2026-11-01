## Summary
Describe the changes to routing heuristics, configurations, or handoff scripts.

## Verification Checklist
- [ ] `python3 bin/sage-route --self-test` passes
- [ ] `bash scripts/fleet-status.sh` exits 0
- [ ] No live API keys or credentials committed (`git diff` checked)
