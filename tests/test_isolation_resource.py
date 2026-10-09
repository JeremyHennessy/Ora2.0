"""Small meaningful guards for the new fixed pressure adapter."""
import ast
import json
import os
from pathlib import Path
import tempfile
import unittest
from experiments import isolation_resource_audit as audit
from experiments import isolation_resource_worker as adapter


class ResourceAdapterTests(unittest.TestCase):
    def test_audit_imports_no_producer(self):
        imports=[n for n in ast.walk(ast.parse(Path(audit.__file__).read_text(encoding='utf-8'))) if isinstance(n,ast.ImportFrom) and n.module.startswith('experiments')]
        self.assertEqual([(n.module,[x.name for x in n.names]) for n in imports],[('experiments',['isolation_world_audit'])])

    def test_pressure_rejected_on_resume(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORA_TEST_TEMP')) as folder:
            path=Path(folder)
            (path/'request.json').write_text(json.dumps(dict(world_id='fixed',revision='a'*40,resume=True,case='cpu')),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'never repeats'): adapter.main(path)
            self.assertFalse((path/'world-started').exists())

    @unittest.skipIf(os.name=='nt','Non-Windows fail-closed guard')
    def test_non_windows_refuses_before_output(self):
        from experiments import isolation_resource
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'absent'
            with self.assertRaises(OSError): isolation_resource.run_panel(output,'a'*40)
            self.assertFalse(output.exists())
