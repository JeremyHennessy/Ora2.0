import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from experiments import heartbeat_template as world
from experiments import world_telemetry as telemetry

REV='a'*40


class TelemetryTests(unittest.TestCase):
    def test_cached_state_must_match_its_authoritative_frame(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORA_TEST_TEMP')) as folder:
            path=Path(folder)/'world'; original=world.write_file; observations=[]
            def observe(file,frame):
                original(file,frame)
                if file.name!='checkpoint.pending' or frame['reason']!='advanced': return
                identity=json.loads((path/'manifest.json').read_bytes())['identity']
                binding=dict(pid=1,birth_filetime=1,
                    **{k:identity[k] for k in ('world_id','run_id','source_revision')})
                before=telemetry.hashes(path)
                first=telemetry.sample(path,REV,binding,observations[-1] if observations else None)
                for fields in ({'simulation_tick':0},{'simulation_tick':True},
                               {'noise_cursor':0},{'state_sha256':'0'*64}):
                    with self.subTest(tick=frame['state']['simulation_tick'],fields=fields):
                        damaged=telemetry.sample(path,REV,binding,dict(first,**fields))
                        self.assertFalse(damaged['active'])
                        self.assertEqual(damaged['status'],'history_mismatch')
                        self.assertTrue(damaged['validated'])
                same=telemetry.sample(path,REV,binding,first)
                self.assertEqual(same['status'],'awaiting_advance')
                self.assertFalse(same['active']); self.assertEqual(before,telemetry.hashes(path))
                observations.append(first)
            probe=dict(verified=True,pid=1,alive=True,birth_filetime=1)
            with patch.object(telemetry,'process_sample',return_value=probe), patch.object(world,'write_file',observe):
                world.run(path,'cache-integrity-fixture',REV,max_ticks=3)
            self.assertEqual(observations[0]['status'],'awaiting_advance')
            self.assertTrue(observations[1]['active'])
            self.assertTrue(observations[2]['active'])

    def test_recorded_never_probes_or_claims_live(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORA_TEST_TEMP')) as folder:
            path=Path(folder)/'world'; world.run(path,'recorded',REV,max_ticks=2)
            with patch.object(telemetry,'process_sample',side_effect=AssertionError('Unexpected PID probe')):
                result=telemetry.sample(path,REV)
            self.assertTrue(result['validated']); self.assertEqual(result['status'],'recorded'); self.assertFalse(result['active'])

    def test_partial_tail_returns_unknown_without_mutation(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORA_TEST_TEMP')) as folder:
            path=Path(folder)/'world'; world.run(path,'broken',REV,max_ticks=2)
            with (path/'frames.jsonl').open('ab') as stream: stream.write(b'{')
            before=telemetry.hashes(path); result=telemetry.sample(path,REV)
            self.assertFalse(result['validated']); self.assertFalse(result['active']); self.assertEqual(telemetry.hashes(path),before)

    @unittest.skipUnless(os.name=='nt','Actual Windows process identity and in-writer snapshots')
    def test_live_requires_native_identity_and_actual_state_advance(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORA_TEST_TEMP')) as folder:
            path=Path(folder)/'world'; results=[]; original=world.write_file
            def observe(file,frame):
                original(file,frame)
                if file.name!='checkpoint.pending' or frame['reason']!='advanced': return
                identity=json.loads((path/'manifest.json').read_bytes())['identity']
                binding=dict(pid=os.getpid(),birth_filetime=telemetry.process_sample(os.getpid())['birth_filetime'],
                    **{k:identity[k] for k in ('world_id','run_id','source_revision')})
                first=telemetry.sample(path,REV,binding,results[-1] if results else None)
                repeated=telemetry.sample(path,REV,binding,first)
                wrong=dict(binding,birth_filetime=binding['birth_filetime']+1)
                reused=telemetry.sample(path,REV,wrong,first)
                self.assertFalse(repeated['active']); self.assertEqual(reused['status'],'process_identity_mismatch')
                history=dict(first,frame_sha256='0'*64)
                divergent=telemetry.sample(path,REV,binding,history)
                self.assertEqual(divergent['status'],'history_mismatch'); self.assertFalse(divergent['active'])
                self.assertTrue(first['validated']); results.append(first)
            with patch.object(world,'write_file',observe): world.run(path,'finite-live-fixture',REV,max_ticks=3)
            self.assertEqual(results[0]['status'],'awaiting_advance')
            self.assertTrue(results[1]['active']); self.assertEqual(results[1]['simulation_tick'],2)
            stopped=telemetry.sample(path,REV,results[-1]['binding'],results[-1])
            self.assertEqual(stopped['status'],'stopped'); self.assertFalse(stopped['active'])
