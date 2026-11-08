"""Keep every harness test's mutable stores and default working directory local."""
import os
from pathlib import Path
import tempfile
from unittest.mock import patch

import mcp_core


class IsolatedStateMixin:
    def setUp(self):
        super().setUp()
        temp = tempfile.TemporaryDirectory(prefix="hybrid-sage-test-state-")
        self.addCleanup(temp.cleanup)
        self.state_dir = Path(temp.name)
        previous_cwd = Path.cwd()
        os.chdir(self.state_dir)
        self.addCleanup(os.chdir, previous_cwd)
        for name, leaf in {
            "LESSONS_PATH": "lessons.jsonl",
            "SHARED_MEMORY_PATH": "memory.json",
            "STATS_LEDGER_PATH": "stats.jsonl",
            "JOBS_DIR": "jobs",
        }.items():
            patcher = patch.object(mcp_core, name, self.state_dir / leaf)
            patcher.start()
            self.addCleanup(patcher.stop)
