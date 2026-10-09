"""Portable rejection guards; native matrix is separately bounded and audited."""
import ast
import json
import os
from pathlib import Path
import tempfile
import unittest
from experiments import integrated_recovery_audit as audit
from experiments import integrated_recovery_worker as worker


class IntegratedTests(unittest.TestCase):
    def test_no_producer_imports_in_audit(self):
        nodes=ast.walk(ast.parse(Path(audit.__file__).read_text(encoding='utf-8')))
        imports=[(n.module,[x.name for x in n.names]) for n in nodes if isinstance(n,ast.ImportFrom) and n.module.startswith('experiments')]
        self.assertEqual(imports,[('experiments',['isolation_resource_audit'])])

    def test_fault_requires_existing_world(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORA_TEST_TEMP')) as folder:
            path=Path(folder); (path/'request.json').write_text(json.dumps(dict(world_id='fixed',revision='a'*40,resume=False,case='io-journal')),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'continuation fault'): worker.main(path)
            self.assertFalse((path/'world').exists())

    @unittest.skipIf(os.name=='nt','Non-Windows guard')
    def test_no_portable_execution_fallback(self):
        from experiments import integrated_recovery
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'absent'
            with self.assertRaises(OSError): integrated_recovery.run_panel(output,'a'*40)
            self.assertFalse(output.exists())
