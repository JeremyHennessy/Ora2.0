import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile
from experiments import heartbeat_template as worker
from experiments import heartbeat_template_audit as heartbeat
from experiments import world_snapshot as snapshot
from experiments import world_snapshot_audit as audit

REVISION = 'a'*40
ROOT = Path(__file__).resolve().parents[1]


class WorldSnapshotTests(unittest.TestCase):
    def fixture(self, root):
        world, archive = root/'world', root/'snapshot.zip'
        worker.run(world, 'snapshot-unit', REVISION, pause_after=5)
        snapshot.pack(world, archive, REVISION)
        return world, archive

    def rewrite(self, archive, blobs, attributes=None, extra=None):
        with zipfile.ZipFile(archive, 'x') as z:
            for name, value in blobs.items():
                entry = zipfile.ZipInfo(name)
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = (attributes or {}).get(name, 0o100600 << 16)
                z.writestr(entry, value)
            if extra:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', UserWarning)
                    z.writestr(extra[0], extra[1], compress_type=zipfile.ZIP_DEFLATED)

    def test_round_trip_complete_identity_rng_provenance_and_determinism(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            world, archive = self.fixture(root)
            second = root/'second.zip'
            snapshot.pack(world, second, REVISION)
            self.assertEqual(archive.read_bytes(), second.read_bytes())
            restored = root/'restored'
            result = snapshot.unpack(archive, restored, REVISION)
            self.assertEqual(result['verified_simulation_tick'], 5)
            for name in ('manifest.json', 'frames.jsonl', 'checkpoint.json', 'writer.lock'):
                self.assertEqual((world/name).read_bytes(), (restored/name).read_bytes())
            worker.run(world, 'snapshot-unit', REVISION, resume=True)
            worker.run(restored, 'snapshot-unit', REVISION, resume=True)
            self.assertEqual(heartbeat.inspect(world, REVISION)['states'], heartbeat.inspect(restored, REVISION)['states'])

    def test_existing_archive_and_restore_world_never_overwritten(self):
        with tempfile.TemporaryDirectory() as t:
            world, archive = self.fixture(Path(t))
            before = archive.read_bytes()
            journal = (world/'frames.jsonl').read_bytes()
            with self.assertRaises(FileExistsError):
                snapshot.pack(world, archive, REVISION)
            with self.assertRaises(FileExistsError):
                snapshot.unpack(archive, world, REVISION)
            self.assertEqual(archive.read_bytes(), before)
            self.assertEqual((world/'frames.jsonl').read_bytes(), journal)

    def test_unsafe_duplicate_path_symlink_oversize_and_duplicate_json_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            _, archive = self.fixture(root)
            with zipfile.ZipFile(archive) as z:
                original = {name:z.read(name) for name in z.namelist()}
            for index, kind in enumerate(('duplicate', 'path', 'symlink', 'oversize', 'json')):
                blobs = dict(original)
                attributes, extra = None, None
                if kind == 'duplicate':
                    extra = ('writer.lock', b'L')
                elif kind == 'path':
                    extra = ('../escaped', b'bad')
                elif kind == 'symlink':
                    attributes = {'writer.lock':0o120777 << 16}
                elif kind == 'oversize':
                    blobs['manifest.json'] = b'x'*(1024**2+1)
                else:
                    blobs['metadata.json'] = b'{"schema":"bad",'+blobs['metadata.json'][1:]
                forged = root/(str(index)+'.zip')
                self.rewrite(forged, blobs, attributes, extra)
                target = root/(str(index)+'-restore')
                with self.assertRaises(ValueError):
                    snapshot.unpack(forged, target, REVISION)
                self.assertFalse(target.exists())
            self.assertFalse((root.parent/'escaped').exists())

    def test_coherently_rehashed_random_state_forgery_rejected_by_semantic_replay(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            world, archive = self.fixture(root)
            original = archive.read_bytes()
            with zipfile.ZipFile(archive) as z:
                blobs = {name:z.read(name) for name in z.namelist()}
            metadata = json.loads(blobs.pop('metadata.json'))
            frames = [json.loads(line) for line in blobs['frames.jsonl'].splitlines()]
            frame = frames[-1]
            frame['state']['noise_cursor'] += 1
            frame['state_sha256'] = heartbeat.digest(frame['state'])
            frame['frame_sha256'] = heartbeat.digest({k:v for k,v in frame.items() if k != 'frame_sha256'})
            blobs['frames.jsonl'] = ''.join(heartbeat.canonical(v)+'\n' for v in frames).encode()
            blobs['checkpoint.json'] = (heartbeat.canonical(frame)+'\n').encode()
            metadata.update(files=audit.describe(blobs), state_sha256=frame['state_sha256'], last_frame_sha256=frame['frame_sha256'])
            blobs['metadata.json'] = (heartbeat.canonical(metadata)+'\n').encode()
            forged = root/'forged.zip'
            self.rewrite(forged, blobs)
            audit.read_package(forged, REVISION)  # Envelope really passes; semantics must reject.
            with self.assertRaisesRegex(ValueError, 'divergence'):
                snapshot.unpack(forged, root/'rejected-output', REVISION)
            self.assertTrue((root/'rejected-output').is_dir())
            self.assertEqual(archive.read_bytes(), original)
            self.assertEqual(heartbeat.inspect(world, REVISION)['report']['verified_simulation_tick'], 5)

    def test_real_competing_writer_blocks_capture_before_archive_creation(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            world, _ = self.fixture(root)
            command = ('import sys; from pathlib import Path; '
                       'from experiments.heartbeat_checkpoint import writer_lock; '
                       '\nwith writer_lock(Path(sys.argv[1])):\n print("LOCKED",flush=True)\n sys.stdin.readline()')
            with subprocess.Popen([sys.executable, '-B', '-c', command, str(world)], cwd=ROOT,
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as child:
                try:
                    self.assertEqual(child.stdout.readline().strip(), 'LOCKED')
                    with self.assertRaises(OSError):
                        snapshot.pack(world, root/'competing.zip', REVISION)
                    self.assertFalse((root/'competing.zip').exists())
                finally:
                    child.communicate('release\n', timeout=5)
                self.assertEqual(child.returncode, 0)

    def test_revision_binding_rejects_before_new_output(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            world, archive = self.fixture(root)
            for revision in ('main', 'z'*40, 'a'*39):
                with self.assertRaises(ValueError):
                    snapshot.pack(world, root/'invalid.zip', revision)
                self.assertFalse((root/'invalid.zip').exists())
            with self.assertRaises(ValueError):
                snapshot.unpack(archive, root/'mismatched', 'b'*40)
            self.assertFalse((root/'mismatched').exists())


if __name__ == '__main__':
    unittest.main()
