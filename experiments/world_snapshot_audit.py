"""Strict bounded snapshot envelope reader; no worker or snapshot writer imports."""
import hashlib
import io
import json
from pathlib import Path
import stat
import zipfile
from experiments import heartbeat_template_audit as heartbeat

ROOT = Path(__file__).resolve().parents[1]
LIMITS = {'manifest.json': 1024**2, 'checkpoint.json': 1024**2,
          'frames.jsonl': 16*1024**2, 'writer.lock': 1, 'metadata.json': 65536}
FILES = (*heartbeat.FILES, 'experiments/world_snapshot.py', 'experiments/world_snapshot_audit.py',
         'experiments/world_storage.py', 'experiments/world_storage_audit.py', 'docs/STORAGE-01-CONTRACT.md')


def sources():
    return {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in FILES}


def revision_valid(revision):
    return isinstance(revision, str) and len(revision) == 40 and all(c in '0123456789abcdef' for c in revision)


def describe(blobs):
    return {name: dict(size=len(data), sha256=hashlib.sha256(data).hexdigest()) for name, data in blobs.items()}


def read_package(archive, revision):
    """Validate envelope only; semantic success additionally requires world replay."""
    if not revision_valid(revision):
        raise ValueError('Exact revision required')
    with Path(archive).open('rb') as stream:
        raw = stream.read(20*1024**2+1)
    if len(raw) > 20*1024**2:
        raise ValueError('Bounded archive')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries = z.infolist()
        names = [entry.filename for entry in entries]
        required = {'manifest.json', 'frames.jsonl', 'writer.lock', 'metadata.json'}
        if len(names) != len(set(names)) or not required <= set(names) <= set(LIMITS):
            raise ValueError('Fixed unique archive member allowlist')
        for entry in entries:
            mode = entry.external_attr >> 16
            if (entry.is_dir() or entry.flag_bits & 1 or entry.compress_type != zipfile.ZIP_DEFLATED
                    or mode and stat.S_IFMT(mode) not in (0, stat.S_IFREG)
                    or entry.file_size > LIMITS[entry.filename]):
                raise ValueError('Unsafe or oversized archive member')
        blobs = {entry.filename: z.read(entry) for entry in entries}
    if any(len(value) > LIMITS[name] for name, value in blobs.items()):
        raise ValueError('Actual member size exceeds bound')
    metadata = heartbeat.decode(blobs.pop('metadata.json'))
    keys = {'schema', 'source_revision', 'source_sha256', 'identity', 'captured_tick',
            'last_frame_sha256', 'state_sha256', 'files'}
    if not isinstance(metadata, dict) or set(metadata) != keys or metadata['schema'] != 'storage01-snapshot-v1':
        raise ValueError('Snapshot metadata schema')
    if (metadata['source_revision'] != revision or metadata['source_sha256'] != sources()
            or type(metadata['captured_tick']) is not int or not 0 <= metadata['captured_tick'] <= 128):
        raise ValueError('Snapshot source/capture binding')
    if metadata['files'] != describe(blobs) or blobs['writer.lock'] != b'L':
        raise ValueError('Snapshot file sizes/hashes/lock')
    for name in ('last_frame_sha256', 'state_sha256'):
        if not heartbeat.hex_string(metadata[name], 64):
            raise ValueError('Snapshot state/frame digest')
    return metadata, blobs


def compare_capture(metadata, evidence):
    report, last = evidence['report'], evidence['frames'][-1]
    if (metadata['identity'] != evidence['manifest']['identity']
            or metadata['captured_tick'] != report['verified_simulation_tick']
            or metadata['state_sha256'] != report['verified_state_sha256']
            or metadata['last_frame_sha256'] != last['frame_sha256']):
        raise ValueError('Snapshot capture diverges from independent world replay')
