import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from experiments import heartbeat_world as worker
from experiments import heartbeat_world_audit as audit
from experiments import material_turnover

REVISION = 'a'*40


def tree(output, exclude_lock=False):
    return {p.name: p.read_bytes() for p in output.iterdir() if p.is_file() and (not exclude_lock or p.name != 'writer.lock')}


def cli(output, *extra):
    return [sys.executable, '-m', 'experiments.heartbeat_world', '--output-dir', str(output), '--world-id', 'reference',
            '--source-revision', REVISION, *extra]


def run(args):
    return subprocess.run(args, capture_output=True, text=True, timeout=30)


def rechain(output, frames):
    previous = '0'*64
    for index, f in enumerate(frames):
        f['seq'] = index
        f['previous_sha256'] = previous
        f['state_sha256'] = audit.digest(f['state'])
        f['frame_sha256'] = audit.digest({k: v for k, v in f.items() if k != 'frame_sha256'})
        previous = f['frame_sha256']
    (output/'frames.jsonl').write_bytes((''.join(audit.canonical(f)+'\n' for f in frames)).encode())
    (output/'checkpoint.json').write_bytes((audit.canonical(frames[-1])+'\n').encode())


class HeartbeatWorldTests(unittest.TestCase):
    def test_full_prng_history_matches_existing_reference_stream(self):
        with tempfile.TemporaryDirectory() as t:
            output = Path(t)/'reference'
            worker.run(output, 'reference', REVISION, max_ticks=128)
            checked = audit.inspect(output)
            baseline = material_turnover.simulate(1, 96)['arms'][0]
            events = [f['event'] for f in checked['frames'] if f['event'] is not None]
            self.assertEqual(events, baseline['events'])
            self.assertEqual(checked['states'][-1]['world'], baseline['terminal'])
            self.assertEqual(checked['states'][-1]['noise_cursor'], 128)
            self.assertGreater(len(checked['states'][-1]['object_history']), 32)

    def test_actual_four_boundaries_recover_full_states_and_prefix(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            worker.run(root/'reference', 'reference', REVISION)
            expected = audit.inspect(root/'reference')['states']
            for point, code in worker.FAULTS.items():
                output = root/point
                result = run(cli(output, '--fault-tick', '5', '--fault-point', point))
                self.assertEqual(result.returncode, code, result.stderr)
                prefix = (output/'frames.jsonl').read_bytes()
                before = tree(output)
                report = audit.inspect(output)['report']
                self.assertEqual(tree(output), before)
                self.assertEqual(report['verified_simulation_tick'], 4 if point == 'pre_commit' else 5)
                self.assertEqual(run(cli(output, '--resume')).returncode, 0)
                self.assertTrue((output/'frames.jsonl').read_bytes().startswith(prefix))
                self.assertEqual(audit.inspect(output)['states'], expected)

    def test_repeated_faults_and_pause_preserve_same_world(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            worker.run(root/'reference', 'reference', REVISION)
            expected = audit.inspect(root/'reference')['states']
            output = root/'multiple'
            for tick, point in ((5, 'pre_commit'), (6, 'post_journal'), (7, 'post_pending')):
                args = cli(output, '--fault-tick', str(tick), '--fault-point', point)
                if tick > 5:
                    args += ['--resume']
                self.assertEqual(run(args).returncode, worker.FAULTS[point])
            self.assertEqual(run(cli(output, '--resume')).returncode, 0)
            self.assertEqual(audit.inspect(output)['states'], expected)
            worker.run(root/'pause', 'reference', REVISION, pause_after=5)
            worker.run(root/'pause', 'reference', REVISION, resume=True)
            self.assertEqual(audit.inspect(root/'pause')['states'], expected)

    def test_zero_work_still_tracks_neutral_noise_and_terminal_idempotence(self):
        with tempfile.TemporaryDirectory() as t:
            output = Path(t)/'empty'
            worker.run(output, 'reference', REVISION, work=0, max_ticks=8)
            e = audit.inspect(output)
            self.assertEqual(e['report']['noise_cursor'], 8)
            self.assertEqual(e['report']['work'], 0)
            before = tree(output)
            worker.run(output, 'reference', REVISION, work=0, max_ticks=8, resume=True)
            self.assertEqual(tree(output), before)

    def test_missing_lagged_checkpoint_ignores_pending(self):
        with tempfile.TemporaryDirectory() as t:
            for missing in (False, True):
                output = Path(t)/str(missing)
                worker.run(output, 'reference', REVISION, pause_after=5)
                e = audit.inspect(output)
                if missing:
                    (output/'checkpoint.json').unlink()
                else:
                    (output/'checkpoint.json').write_bytes(audit.canonical(e['frames'][1]).encode())
                (output/'checkpoint.pending').write_bytes(b'untrusted')
                worker.run(output, 'reference', REVISION, resume=True)
                self.assertTrue(audit.inspect(output)['report']['checkpoint_current'])

    def test_rehashed_noise_ancestry_work_and_lifecycle_forgery_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            for name in ('random', 'cursor', 'history', 'work', 'draw', 'epoch', 'tick'):
                output = Path(t)/name
                worker.run(output, 'reference', REVISION, pause_after=5)
                frames = audit.inspect(output)['frames']
                f = frames[2]
                if name == 'random':
                    f['state']['rng_state'][1][0] += 1
                elif name == 'cursor':
                    f['state']['noise_cursor'] += 1
                elif name == 'history':
                    f['state']['object_history']['g0']['parents'] = ['fake']
                elif name == 'work':
                    f['state']['world']['W'] += 1
                elif name == 'draw':
                    f['event']['draw'][0] = (f['event']['draw'][0]+1) % 8
                elif name == 'epoch':
                    f['epoch'] += 1
                else:
                    f['state']['simulation_tick'] += 1
                rechain(output, frames)
                before = tree(output)
                with self.subTest(name=name), self.assertRaises(ValueError):
                    worker.run(output, 'reference', REVISION, resume=True)
                self.assertEqual(before, tree(output))

    def test_partial_tail_config_source_and_corrupt_snapshot_reject_without_mutation(self):
        with tempfile.TemporaryDirectory() as t:
            for name in ('tail', 'checkpoint', 'config', 'revision', 'world', 'python', 'source'):
                output = Path(t)/name
                worker.run(output, 'reference', REVISION, pause_after=5)
                kwargs = {}
                world, revision = 'reference', REVISION
                if name == 'tail':
                    with (output/'frames.jsonl').open('ab') as f:
                        f.write(b'{')
                elif name == 'checkpoint':
                    (output/'checkpoint.json').write_bytes(b'{}')
                elif name == 'config':
                    kwargs['max_ticks'] = 33
                elif name == 'revision':
                    revision = 'b'*40
                elif name == 'world':
                    world = 'replacement'
                else:
                    manifest = json.loads((output/'manifest.json').read_bytes())
                    if name == 'python':
                        manifest['identity']['python'] = '0.0.0'
                    else:
                        manifest['identity']['source_sha256'][audit.FILES[0]] = '0'*64
                    manifest['identity']['run_id'] = audit.digest({k: v for k, v in manifest['identity'].items() if k != 'run_id'})
                    (output/'manifest.json').write_bytes(audit.canonical(manifest).encode())
                before = tree(output)
                with self.subTest(name=name), self.assertRaises((ValueError, KeyError)):
                    worker.run(output, world, revision, resume=True, **kwargs)
                self.assertEqual(before, tree(output))

    def test_real_competing_resume_and_read_only_observer(self):
        with tempfile.TemporaryDirectory() as t:
            output = Path(t)/'world'
            worker.run(output, 'reference', REVISION, pause_after=5)
            with worker.writer_lock(output):
                before = tree(output, True)
                result = run(cli(output, '--resume'))
                self.assertEqual(result.returncode, 2)
                audit.inspect(output)
                self.assertEqual(tree(output, True), before)
            before = tree(output)
            audit.inspect(output)
            self.assertEqual(tree(output), before)
            worker.run(output, 'reference', REVISION, resume=True)
            self.assertEqual(audit.inspect(output)['report']['noise_cursor'], 32)


if __name__ == '__main__':
    unittest.main()
