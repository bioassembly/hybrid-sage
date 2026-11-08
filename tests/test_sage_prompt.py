import json
import subprocess
import sys
import unittest
from pathlib import Path


class SagePromptTests(unittest.TestCase):
    def test_prompt_discovery_and_rendering_without_changing_preferences(self):
        requests = [
            {'id': 1, 'method': 'initialize', 'params': {}},
            {'id': 2, 'method': 'prompts/list'},
            {'id': 3, 'method': 'prompts/get', 'params': {'name': 'sage', 'arguments': {'request': 'off'}}},
            {'id': 4, 'method': 'prompts/get', 'params': {'name': 'missing'}},
            {'id': 5, 'method': 'prompts/get', 'params': {'name': 'sage', 'arguments': {'request': []}}},
        ]
        server = Path(__file__).resolve().parents[1] / 'plugins/mcp_server.py'
        result = subprocess.run([sys.executable, str(server)], input='\n'.join(map(json.dumps, requests))+'\n',
                                text=True, capture_output=True, check=True, timeout=15)
        replies = {item['id']: item for item in map(json.loads, result.stdout.splitlines())}
        self.assertIn('prompts', replies[1]['result']['capabilities'])
        self.assertEqual(replies[2]['result']['prompts'][0]['name'], 'sage')
        text = replies[3]['result']['messages'][0]['content']['text']
        self.assertIn('configure_fleet', text)
        self.assertTrue(text.endswith('SAGE request: off'))
        self.assertIn('error', replies[4])
        self.assertIn('error', replies[5])
