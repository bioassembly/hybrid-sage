#!/usr/bin/env python3
"""Persist bounded OpenCode worker completion for MCP async polling."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import subprocess
import sys


def run(job_dir: Path) -> int:
    os.umask(0o077)
    result = {"returncode": -1}
    try:
        meta = json.loads((job_dir / "meta.json").read_text())
        with (job_dir / "job.log").open("w", encoding="utf-8") as log:
            proc = subprocess.run(meta["command"], stdout=log, stderr=subprocess.STDOUT,
                                  cwd=meta["workdir"], timeout=meta["timeout_sec"],
                                  env={**os.environ, "HYBRID_SAGE_CHILD": "opencode", "PWD": meta["workdir"]})
        result["returncode"] = proc.returncode
        if proc.returncode == 0 and meta.get("verify_command"):
            argv = shlex.split(meta["verify_command"])
            if not argv:
                raise ValueError("Empty verify_command")
            check = subprocess.run(argv, cwd=meta["workdir"], capture_output=True,
                                   text=True, timeout=120, shell=False,
                                   env={**os.environ, "PWD": meta["workdir"]})
            result["verification"] = {"command": meta["verify_command"], "passed": check.returncode == 0,
                                      "output_tail": (check.stdout + check.stderr)[-1500:]}
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        result = {"returncode": -1, "error": str(exc)}
    temp = job_dir / "finished.json.tmp"
    temp.write_text(json.dumps(result), encoding="utf-8")
    temp.replace(job_dir / "finished.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(run(Path(sys.argv[1])))
