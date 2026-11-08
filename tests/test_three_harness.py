import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "plugins"))
import mcp_core
from state_isolation import IsolatedStateMixin


class ThreeHarnessTests(IsolatedStateMixin, unittest.TestCase):
    def codex_call(self, args, process=None):
        proc = process or Mock(returncode=0, stdout="Independent finding", stderr="")
        with patch.object(mcp_core, "get_codex_runtime", return_value={"available": True, "binary": "/bin/codex"}), \
             patch.object(mcp_core.subprocess, "run", return_value=proc) as run:
            result = mcp_core.handle_consult_codex(args)
        return result, run

    def test_codex_snapshot_redacts_prompt_and_complete_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.py"
            source.write_text("# secret sk-abcdefghij1234567890abcd\ndef add(x): return x + 1\n")
            result, run = self.codex_call({"prompt": "Review add", "files": ["source.py"], "workdir": tmp})
            self.assertEqual(result["status"], "ok")
            self.assertGreater(result["redacted_findings"], 0)
            passed = run.call_args.kwargs
            self.assertNotIn("sk-abcdefghij1234567890abcd", passed["input"])
            self.assertIn("def add", passed["input"])
            self.assertNotEqual(passed["cwd"], tmp)
            self.assertEqual(passed["env"]["HYBRID_SAGE_CHILD"], "codex")
            argv = run.call_args.args[0]
            self.assertIn("--ignore-user-config", argv)
            self.assertIn("features.shell_tool=false", argv)
            self.assertIn("agents.enabled=false", argv)
            self.assertEqual(argv[argv.index("--sandbox") + 1], "read-only")
            self.assertTrue(Path(result["full_output_path"]).is_file())

    def test_codex_never_runs_when_unredacted_secret_is_blocked(self):
        result, run = self.codex_call({"prompt": "Inspect Bearer secret-token-1234567890", "redact": False})
        self.assertTrue(result["airgap_blocked"])
        run.assert_not_called()

    def test_codex_context_is_read_before_running_and_errors_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, run = self.codex_call({"prompt": "Review file", "files": ["missing.py"], "workdir": tmp})
            self.assertEqual(result["status"], "error")
            run.assert_not_called()
            path = Path(tmp) / "large.py"
            path.write_bytes(b"x" * 128001)
            result, run = self.codex_call({"prompt": "Review", "files": [str(path)]})
            self.assertEqual(result["status"], "error")
            run.assert_not_called()

    def test_codex_explicit_model_and_failure_do_not_trigger_fallback(self):
        result, run = self.codex_call({"prompt": "Review", "model_id": "chosen-model"},
                                     Mock(returncode=1, stdout="", stderr="quota exceeded"))
        self.assertEqual(result["status"], "error")
        self.assertFalse(result["fallback_invoked"])
        self.assertIn("chosen-model", run.call_args.args[0])
        self.assertEqual(run.call_count, 1)

    def test_missing_codex_is_an_explicit_error(self):
        with patch.object(mcp_core, "get_codex_runtime", return_value={"available": False}):
            self.assertEqual(mcp_core.handle_consult_codex({"prompt": "Review"})["status"], "error")

    def test_timeout_returns_error_without_second_provider(self):
        with patch.object(mcp_core, "get_codex_runtime", return_value={"available": True, "binary": "/codex"}), \
             patch.object(mcp_core.subprocess, "run", side_effect=subprocess.TimeoutExpired("codex", 10)) as run:
            result = mcp_core.handle_consult_codex({"prompt": "Review", "timeout_sec": 10})
        self.assertEqual(result["status"], "error")
        self.assertFalse(result["fallback_invoked"])
        self.assertEqual(run.call_count, 1)

    def test_recursive_delegation_is_rejected_for_every_child_harness(self):
        with patch.dict(os.environ, {"HYBRID_SAGE_CHILD": "opencode"}):
            for handler in [mcp_core.handle_delegate_local, mcp_core.handle_escalate_task, mcp_core.handle_consult_codex]:
                self.assertTrue(handler({"prompt": "Re-delegate"})["recursion_blocked"])

    def test_model_catalog_is_discovery_without_price_assertions(self):
        proc = Mock(returncode=0, stdout="opencode/candidate-free\nprovider/paid-model\n", stderr="")
        with patch.object(mcp_core, "cached_worker_models", return_value=None), \
             patch.object(mcp_core.shutil, "which", return_value="/opencode"), \
             patch.object(mcp_core.subprocess, "run", return_value=proc) as run:
            result = mcp_core.handle_list_worker_models({})
        self.assertEqual(result["free_named_candidates"], ["opencode/candidate-free"])
        self.assertFalse(result["pricing_verified"])
        self.assertEqual(run.call_args.args[0], ["/opencode", "models"])

    def test_explicit_opencode_model_bypasses_unrelated_offline_default(self):
        proc = Mock(returncode=0, stdout='{"type":"text","part":{"text":"No findings."}}', stderr="")
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(mcp_core, "select_best_local_node", return_value={"online": False}), \
             patch.object(mcp_core.shutil, "which", return_value="/opencode"), \
             patch.object(mcp_core.subprocess, "run", return_value=proc) as run, \
             patch.object(mcp_core, "worker_policy", return_value={"default_model": "opencode/candidate-free", "free_model_ids": ["opencode/candidate-free"], "max_parallel_jobs": 3, "timeout_sec": 900}), \
             patch.object(mcp_core, "record_delegation_stat"):
            result = mcp_core.handle_delegate_local({"prompt": "Review a small change", "model_id": "opencode/candidate-free", "workdir": tmp, "mode": "review"})
        self.assertEqual(result["status"], "ok")
        self.assertIn("opencode/candidate-free", run.call_args.args[0])
        self.assertIn("--standalone", run.call_args.args[0])
        self.assertEqual(run.call_args.kwargs["env"]["HYBRID_SAGE_CHILD"], "opencode")

    def test_remote_override_cannot_receive_detected_sensitive_data(self):
        with patch.object(mcp_core, "select_best_local_node", return_value={"online": False}), \
             patch.object(mcp_core.shutil, "which", return_value="/opencode"), \
             patch.object(mcp_core.subprocess, "run") as run:
            result = mcp_core.handle_delegate_local({"prompt": "Read NIK: 3201234567890001", "model_id": "remote/free", "free_only": False})
        self.assertTrue(result["airgap_blocked"])
        run.assert_not_called()

    def test_failed_opencode_does_not_overwrite_output_or_claim_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "answer.py"
            target.write_text("original\n")
            with patch("shutil.which", return_value="/mock/opencode"), patch.object(mcp_core, "select_best_local_node", return_value={"online": True, "endpoint": "opencode://cli"}), \
                 patch.object(mcp_core.subprocess, "run", return_value=Mock(returncode=1, stdout="partial garbage", stderr="provider failed")):
                result = mcp_core.handle_delegate_local({"prompt": "Write code", "workdir": tmp, "output_path": "answer.py"})
            self.assertEqual(result["status"], "error")
            self.assertEqual(target.read_text(), "original\n")

    def test_stdio_tools_discovery_includes_all_three_harnesses(self):
        repo = Path(__file__).resolve().parent.parent
        request = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}) + "\n"
        proc = subprocess.run([sys.executable, str(repo / "plugins/mcp_server.py")], input=request, capture_output=True, text=True, check=True)
        names = {tool["name"] for tool in json.loads(proc.stdout)["result"]["tools"]}
        self.assertIn("consult_codex", names)
        self.assertIn("delegate_local", names)
        self.assertIn("escalate_task", names)

    def test_free_only_blocks_non_allowlisted_model_before_execution(self):
        with patch.object(mcp_core.subprocess, "run") as run:
            result = mcp_core.handle_delegate_local({"prompt": "Implement", "model_id": "provider/paid"})
        self.assertTrue(result["free_only_blocked"])
        run.assert_not_called()

    def test_async_poll_requires_real_exit_result_and_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(mcp_core, "JOBS_DIR", Path(tmp)):
            self.assertEqual(mcp_core.poll_async_job("../../outside")["status"], "error")
            job = Path(tmp) / "job-test"
            job.mkdir()
            (job / "meta.json").write_text(json.dumps({"pid": 99999999, "log_path": str(job / "job.log")}))
            (job / "job.log").write_text("partial result")
            result = mcp_core.poll_async_job("job-test")
            self.assertEqual(result["status"], "error")
            (job / "finished.json").write_text('{"returncode":1}')
            self.assertEqual(mcp_core.poll_async_job("job-test")["status"], "error")

    def test_real_worker_supervisor_records_success_failure_and_verification(self):
        runner = Path(__file__).resolve().parent.parent / "scripts/worker-runner.py"
        with tempfile.TemporaryDirectory() as tmp, patch.object(mcp_core, "JOBS_DIR", Path(tmp)):
            for exit_code in [0, 7]:
                job = Path(tmp) / f"job-test-{exit_code}"
                job.mkdir()
                meta = {"command": [sys.executable, "-c", f"print('worker output'); raise SystemExit({exit_code})"],
                        "workdir": tmp, "timeout_sec": 10, "log_path": str(job / "job.log"),
                        "verify_command": f'{sys.executable} -c "raise SystemExit(1)"'}
                (job / "meta.json").write_text(json.dumps(meta))
                subprocess.run([sys.executable, str(runner), str(job)], check=True)
                result = mcp_core.poll_async_job(job.name)
                self.assertEqual(result["status"], "verification_failed" if exit_code == 0 else "error")
                finished = json.loads((job / "finished.json").read_text())
                self.assertEqual(finished["returncode"], exit_code)

    def test_async_concurrency_cap_is_shared_across_calls(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(mcp_core, "JOBS_DIR", Path(tmp)), \
             patch.object(mcp_core, "select_best_local_node", return_value={"online": True}), \
             patch.object(mcp_core.shutil, "which", return_value="/opencode"), \
             patch.object(mcp_core.subprocess, "Popen") as launch:
            for i in range(3):
                job = Path(tmp) / f"job-{i}"
                job.mkdir()
                (job / "meta.json").write_text(json.dumps({"pid": os.getpid()}))
            result = mcp_core.handle_delegate_local({"prompt": "Implement one thing", "async_mode": True})
            self.assertEqual(result["status"], "busy_skipped")
            launch.assert_not_called()

    def test_cached_catalog_excludes_paid_and_deprecated_models_without_running_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "models.json"
            cache.write_text(json.dumps({"opencode": {"models": {
                "good-free": {"cost": {"input": 0, "output": 0}},
                "misleading-free": {"cost": {"input": 1, "output": 0}},
                "old-free": {"status": "deprecated", "cost": {"input": 0, "output": 0}},
            }}}))
            with patch.dict(os.environ, {"HYBRID_SAGE_MODELS_CACHE": str(cache)}), patch.object(mcp_core.subprocess, "run") as run:
                result = mcp_core.handle_list_worker_models({})
            self.assertEqual(result["models"], ["opencode/good-free"])
            self.assertFalse(result["catalog"]["availability_verified"])
            run.assert_not_called()

    def test_local_only_intent_is_enforced_without_sensitive_patterns(self):
        with patch.object(mcp_core, "select_best_local_node", return_value={"online": True, "locality": "remote", "privacy_cleared": False}), \
             patch.object(mcp_core.subprocess, "run") as run:
            result = mcp_core.handle_delegate_local({"prompt": "Implement my unpublished algorithm", "require_local": True})
        self.assertTrue(result["airgap_blocked"])
        run.assert_not_called()

    def test_local_only_preserves_verified_local_model_without_hosted_default(self):
        runtime = {"online": True, "endpoint": "opencode://cli", "locality": "local", "privacy_cleared": True, "model": "local/my-model"}
        with patch.object(mcp_core, "select_best_local_node", return_value=runtime), \
             patch.object(mcp_core.subprocess, "run", return_value=Mock(returncode=0, stdout="result", stderr="")) as run:
            result = mcp_core.handle_delegate_local({"prompt": "Implement my private algorithm", "require_local": True})
        self.assertEqual(result["status"], "ok")
        self.assertNotIn("opencode/glm-5.3-flash-free", run.call_args.args[0])

    def test_async_output_path_is_rejected_instead_of_claiming_missing_file_success(self):
        with patch.object(mcp_core.subprocess, "Popen") as launch:
            result = mcp_core.handle_delegate_local({"prompt": "Implement", "async_mode": True, "output_path": "required.py"})
        self.assertEqual(result["status"], "error")
        launch.assert_not_called()

    def test_lesson_memory_and_stats_stores_are_isolated(self):
        for path in [mcp_core.LESSONS_PATH, mcp_core.SHARED_MEMORY_PATH, mcp_core.STATS_LEDGER_PATH, mcp_core.JOBS_DIR]:
            self.assertTrue(path.is_relative_to(self.state_dir))
        mcp_core.record_lesson(str(self.state_dir), "test symptom", "test command", "test invariant")
        self.assertTrue((self.state_dir / "lessons.jsonl").exists())
        self.assertTrue((self.state_dir / "memory.json").exists())

    def test_private_router_recommendation_and_cli_preserve_local_only_intent(self):
        result = mcp_core.handle_route_task({"prompt": "Implement my unpublished algorithm", "private": True})
        self.assertIn("require_local=True", result["recommended_command"])
        router = sys.modules["sage_route"]
        with patch.object(router, "probe_unit_health", return_value=(True, False, 262144)):
            decision = router.classify_task("Implement my unpublished algorithm", mcp_core.load_fleet_config(), private=True)
        with patch.object(router.subprocess, "call", return_value=0) as call:
            router.execute_decision(decision, "Implement my unpublished algorithm", [], False)
        self.assertIn("--require-local", call.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
