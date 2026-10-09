import json
import os
from pathlib import Path
import tempfile
import unittest
from experiments import launch_telemetry as launch
from experiments import launch_telemetry_worker as worker
from experiments import launch_telemetry_audit as audit
from experiments import heartbeat_template as world
from experiments import heartbeat_template_audit as replay


class LaunchTests(unittest.TestCase):
    def test_operator_identity_matches_exact_finite_world(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORA_TEST_TEMP')) as tmp:
            path=Path(tmp)/'world';revision='b'*40;world.run(path,'operator-fixture',revision,max_ticks=32)
            self.assertEqual(launch.identity('operator-fixture',revision),replay.inspect(path,revision)['manifest']['identity'])
            self.assertNotEqual(launch.identity('different',revision)['run_id'],launch.identity('operator-fixture',revision)['run_id'])

    def test_worker_refuses_extra_command_before_world_mutation(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORA_TEST_TEMP')) as tmp:
            path=Path(tmp);request=dict(world_id='x',revision='a'*40,resume=False,resource=False,command='arbitrary')
            (path/'request.json').write_text(json.dumps(request),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'Fixed finite'):worker.main(path)
            self.assertEqual({p.name for p in path.iterdir()},{'request.json'})

    def test_separate_audit_rejects_missing_full_source_denominator(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORA_TEST_TEMP')) as tmp:
            path=Path(tmp);(path/'evidence.json').write_text(json.dumps(dict(schema='launch01-v1',revision='a'*40,source_sha256={})),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'Pinned full'):audit.audit(path,launch.ROOT,'a'*40)

    @unittest.skipIf(os.name=='nt','Non-Windows fail-closed platform guard')
    def test_native_panel_cannot_start_on_other_platform(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'never-started'
            with self.assertRaises(OSError):launch.panel(path,'a'*40)
            self.assertFalse(path.exists())


if __name__=='__main__':unittest.main()
