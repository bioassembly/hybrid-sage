# Contributing to Hybrid SAGE

Contributions to improve routing heuristics, fleet elasticity (`configs/fleet.json`), CLI tools, and cross-agent handoff protocols are welcome.

## Development Workflow

1. **Run unit and integration tests before committing**:
   ```bash
   python3 -m unittest discover -s tests -v
   python3 bin/sage-route --self-test
   ```
2. **Never commit API keys or secrets**: Use placeholder tokens (`__API_KEY__`) in `configs/*.template.json` and extract live credentials at runtime from local config files.
3. **Zero external dependencies**: Keep `plugins/mcp_core.py` and `plugins/mcp_server.py` compatible with the Python 3.10+ standard library.
