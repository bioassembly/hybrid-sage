#!/usr/bin/env python3
"""
mcp_server.py: Atomic Hot-Reloading JSON-RPC stdio MCP server for Hybrid SAGE v2.0.

Automatically reloads `mcp_core.py` into a fresh module object whenever its
mtime changes on disk, swapping the active module reference atomically only
after `exec_module` succeeds (preventing half-initialized module corruption
during mid-write saves).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent
CORE_FILE = PLUGIN_DIR / "mcp_core.py"
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

import mcp_core as _initial_core  # noqa: E402

_ACTIVE_CORE: Any = _initial_core
_LAST_MTIME: float = CORE_FILE.stat().st_mtime if CORE_FILE.exists() else 0.0


def get_core() -> Any:
    """Atomically reload mcp_core.py if its mtime changed; retain previous module on error."""
    global _ACTIVE_CORE, _LAST_MTIME
    try:
        if not CORE_FILE.exists():
            return _ACTIVE_CORE
        cur_mtime = CORE_FILE.stat().st_mtime
        if cur_mtime != _LAST_MTIME:
            spec = importlib.util.spec_from_file_location("mcp_core", str(CORE_FILE))
            if spec and spec.loader:
                new_mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(new_mod)
                sys.modules["mcp_core"] = new_mod
                _ACTIVE_CORE = new_mod
                _LAST_MTIME = CORE_FILE.stat().st_mtime
    except Exception:
        pass
    return _ACTIVE_CORE


def send_rpc(msg: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue

        method = req.get("method", "")
        msg_id = req.get("id")
        raw_params = req.get("params")
        params = raw_params if isinstance(raw_params, dict) else {}
        core = get_core()

        if method == "initialize":
            send_rpc(
                {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": params.get("protocolVersion", "2024-11-05"),
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "hybrid-sage", "version": "3.0.0"},
                    },
                }
            )
        elif method in ("notifications/initialized", "initialized"):
            continue
        elif method == "tools/list":
            send_rpc({"jsonrpc": "2.0", "id": msg_id, "result": {"tools": core.TOOLS}})
        elif method == "tools/call":
            name = params.get("name", "")
            raw_args = params.get("arguments")
            args = raw_args if isinstance(raw_args, dict) else {}
            try:
                out = core.dispatch_tool_call(name, args)
                send_rpc(
                    {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [{"type": "text", "text": json.dumps(out, indent=2)}],
                            "isError": out.get("status") in {"error", "verification_failed"},
                        },
                    }
                )
            except Exception as exc:
                send_rpc(
                    {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [{"type": "text", "text": f"Error: {exc}"}],
                            "isError": True,
                        },
                    }
                )
        elif msg_id is not None:
            send_rpc(
                {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
