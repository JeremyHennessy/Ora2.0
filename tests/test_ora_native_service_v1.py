"""Real Windows Job containment for new service slice launcher; no Worlds."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.ora_native_slice_v1 import run_slice, Limits
from experiments.ora_supervised_service_v1 import supervise


@unittest.skipUnless(os.name=='nt','Windows Job enforcement')
class NativeService(unittest.TestCase):
    def run_code(self,code,wall=3):
        return run_slice(lambda *unused:[sys.executable,'-B','-c',code],ROOT,
            Limits(memory_bytes=128*1024**2,cpu_seconds=2,processes=3,wall_seconds=wall))

    def test_success_and_outside_wall_stop(self):
        result=self.run_code('print("bounded")')
        self.assertEqual(result['exit_code'],0)
        self.assertEqual(result['output'].strip(),'bounded')
        self.assertEqual(result['usage']['active_before_close'],0)
        stopped=self.run_code('import time; time.sleep(30)',.2)
        self.assertEqual(stopped['reason'],'wall-limit')
        self.assertTrue(stopped['post_close_processes_exited'])

    def test_descendant_cannot_survive_leader_exit(self):
        result=self.run_code('import subprocess,sys; subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"])')
        self.assertTrue(result['descendant_leak'])
        self.assertEqual(result['usage']['active_before_close'],0)
        self.assertTrue(result['capture_eof'])

    def test_output_flood_is_capped(self):
        result=self.run_code('import os; os.write(1,b"x"*(2*1024**2))')
        self.assertTrue(result['output_limit_exceeded'])
        self.assertEqual(result['retained_bytes'],1024**2)
        self.assertEqual(result['usage']['active_before_close'],0)

    def test_supervisor_renews_slices_and_stops_retrying_errors(self):
        with tempfile.TemporaryDirectory() as folder:
            result=supervise(folder,seconds=2,slice_seconds=.5,max_restarts=0)
            self.assertGreaterEqual(len(result['attempts']),2)
            self.assertTrue(result['all_attempts_closed'])
            self.assertEqual(result['crash_failures'],0)
            self.assertTrue((Path(folder)/'backups/snapshot-0.sqlite3').exists())
            self.assertTrue((Path(folder)/'backups/snapshot-1.sqlite3').exists())
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder)/'inbox.json').write_text('not valid json')
            result=supervise(folder,seconds=5,slice_seconds=1,max_restarts=1)
            self.assertEqual(result['reason'],'retry-bound')
            self.assertEqual(result['crash_failures'],2)
            self.assertEqual(len(result['attempts']),2)


if __name__=='__main__': unittest.main()
