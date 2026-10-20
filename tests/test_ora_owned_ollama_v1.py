"""Owned endpoint refuses fallback and non-CPU model observations; no real model."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from experiments.ora_ollama_feedback_v1 import generate
from experiments.ora_owned_ollama_v1 import OwnedOllama,verify_owner,listener_pid,retain_result


class OwnedPolicy(unittest.TestCase):
    def test_unicode_log_and_physical_log_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            result=dict(output='Unicode: λ → ✓',post_close_processes_exited=True)
            retain_result(root,result)
            self.assertEqual((root/'server.log').read_text(encoding='utf8'),'Unicode: λ → ✓')
            self.assertTrue(json.loads((root/'native-result.json').read_text())['post_close_processes_exited'])
            retain_result(root,dict(output='λ'*(1024**2),post_close_processes_exited=True))
            self.assertEqual((root/'server.log').stat().st_size,1024**2)

    def test_owned_endpoint_must_authenticate_before_http(self):
        with (patch('experiments.ora_owned_ollama_v1.verify_owner',side_effect=RuntimeError('wrong birth')),
              patch('experiments.ora_ollama_feedback_v1.http.client.HTTPConnection') as http):
            with self.assertRaises(RuntimeError): generate('gpt-oss:20b','prompt',port=11435,owner_directory='fixture')
            http.assert_not_called()

    def test_arbitrary_destination_refused(self):
        with self.assertRaises(ValueError): generate('gpt-oss:20b','prompt',port=80)
        with self.assertRaises(ValueError): generate('gpt-oss:20b','prompt',port=11435)

    def test_gpu_or_second_model_stops_owned_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            server=OwnedOllama(directory,0); server.path.mkdir()
            with patch('experiments.ora_owned_ollama_v1.verify_owner'),patch(
                'experiments.ora_owned_ollama_v1.request',return_value={'models':[{'size_vram':1}]}):
                with self.assertRaises(RuntimeError): server.check_model()
            self.assertTrue((server.path/'STOP').exists())

    def test_read_only_listener_inventory_and_absent_marker(self):
        self.assertTrue(listener_pid() is None or type(listener_pid()) is int)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError): verify_owner(directory)


if __name__=='__main__': unittest.main()
