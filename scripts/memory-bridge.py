#!/usr/bin/env python3
"""
memory-bridge.py: Atomic, flock-protected inspector & backup manager for the shared
OpenCode + Antigravity MCP knowledge graph (`~/.config/opencode/memory.json`).

Prevents concurrent read/write corruption across parallel sessions and allows instant
CLI search across all persisted architectural facts.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

MEMORY_PATH = Path.home() / ".config" / "opencode" / "memory.json"


def load_entries_locked(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
        try:
            content = f.read().strip()
            if not content:
                return []
            # 1. Try parsing as a complete JSON document (single-line or multi-line indented)
            try:
                obj = json.loads(content)
                if isinstance(obj, dict):
                    for e in obj.get("entities", []):
                        entries.append({"type": "entity", **e})
                    for r in obj.get("relations", []):
                        entries.append({"type": "relation", **r})
                    if entries:
                        return entries
                elif isinstance(obj, list):
                    return [x for x in obj if isinstance(x, dict)]
            except json.JSONDecodeError:
                pass

            # 2. Fallback: parse line-by-line as JSON-Lines (official server-memory format)
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safe, flock-protected shared memory graph utility for OpenCode & Antigravity."
    )
    parser.add_argument(
        "action",
        choices=["status", "list", "search", "backup"],
        nargs="?",
        default="status",
        help="Action to perform on ~/.config/opencode/memory.json",
    )
    parser.add_argument("query", nargs="*", help="Search query when action is 'search'")
    args = parser.parse_args()

    if not MEMORY_PATH.exists():
        if args.action == "status":
            print(f"• Shared Memory File : {MEMORY_PATH} (not created yet — will initialize on first MCP write)")
            return 0
        print(f"Shared memory file not found at {MEMORY_PATH}", file=sys.stderr)
        return 1

    entries = load_entries_locked(MEMORY_PATH)
    entities = [e for e in entries if e.get("type") == "entity" or "entityType" in e]
    relations = [e for e in entries if e.get("type") == "relation" or "relationType" in e]

    if args.action == "status":
        sz = MEMORY_PATH.stat().st_size
        print(f"• Shared Memory File : {MEMORY_PATH} ({sz:,} bytes)")
        print(f"• Persisted Entities : {len(entities)} | Relations: {len(relations)}")
        return 0

    if args.action == "list":
        for e in entities:
            name = e.get("name", "unknown")
            etype = e.get("entityType", "unknown")
            obs = e.get("observations", [])
            print(f"▪ [{etype}] {name} ({len(obs)} observations)")
            for o in obs[:3]:
                print(f"    - {o}")
        return 0

    if args.action == "search":
        q = " ".join(args.query).lower().strip()
        if not q:
            print("Usage: sage memory search <keyword>", file=sys.stderr)
            return 1
        matches = 0
        for e in entities:
            blob = json.dumps(e).lower()
            if q in blob:
                matches += 1
                print(f"▪ [{e.get('entityType', '?')}] {e.get('name', '?')}")
                for o in e.get("observations", []):
                    if q in o.lower() or len(e.get("observations", [])) <= 3:
                        print(f"    - {o}")
        if matches == 0:
            print(f"No memory entities matching '{q}'.")
        return 0

    if args.action == "backup":
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        bak_path = MEMORY_PATH.with_name(f"memory.json.bak-{ts}")
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                shutil.copy2(MEMORY_PATH, bak_path)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        print(f"✔ Atomically backed up shared memory graph -> {bak_path}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
