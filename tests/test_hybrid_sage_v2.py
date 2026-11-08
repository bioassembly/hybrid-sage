import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "plugins"))
import mcp_core
from state_isolation import IsolatedStateMixin


class TestHybridSageV2(IsolatedStateMixin, unittest.TestCase):

    def test_redact_secrets(self):
        redacted, findings = mcp_core.redact_sensitive_text(
            "token sk-abcdefghij1234567890abcd and AKIA1234567890ABCDEF"
        )
        self.assertIn("[REDACTED_SECRET:", redacted)
        self.assertGreaterEqual(len(findings), 2)

    def test_redact_phi(self):
        redacted, findings = mcp_core.redact_sensitive_text(
            "##fileformat=VCFv4.2\nNIK: 3201234567890001\nMRN: RM-99881"
        )
        self.assertIn("[REDACTED_PHI:", redacted)
        self.assertGreaterEqual(len(findings), 3)

    def test_airgap_scan_clean_vs_sensitive(self):
        self.assertIs(
            mcp_core.handle_airgap_scan({"text": "def add(a, b): return a + b"})["safe_for_cloud"],
            True,
        )
        self.assertIs(
            mcp_core.handle_airgap_scan({"text": "Bearer secret-token-1234567890", "redact": True})["safe_for_cloud"],
            False,
        )

    def test_route_task_meta_prompt_exemption(self):
        self.assertNotEqual(
            mcp_core.handle_route_task({"prompt": "Architect a PHI firewall and secret scanner module"})["unit_id"],
            "local-workhorse",
        )
        self.assertEqual(
            mcp_core.handle_route_task({"prompt": "Parse patient record NIK: 3201234567890001"})["unit_id"],
            "local-workhorse",
        )

    def test_extract_code_block(self):
        self.assertEqual(
            mcp_core.extract_code_block("Here is code:\n" + "`" * 3 + "python\nx = 42\n" + "`" * 3),
            "x = 42\n",
        )

    def test_tools_schema_v2(self):
        self.assertEqual(
            {t["name"] for t in mcp_core.TOOLS},
            {"fleet_status", "route_task", "delegate_local", "manage_handoff", "airgap_scan", "escalate_task", "consult_codex", "list_worker_models", "configure_fleet"},
        )

    def test_opencode_runtime_inspection(self):
        node = mcp_core.get_opencode_runtime(timeout=0.3)
        self.assertIn("online", node)
        self.assertEqual(node.get("harness"), "opencode")
        self.assertEqual(node.get("endpoint"), "opencode://cli")
        self.assertIn("selection_reason", node)

    def test_escalate_task_missing_prompt(self):
        res = mcp_core.handle_escalate_task({})
        self.assertEqual(res.get("status"), "error")
        self.assertIn("Missing required argument", res.get("error", ""))

    def test_escalate_task_airgap_blocks_unredacted_secrets(self):
        res = mcp_core.handle_escalate_task({
            "prompt": "Fix bug with sk-abcdefghij1234567890abcd",
            "redact": False,
        })
        self.assertEqual(res.get("status"), "error")
        self.assertTrue(res.get("airgap_blocked"))
        self.assertIn("Airgap firewall blocked", res.get("error", ""))

        # Also verify unredacted secret in failing_output or attempted blocks egress
        res_fo = mcp_core.handle_escalate_task({
            "prompt": "Clean prompt",
            "failing_output": "Error: Auth failed for sk-abcdefghij1234567890abcd",
            "redact": False,
        })
        self.assertTrue(res_fo.get("airgap_blocked"))

        res_att = mcp_core.handle_escalate_task({
            "prompt": "Clean prompt",
            "attempted": ["Tried using Bearer secret-token-1234567890"],
            "redact": False,
        })
        self.assertTrue(res_att.get("airgap_blocked"))

    def test_escalate_task_execution_with_mock_agy(self):
        from unittest.mock import patch, MagicMock
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = "DIAGNOSIS: Root cause is off-by-one error.\nINVARIANTS: Use <= instead of <."
            mock_proc.stderr = ""

            with patch("shutil.which", return_value="/mock/bin/agy"), \
                 patch("pathlib.Path.is_file", return_value=True), \
                 patch("os.access", return_value=True), \
                 patch("subprocess.run", return_value=mock_proc):
                res = mcp_core.handle_escalate_task({
                    "prompt": "Bug in index calculation",
                    "failing_command": "pytest -q tests/test_calc.py",
                    "failing_output": "KeyError sk-12345678901234567890",
                    "attempted": "Tried fixing index",  # Test string normalization to list
                    "workdir": tmpdir,
                    "target_model": "gemini-4-argon-medium",
                    "auto_handoff": True,
                    "redact": True,
                })

            self.assertEqual(res.get("status"), "ok")
            self.assertEqual(res.get("model"), "gemini-4-argon-medium")
            self.assertIn("DIAGNOSIS", res.get("diagnosis_and_spec", ""))
            self.assertIsNotNone(res.get("airgap_warning"))
            notes_p = Path(tmpdir) / "NOTES.md"
            self.assertTrue(notes_p.exists())
            notes_text = notes_p.read_text()
            self.assertIn("DIAGNOSIS: Root cause is off-by-one error", notes_text)
            self.assertIn("## 3. Verification Command", notes_text)
            self.assertIn("pytest -q tests/test_calc.py", notes_text)

    def test_resolve_escalation_model_smart_routing(self):
        # 1. Simple questions / reviews -> gemini-3.8-flash-medium (saves frontier quota)
        model, reason = mcp_core.resolve_escalation_model(
            target_model="auto",
            prompt="Can you explain how this parser handles trailing commas?",
            attempted=[],
            has_failing_output=False,
        )
        self.assertEqual(model, "gemini-3.8-flash-medium")
        self.assertIn("Cloud Sprinter", reason)

        # 2. Strike-1 failure with no prior attempts routes to Flash (quick triage, saves Argon)
        model, reason = mcp_core.resolve_escalation_model(
            target_model="auto",
            prompt="Test failure in test_parser.py",
            attempted=[],
            has_failing_output=True,
        )
        self.assertEqual(model, "gemini-3.8-flash-medium")

        # 3. 2-strike wall (>= 2 attempts) -> gemini-4-argon-medium (Frontier Architect)
        model, reason = mcp_core.resolve_escalation_model(
            target_model="auto",
            prompt="Index error in array traversal",
            attempted=["Tried boundary check", "Tried while loop"],
            has_failing_output=True,
        )
        self.assertEqual(model, "gemini-4-argon-medium")
        self.assertIn("Frontier Architect", reason)

        # 4. Plural and derivative architecture keywords -> gemini-4-argon-medium
        for prompt_phrase in [
            "Reviewing invariants in state machine",
            "Resolving deadlocks and race conditions",
            "Designing cryptographic protocols",
            "Architectural refactoring across repositories",
            "Hit 2 strikes on this subtle bug",
        ]:
            m, r = mcp_core.resolve_escalation_model(
                target_model="auto",
                prompt=prompt_phrase,
                attempted=[],
                has_failing_output=False,
            )
            self.assertEqual(m, "gemini-4-argon-medium", f"Failed for phrase: {prompt_phrase}")
            self.assertIn("Frontier Architect", r)

        # 5. Explicit overrides with whitespace tolerance
        model_f, _ = mcp_core.resolve_escalation_model(" flash ", "hard bug", [], False)
        self.assertEqual(model_f, "gemini-3.8-flash-medium")

        model_a, _ = mcp_core.resolve_escalation_model(" argon ", "simple question", [], False)
        self.assertEqual(model_a, "gemini-4-argon-medium")

        model_custom, _ = mcp_core.resolve_escalation_model(" claude-opus-5-5-medium ", "bug", [], False)
        self.assertEqual(model_custom, "claude-opus-5-5-medium")

    def test_parse_opencode_json_output(self):
        sample_ndjson = (
            '{"type":"step_start","timestamp":100,"part":{"type":"step-start"}}\n'
            '{"type":"tool_use","timestamp":101,"part":{"type":"tool","tool":"read"}}\n'
            '{"type":"step_finish","timestamp":102,"part":{"type":"step-finish","tokens":{"input":100,"output":20,"reasoning":50}}}\n'
            '{"type":"text","timestamp":103,"part":{"type":"text","text":"No findings."}}\n'
        )
        parsed = mcp_core.parse_opencode_json_output(sample_ndjson)
        self.assertEqual(parsed["text"], "No findings.")
        self.assertEqual(parsed["tools_used"], ["read"])
        self.assertEqual(parsed["tokens"]["input"], 100)
        self.assertEqual(parsed["tokens"]["output"], 20)
        self.assertEqual(parsed["tokens"]["reasoning"], 50)

    def test_extract_clean_response_strips_think(self):
        msg = {
            "content": "<think>Let me analyze line by line...\nWait, checking further.</think>\nNo findings.",
            "reasoning_content": "Internal thought trace",
        }
        text, status = mcp_core.extract_clean_response(msg, finish_reason="stop")
        self.assertEqual(text, "No findings.")
        self.assertEqual(status, "ok")

    def test_extract_clean_response_unclosed_think_truncated(self):
        msg = {
            "content": "<think>Cut off mid-thought...",
            "reasoning_content": None,
        }
        text, status = mcp_core.extract_clean_response(msg, finish_reason="length")
        self.assertEqual(status, "truncated")
        self.assertIn("[TRUNCATED: Model reached token limit", text)

    def test_extract_clean_response_separate_reasoning_ignored(self):
        msg = {
            "content": "def add(a, b): return a + b",
            "reasoning_content": "We need to write an add function in Python",
        }
        text, status = mcp_core.extract_clean_response(msg, finish_reason="stop")
        self.assertEqual(text, "def add(a, b): return a + b")
        self.assertEqual(status, "ok")

    def test_handle_delegate_local_opencode_mocked_sync(self):
        from unittest.mock import patch, MagicMock

        sample_stdout = (
            '{"type":"tool_use","part":{"tool":"read"}}\n'
            '{"type":"text","part":{"text":"## Findings\\n- file.py:10 - missing guard - add check"}}\n'
            '{"type":"step_finish","part":{"tokens":{"input":500,"output":30}}}\n'
        )
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = sample_stdout
        mock_proc.stderr = ""

        with patch("shutil.which", return_value="/mock/opencode"), patch.object(mcp_core, "select_best_local_node", return_value={"online": True, "endpoint": "opencode://cli", "slot_0_busy": False}), patch("subprocess.run", return_value=mock_proc):
            res = mcp_core.handle_delegate_local({
                "prompt": "Review code",
                "mode": "review",
                "files": ["/tmp/test.py"],
            })
            self.assertEqual(res.get("status"), "ok")
            self.assertEqual(res.get("mode"), "review")
            self.assertEqual(res.get("agent"), "reviewer")
            self.assertIn("## Findings", res.get("response", ""))
            self.assertIn("full_output_path", res)

    def test_handle_delegate_local_async_mocked(self):
        from unittest.mock import patch, MagicMock

        mock_popen = MagicMock()
        mock_popen.pid = 99999

        with patch("shutil.which", return_value="/mock/opencode"), patch.object(mcp_core, "select_best_local_node", return_value={"online": True, "endpoint": "opencode://cli", "slot_0_busy": False}), patch("subprocess.Popen", return_value=mock_popen):
            res = mcp_core.handle_delegate_local({
                "prompt": "Long building task",
                "mode": "code",
                "async_mode": True,
            })
            self.assertEqual(res.get("status"), "async_started")
            self.assertIn("job_id", res)
            self.assertTrue(res["job_id"].startswith("job-"))

    def test_load_fleet_config_units(self):
        cfg = mcp_core.load_fleet_config()
        unit_ids = [u.get("id") for u in cfg.get("units", [])]
        self.assertIn("local-workhorse", unit_ids)
        lw = next(u for u in cfg["units"] if u.get("id") == "local-workhorse")
        self.assertEqual(lw.get("endpoint"), "opencode://cli")
        self.assertNotIn("lan_mesh", cfg)

    def test_record_and_recall_lessons(self):
        import tempfile
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmpdir:
            test_lessons = Path(tmpdir) / "lessons.jsonl"
            test_memory = Path(tmpdir) / "memory.json"
            test_repo = Path(tmpdir) / "test-repo"
            test_repo.mkdir()

            with patch.object(mcp_core, "LESSONS_PATH", test_lessons), \
                 patch.object(mcp_core, "SHARED_MEMORY_PATH", test_memory):

                rec = mcp_core.record_lesson(
                    repo_path=str(test_repo),
                    symptom="Parser fails on unquoted keys",
                    error_signature="JSONDecodeError: Expecting property name enclosed in double quotes",
                    root_cause_summary="Input is lenient JSON; use ast.literal_eval or yaml.safe_load",
                    source="unit-test",
                )
                self.assertEqual(rec["symptom"], "Parser fails on unquoted keys")
                self.assertTrue(test_lessons.exists())

                recalled = mcp_core.recall_lessons(repo_path=str(test_repo), query="JSONDecodeError property name", top_k=3)
                self.assertGreaterEqual(len(recalled), 1)
                self.assertEqual(recalled[0]["symptom"], "Parser fails on unquoted keys")

                mcp_core.record_lesson(
                    repo_path=str(test_repo),
                    symptom="Parser fails on unquoted keys",
                    error_signature="JSONDecodeError: Expecting property name enclosed in double quotes",
                    root_cause_summary="Updated: use json5 or pyyaml parser",
                    source="unit-test-update",
                )
                lines = test_lessons.read_text(encoding="utf-8").strip().splitlines()
                self.assertEqual(len(lines), 1, "Expected deduplication to keep single record for matching signature")
                self.assertIn("json5", lines[0])

    def test_manage_handoff_learn_and_recall(self):
        import tempfile
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmpdir:
            test_lessons = Path(tmpdir) / "lessons.jsonl"
            with patch.object(mcp_core, "LESSONS_PATH", test_lessons):
                res_learn = mcp_core.handle_manage_handoff({
                    "action": "learn",
                    "workdir": tmpdir,
                    "symptom": "Flock deadlock in multi-worker pipeline",
                    "error_signature": "BlockingIOError: Resource temporarily unavailable",
                    "root_cause_summary": "Use non-blocking LOCK_NB with exponential backoff",
                })
                self.assertEqual(res_learn.get("action"), "learn")
                self.assertEqual(res_learn.get("status"), "recorded")

                res_recall = mcp_core.handle_manage_handoff({
                    "action": "recall",
                    "workdir": tmpdir,
                    "query": "flock deadlock",
                })
                self.assertEqual(res_recall.get("action"), "recall")
                self.assertGreaterEqual(len(res_recall.get("matched_lessons", [])), 1)

    def test_handle_escalate_task_mode_plan(self):
        import tempfile
        from unittest.mock import patch, MagicMock

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "worker.py"
            test_file.write_text("def worker():\n    pass\n", encoding="utf-8")

            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = "Diagnosis: Race condition in worker pool.\nSpec: Add mutex lock."
            mock_proc.stderr = ""

            with patch("shutil.which", return_value="/fake/agy"), \
                 patch("pathlib.Path.is_file", return_value=True), \
                 patch("os.access", return_value=True), \
                 patch("subprocess.run", return_value=mock_proc) as mock_run:

                res = mcp_core.handle_escalate_task({
                    "prompt": "Fix race condition in worker pool",
                    "files": [str(test_file)],
                    "workdir": tmpdir,
                    "target_model": "gemini-4-argon-high",
                })
                self.assertEqual(res.get("status"), "ok")
                self.assertEqual(res.get("model"), "gemini-4-argon-high")
                self.assertIn("mutex lock", res.get("diagnosis_and_spec", ""))

                call_args = mock_run.call_args[0][0]
                self.assertIn("--mode", call_args)
                self.assertEqual(call_args[call_args.index("--mode") + 1], "plan")
                self.assertIn("--model", call_args)
                self.assertEqual(call_args[call_args.index("--model") + 1], "gemini-4-argon-high")

                prompt_arg = call_args[call_args.index("--print") + 1]
                self.assertIn("accessible in cwd", prompt_arg)

    def test_airgap_scan_redacts_file_contents(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            secret_file = Path(tmpdir) / "config.py"
            secret_file.write_text("OPENAI_KEY = 'sk-proj-1234567890abcdefghijklmnop'\n", encoding="utf-8")
            scan = mcp_core.handle_airgap_scan({
                "text": "Inspect config",
                "files": [str(secret_file)],
                "redact": True,
            })
            self.assertFalse(scan["safe_for_cloud"])
            self.assertIn(str(secret_file), scan["redacted_files"])
            self.assertNotIn("sk-proj-1234567890abcdefghijklmnop", scan["redacted_files"][str(secret_file)])

    def test_delegate_local_writes_output_path_and_avoids_shell_true(self):
        import tempfile
        from unittest.mock import patch, MagicMock

        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "gen_mod.py"
            out_file.write_text("OLD = 1\n", encoding="utf-8")

            opencode_proc = MagicMock(
                returncode=0,
                stdout='{"type":"text","part":{"type":"text","text":"```python\\nNEW = 42\\n```"}}\n',
                stderr="",
            )
            verify_proc = MagicMock(returncode=0, stdout="ok", stderr="")

            with patch("shutil.which", return_value="/mock/opencode"), patch.object(mcp_core, "select_best_local_node", return_value={"online": True, "endpoint": "opencode://cli", "slot_0_busy": False}), \
                 patch.object(mcp_core, "record_delegation_stat"), \
                 patch("subprocess.run", side_effect=[opencode_proc, verify_proc]) as mock_run:
                res = mcp_core.handle_delegate_local({
                    "prompt": "Generate module",
                    "mode": "code",
                    "workdir": tmpdir,
                    "output_path": str(out_file),
                    "verify_command": "python3 -c 'import gen_mod; assert gen_mod.NEW == 42'",
                })
                self.assertEqual(res["status"], "ok")
                self.assertTrue(res["wrote_file"])
                self.assertEqual(out_file.read_text(encoding="utf-8"), "NEW = 42\n")
                self.assertTrue(Path(res["backup_path"]).is_file())
                # Verify second subprocess.run call (verify_command) used shell=False and list argv
                verify_call = mock_run.call_args_list[1]
                self.assertIsInstance(verify_call[0][0], list)
                self.assertFalse(verify_call[1].get("shell", False))


if __name__ == "__main__":
    unittest.main()
