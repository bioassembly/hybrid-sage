# Security Policy

## Credential & Data Privacy Rules

1. **Zero Secret Leakage**: Never commit live API keys (`strata-*`, Google AI Pro tokens, or workplace-ai keys) to git. Always use template files with `__API_KEY__` placeholders.
2. **PHI / Patient Genomics Routing**: Unanonymized patient clinical metadata, raw hospital LIMS identifiers, and embargoed sequences **must remain strictly on local units with `"privacy_cleared": true` in `configs/fleet.json` (executed locally via OpenCode)**. Never route private credentials or unanonymized clinical data to upstream cloud units.
3. **Reporting a Vulnerability**: Contact **bioassembly** via GitHub private vulnerability reporting (do not open a public issue with sensitive details).
