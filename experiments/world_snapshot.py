"""Explicit create-new verified finite-world snapshots and restoration."""
import argparse
import json
import os
from pathlib import Path
import zipfile
from experiments.heartbeat_checkpoint import writer_lock
from experiments import world_snapshot_audit as audit


def pack(world, archive, revision):
    if not audit.revision_valid(revision):
        raise ValueError('Exact revision required')
    world, archive = Path(world), Path(archive)
    if archive.exists():
        raise FileExistsError('Snapshot archive must be new')
    # Windows denies reading the held byte through a second file descriptor.
    with (world/'writer.lock').open('rb') as stream:
        initializer = stream.read(2)
    if initializer != b'L':
        raise ValueError('Lock initializer')
    with writer_lock(world):
        evidence = audit.heartbeat.inspect(world, revision)
        names = ['manifest.json', 'frames.jsonl']
        if (world/'checkpoint.json').exists():
            names.append('checkpoint.json')
        blobs = {'writer.lock': initializer}
        for name in names:
            with (world/name).open('rb') as stream:
                blobs[name] = stream.read(audit.LIMITS[name]+1)
            if len(blobs[name]) > audit.LIMITS[name]:
                raise ValueError('Bounded snapshot source file')
        if blobs['writer.lock'] != b'L':
            raise ValueError('Lock initializer')
        metadata = dict(schema='storage01-snapshot-v1', source_revision=revision,
                        source_sha256=audit.sources(), identity=evidence['manifest']['identity'],
                        captured_tick=evidence['report']['verified_simulation_tick'],
                        last_frame_sha256=evidence['frames'][-1]['frame_sha256'],
                        state_sha256=evidence['report']['verified_state_sha256'], files=audit.describe(blobs))
        audit.compare_capture(metadata, audit.heartbeat.inspect(world, revision))
        if any((world/name).read_bytes() != blobs[name] for name in names):
            raise ValueError('Source changed during cooperative snapshot')
        payload = dict(blobs, **{'metadata.json': (audit.heartbeat.canonical(metadata)+'\n').encode()})
        with archive.open('xb') as stream:
            with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for name, value in sorted(payload.items()):
                    info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o100600 << 16
                    z.writestr(info, value, compresslevel=9)
            stream.flush()
            os.fsync(stream.fileno())
        audit.read_package(archive, revision)
    return metadata


def unpack(archive, destination, revision):
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError('Restore destination must be new')
    metadata, blobs = audit.read_package(archive, revision)
    destination.mkdir()  # Parent must already exist; never replace or merge a world.
    for name, value in blobs.items():
        with (destination/name).open('xb') as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
    if any((destination/name).read_bytes() != value for name, value in blobs.items()):
        raise ValueError('Restored file bytes differ from verified snapshot')
    evidence = audit.heartbeat.inspect(destination, revision)
    audit.compare_capture(metadata, evidence)
    return evidence['report']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('pack', 'restore'))
    parser.add_argument('--world-dir', required=True)
    parser.add_argument('--archive', required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    try:
        result = (pack(args.world_dir, args.archive, args.source_revision) if args.operation == 'pack'
                  else unpack(args.archive, args.world_dir, args.source_revision))
        print(json.dumps(result, indent=2, sort_keys=True))
    except (ValueError, OSError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        parser.exit(2, f'Rejected snapshot: {exc}\n')
