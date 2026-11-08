"""Regression tests for persistent hybrid-mode fleet controls and CLI entry points."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "plugins"))
import mcp_core
from state_isolation import IsolatedStateMixin

REPO_ROOT = Path(__file__).resolve().parent.parent

MODELS_CACHE_FIXTURE = {
    "opencode": {
        "models": {
            "free-model": {"name": "Free Model", "cost": {"input": 0, "output": 0},
                           "limit": {"context": 131072}},
            "paid-model": {"name": "Paid Model", "cost": {"input": 0.000003, "output": 0.000015}},
            "unknown-model": {"name": "Unknown Model", "cost": {}},
            "legacy-model": {"name": "Legacy", "cost": {}, "status": "deprecated"},
        }
    },
    "antigravity": {
        "models": {
            "gemini-x": {"name": "Gemini X", "cost": {"input": 0.000001}},
        }
    },
}

FLEET_FIXTURE = {
    "worker_policy": {
        "default_model": "opencode/free-model",
        "free_model_ids": ["opencode/free-model"],
        "max_parallel_jobs": 3,
        "timeout_sec": 900,
    }
}


class FleetControlsTestCase(IsolatedStateMixin, unittest.TestCase):
    """Isolated preferences, model cache, fleet config, and harness guard."""

    def setUp(self):
        super().setUp()
        env = patch.dict(os.environ, {
            "HYBRID_SAGE_MODELS_CACHE": str(self.state_dir / "models.json"),
            "HYBRID_SAGE_FLEET": str(self.state_dir / "fleet.json"),
            # A delegated worker can inherit its parent's guard; mask it so
            # enabled-path control fixtures behave like a frontier harness.
            "HYBRID_SAGE_CHILD": "",
        })
        env.start()
        self.addCleanup(env.stop)
        (self.state_dir / "models.json").write_text(json.dumps(MODELS_CACHE_FIXTURE), encoding="utf-8")
        (self.state_dir / "fleet.json").write_text(json.dumps(FLEET_FIXTURE), encoding="utf-8")

    def no_subprocess(self):
        for name in ("run", "Popen"):
            patcher = patch.object(mcp_core.subprocess, name,
                                   side_effect=AssertionError("subprocess launched"))
            patcher.start()
            self.addCleanup(patcher.stop)

    def cli_env(self):
        env = dict(os.environ)
        env["HYBRID_SAGE_PREFERENCES"] = str(self.state_dir / "preferences.json")
        env["HYBRID_SAGE_MODELS_CACHE"] = str(self.state_dir / "models.json")
        env["HYBRID_SAGE_FLEET"] = str(self.state_dir / "fleet.json")
        env.pop("HYBRID_SAGE_CHILD", None)
        return env

    def run_cli(self, *argv):
        return subprocess.run(
            [sys.executable, str(REPO_ROOT / "bin" / "sage-control"), *argv],
            cwd=str(REPO_ROOT), env=self.cli_env(), capture_output=True, text=True, timeout=120,
        )

    def preferences(self):
        return json.loads((self.state_dir / "preferences.json").read_text(encoding="utf-8"))

    def seed_preferences(self):
        # Persist the default file so rejection paths can be asserted as unchanged.
        self.assertEqual(mcp_core.handle_configure_fleet({"action": "enable"})["status"], "ok")

    def write_completed_job(self):
        jobs = self.state_dir / "jobs"
        jid = "job-abc123"
        jdir = jobs / jid
        jdir.mkdir(parents=True, exist_ok=True)
        (jdir / "meta.json").write_text(json.dumps({
            "job_id": jid, "pid": os.getpid(), "status": "running", "start_time": time.time(),
            "model_id": "opencode/paid-model", "log_path": str(jdir / "job.log"),
        }), encoding="utf-8")
        (jdir / "job.log").write_text(
            '{"type":"text","part":{"type":"text","text":"done"}}\n', encoding="utf-8")
        (jdir / "finished.json").write_text(json.dumps({"returncode": 0}), encoding="utf-8")
        return jid


class TestPreferencePersistence(FleetControlsTestCase):

    def test_preferences_path_honors_env_override(self):
        self.assertEqual(mcp_core.preferences_path(), self.state_dir / "preferences.json")

    def test_disable_and_enable_persist_to_disk(self):
        result = mcp_core.handle_configure_fleet({"action": "disable"})
        self.assertEqual(result["status"], "ok")
        self.assertIs(result["enabled"], False)
        self.assertIs(result["running_jobs_stopped"], False)
        self.assertIs(self.preferences()["enabled"], False)
        self.assertFalse(mcp_core.read_preferences()["enabled"])

        enabled = mcp_core.handle_configure_fleet({"action": "enable"})
        self.assertIs(enabled["enabled"], True)
        self.assertIs(self.preferences()["enabled"], True)
        # The persisted shape keeps the load-time validation contract.
        prefs = self.preferences()
        self.assertIn("model_id", prefs)
        self.assertIn("allow_paid", prefs)

    def test_selected_model_survives_enable_disable_toggle(self):
        self.assertEqual(mcp_core.handle_configure_fleet(
            {"action": "select", "model_id": "opencode/free-model"})["status"], "ok")
        mcp_core.handle_configure_fleet({"action": "disable"})
        mcp_core.handle_configure_fleet({"action": "enable"})
        status = mcp_core.handle_configure_fleet({"action": "status"})
        self.assertEqual(status["model_id"], "opencode/free-model")
        self.assertIs(status["enabled"], True)


class TestModelSelection(FleetControlsTestCase):

    def test_unknown_model_id_rejected_and_nothing_persisted(self):
        self.seed_preferences()
        result = mcp_core.handle_configure_fleet({"action": "select", "model_id": "opencode/not-listed"})
        self.assertEqual(result["status"], "error")
        self.assertIn("Unknown model_id", result["error"])
        self.assertIsNone(self.preferences()["model_id"])

    def test_paid_selection_requires_explicit_allow_paid(self):
        self.seed_preferences()
        blocked = mcp_core.handle_configure_fleet({"action": "select", "model_id": "opencode/paid-model"})
        self.assertEqual(blocked["status"], "error")
        self.assertIn("allow_paid", blocked["error"])
        self.assertEqual(blocked["price_status"], "paid")
        self.assertIsNone(self.preferences()["model_id"])

        allowed = mcp_core.handle_configure_fleet(
            {"action": "select", "model_id": "opencode/paid-model", "allow_paid": True})
        self.assertEqual(allowed["status"], "ok")
        prefs = self.preferences()
        self.assertEqual(prefs["model_id"], "opencode/paid-model")
        self.assertIs(prefs["allow_paid"], True)
        self.assertEqual(prefs["selected_cost_status"], "paid")
        self.assertIs(allowed["free_only"], False)

    def test_unknown_price_selection_also_requires_allow_paid(self):
        blocked = mcp_core.handle_configure_fleet({"action": "select", "model_id": "opencode/unknown-model"})
        self.assertEqual(blocked["status"], "error")
        self.assertEqual(blocked["price_status"], "unknown")

    def test_free_selection_updates_worker_policy(self):
        result = mcp_core.handle_configure_fleet({"action": "select", "model_id": "opencode/free-model"})
        self.assertEqual(result["status"], "ok")
        policy = mcp_core.worker_policy()
        self.assertEqual(policy["default_model"], "opencode/free-model")
        self.assertIn("opencode/free-model", policy["free_model_ids"])
        self.assertIs(policy["selected_allow_paid"], False)
        # The paid fixture model never joins the allowlist on a free default.
        self.assertNotIn("opencode/paid-model", policy["free_model_ids"])

    def test_explicit_free_only_blocks_selected_paid_model_before_launch(self):
        self.assertEqual(mcp_core.handle_configure_fleet(
            {"action": "select", "model_id": "opencode/paid-model", "allow_paid": True})["status"], "ok")
        policy = mcp_core.worker_policy()
        self.assertNotIn("opencode/paid-model", policy["free_model_ids"])
        self.no_subprocess()
        result = mcp_core.handle_delegate_local(
            {"prompt": "summarize", "model_id": "opencode/paid-model", "free_only": True})
        self.assertEqual(result["status"], "error")
        self.assertTrue(result["free_only_blocked"])
        self.assertIn("free_model_ids", result["error"])


class TestDisabledModeSemantics(FleetControlsTestCase):

    def setUp(self):
        super().setUp()
        self.assertEqual(mcp_core.handle_configure_fleet({"action": "disable"})["enabled"], False)

    def test_no_subprocess_for_new_delegation_while_disabled(self):
        self.no_subprocess()
        sync = mcp_core.handle_delegate_local({"prompt": "do things"})
        async_result = mcp_core.handle_delegate_local({"prompt": "do things", "async_mode": True})
        codex = mcp_core.handle_consult_codex({"prompt": "review change"})
        escalate = mcp_core.handle_escalate_task({"prompt": "subtle race condition"})
        for result in (sync, async_result, codex, escalate):
            self.assertEqual(result["status"], "disabled")
            self.assertTrue(result["hybrid_disabled"])
            self.assertIn("can still be polled", result["message"])

    def test_polling_completed_job_works_while_disabled(self):
        jid = self.write_completed_job()
        self.no_subprocess()
        result = mcp_core.handle_delegate_local({"job_id": jid})
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["model_id"], "opencode/paid-model")
        self.assertEqual(result["response"], "done")

    def test_discovery_and_routing_still_work_while_disabled(self):
        listing = mcp_core.handle_configure_fleet({"action": "list"})
        self.assertEqual(listing["status"], "ok")
        self.assertEqual(listing["total"], 4)  # deprecated fixture entry excluded

        provider_view = mcp_core.handle_list_worker_models({"provider": "antigravity"})
        self.assertEqual(provider_view["models"], ["antigravity/gemini-x"])

        routed = mcp_core.handle_route_task({"prompt": "Write pytest tests for parser.py"})
        self.assertEqual(routed["unit_id"], "direct")
        self.assertIs(routed["hybrid_enabled"], False)


class TestRecursionGuardIsolation(FleetControlsTestCase):

    def test_inherited_child_flag_blocks_nested_delegation(self):
        os.environ["HYBRID_SAGE_CHILD"] = "opencode"
        try:
            result = mcp_core.handle_delegate_local({"prompt": "nested request"})
        finally:
            os.environ.pop("HYBRID_SAGE_CHILD", None)
        self.assertEqual(result["status"], "error")
        self.assertTrue(result["recursion_blocked"])


class TestControlCLI(FleetControlsTestCase):

    def test_hybrid_off_status_on_cycle(self):
        off = self.run_cli("hybrid", "off")
        self.assertEqual(off.returncode, 0, off.stderr)
        self.assertIn("Hybrid: off", off.stdout)
        status = self.run_cli("hybrid", "status")
        self.assertIn("Hybrid: off", status.stdout)
        self.assertIs(self.preferences()["enabled"], False)
        on = self.run_cli("hybrid", "on")
        self.assertIn("Hybrid: on", on.stdout)
        self.assertIs(self.preferences()["enabled"], True)

    def test_model_select_requires_allow_paid_then_persists_across_toggle(self):
        self.assertEqual(self.run_cli("hybrid", "on").returncode, 0)  # seeds persisted defaults
        blocked = self.run_cli("model", "opencode/paid-model")
        self.assertEqual(blocked.returncode, 1)
        error = json.loads(blocked.stdout)
        self.assertIn("allow_paid", error["error"])
        self.assertIsNone(self.preferences()["model_id"])

        allowed = self.run_cli("model", "opencode/paid-model", "--allow-paid")
        self.assertEqual(allowed.returncode, 0, allowed.stdout)
        self.assertIn("assistant: opencode/paid-model", allowed.stdout)
        self.assertIn("paid allowed: True", allowed.stdout)

        self.run_cli("hybrid", "off")
        status = self.run_cli("hybrid", "status")
        self.assertIn("Hybrid: off", status.stdout)
        # Choice, like mode, is persistent: the CLI does not re-enable or reset it.
        self.assertIn("assistant: opencode/paid-model", status.stdout)
        self.assertIn("paid allowed: True", status.stdout)

    def test_models_listing_filters_by_provider(self):
        listed = self.run_cli("models", "--provider", "opencode")
        self.assertEqual(listed.returncode, 0, listed.stderr)
        rows = {line.split("\t")[0]: line.split("\t")[1] for line in listed.stdout.splitlines() if "\t" in line}
        self.assertEqual(rows, {
            "opencode/free-model": "free",
            "opencode/paid-model": "paid",
            "opencode/unknown-model": "unknown",
        })
        self.assertIn("unverified", listed.stderr)


if __name__ == "__main__":
    unittest.main()
