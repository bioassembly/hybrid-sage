import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugins'))
import mcp_core
from state_isolation import IsolatedStateMixin


class FleetControlEdges(IsolatedStateMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        mcp_core.OPENCODE_CONFIG_PATH.write_text(json.dumps({'provider': {'custom': {
            'options': {'apiKey': 'private-config-sentinel'},
            'models': {'free': {'cost': {'input': 0, 'output': 0}},
                       'paid': {'cost': {'input': 1, 'output': 2}}},
        }}}))

    def test_custom_configured_models_are_listed_without_credentials(self):
        result = mcp_core.handle_list_worker_models({'provider': 'custom'})
        self.assertEqual(result['models'], ['custom/free', 'custom/paid'])
        self.assertNotIn('private-config-sentinel', json.dumps(result))
        self.assertEqual(mcp_core.handle_configure_fleet({'action': 'select', 'model_id': 'custom/free'})['status'], 'ok')

    def test_router_uses_the_persisted_assistant_instead_of_the_old_fleet_default(self):
        mcp_core.handle_configure_fleet({'action': 'select', 'model_id': 'custom/paid', 'allow_paid': True})
        with patch.object(mcp_core, 'get_opencode_runtime', return_value={
                'online': True, 'privacy_cleared': False, 'locality': 'remote'}), \
             patch.object(mcp_core.shutil, 'which', return_value='/available-cli'):
            result = mcp_core.handle_route_task({'prompt': 'Write pytest unit tests'})
        self.assertEqual(result['model_id'], 'custom/paid')
        self.assertIn('custom/paid', result['recommended_command'])
        self.assertNotIn('free_only=True', result['recommended_command'])

    def test_selected_paid_model_with_saved_consent_is_used_when_cost_flag_is_omitted(self):
        mcp_core.handle_configure_fleet({'action': 'select', 'model_id': 'custom/paid', 'allow_paid': True})
        process = Mock(returncode=0, stdout='{"type":"text","part":{"text":"result"}}\n', stderr='')
        with patch.object(mcp_core, 'select_best_local_node', return_value={'model': 'other/model', 'online': True}), \
             patch.object(mcp_core.shutil, 'which', return_value='/available-cli'), \
             patch.object(mcp_core.subprocess, 'run', return_value=process) as run:
            result = mcp_core.handle_delegate_local({'prompt': 'Implement one bounded task', 'workdir': str(self.state_dir)})
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['model_id'], 'custom/paid')
        self.assertFalse(result['free_only'])
        self.assertIn('custom/paid', run.call_args.args[0])

    def test_known_paid_catalog_entry_cannot_be_invoked_as_free_by_an_old_allowlist(self):
        fleet = Path(os.environ['HYBRID_SAGE_FLEET'])
        fleet.write_text(json.dumps({'worker_policy': {
            'default_model': 'custom/paid', 'free_model_ids': ['custom/paid'],
        }}))
        with patch.object(mcp_core.subprocess, 'run') as run:
            result = mcp_core.handle_delegate_local({'prompt': 'Task', 'free_only': True})
        self.assertTrue(result['free_only_blocked'])
        run.assert_not_called()

    def test_disabled_cli_execute_does_not_start_another_harness(self):
        mcp_core.handle_configure_fleet({'action': 'disable'})
        result = subprocess.run(['bash', str(mcp_core.REPO_ROOT / 'bin/sage'), 'route', '-x', 'Write tests'],
                                env=os.environ.copy(), capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('no delegated job started', result.stdout)
        self.assertFalse(mcp_core.JOBS_DIR.exists())

    def test_malformed_preferences_fail_closed_without_overwriting_the_file(self):
        file = mcp_core.preferences_path()
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text('{broken')
        self.assertFalse(mcp_core.read_preferences()['enabled'])
        self.assertEqual(mcp_core.handle_consult_codex({'prompt': 'Review'})['status'], 'disabled')
        self.assertEqual(mcp_core.handle_configure_fleet({'action': 'enable'})['status'], 'error')
        self.assertEqual(file.read_text(), '{broken')
