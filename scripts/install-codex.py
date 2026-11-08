#!/usr/bin/env python3
"""Register Hybrid SAGE through Codex's native config writer, preserving settings."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parent.parent
    binary = shutil.which("codex")
    if not binary:
        print("Codex CLI is not installed. Register plugins/mcp_server.py as a stdio MCP server after installation.", file=sys.stderr)
        return 1
    codex_home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    skill = Path.home() / ".agents" / "skills" / "model-router"
    target = repo / "skills" / "model-router"
    if skill.exists() or skill.is_symlink():
        if not skill.is_symlink() or skill.resolve() != target.resolve():
            print(f"Refusing to replace an unrelated skill at {skill}", file=sys.stderr)
            return 1
    cmd = [binary, "mcp", "add", "hybrid-sage", "--", sys.executable,
           str(repo / "plugins" / "mcp_server.py")]
    if args.dry_run:
        print(f"Register stdio MCP in {codex_home / 'config.toml'}; link {skill} -> {target}")
        return 0
    config = codex_home / "config.toml"
    if config.exists():
        backup = codex_home / f"config.toml.pre-hybrid-sage-{time.time_ns()}"
        shutil.copy2(config, backup)
        backup.chmod(0o600)
        print(f"Config backup: {backup}")
    proc = subprocess.run(cmd, check=False)
    if proc.returncode:
        return proc.returncode
    skill.parent.mkdir(parents=True, exist_ok=True)
    if not skill.is_symlink():
        skill.symlink_to(target, target_is_directory=True)
    print(f"Registered Hybrid SAGE in Codex; linked {skill}. Restart Codex to load it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
