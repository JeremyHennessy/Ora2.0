import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from experiments import world_io_panel as panel
from experiments import world_io_audit as audit

REVISION='a'*40

class WorldIOTests(unittest.TestCase):
    def test_actual_short_and_zero_writes_cannot_acknowledge_completion(self):
        with tempfile.TemporaryDirectory() as t:
            for case in ('journal-short-return','journal-zero-return','pending-short-return','pending-zero-return'):
                directory=Path(t)/case; directory.mkdir()
                command=[sys.executable,'-B','-m','experiments.world_io_fault','--case',case,'--trace-dir',str(directory),
                         '--output-dir',str(directory/'world'),'--world-id','storage02-reference','--source-revision',REVISION]
                result=subprocess.run(command,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,2,result.stderr)
                self.assertIn('Incomplete authoritative write',result.stderr)
                trace=json.loads((directory/'injection.json').read_bytes())
                self.assertEqual(trace['injections'],1)
                checkpoint=json.loads((directory/'world/checkpoint.json').read_bytes())
                self.assertEqual(checkpoint['state']['simulation_tick'],4)

    def test_full_operation_panel_independent_replay_and_false_claims(self):
        with tempfile.TemporaryDirectory() as t:
            output=Path(t)/'panel'; evidence=panel.run(output,REVISION)
            before={str(p):p.read_bytes() for p in output.rglob('*') if p.is_file()}
            report=audit.inspect(output,REVISION)
            self.assertEqual(report['direct_continuations'],13)
            self.assertEqual(report['preserved_rejections'],3)
            self.assertEqual(report['backup_continuations'],16)
            self.assertEqual(before,{str(p):p.read_bytes() for p in output.rglob('*') if p.is_file()})
            for change in ('exit','count','source','false-injection'):
                forged=copy.deepcopy(evidence)
                if change=='exit': forged['records'][0]['resume_exit']=0
                elif change=='count': forged['records'].pop()
                elif change=='source': forged['sources'][audit.FILES[0]]='0'*64
                else: forged['records'][0]['observer_read_only']=False
                (output/'panel.json').write_bytes((json.dumps(forged)+'\n').encode())
                with self.subTest(change=change),self.assertRaises(ValueError):
                    audit.inspect(output,REVISION)

if __name__=='__main__': unittest.main()
