"""RESOURCE-02 explicit finite Windows pressure/recovery panel; no service."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from experiments import heartbeat_template as world
from experiments import process_limits as resource
from experiments.resource_continuity_audit import source_hashes

CASES = ('cpu', 'cpu-control', 'memory', 'memory-control', 'wall', 'wall-control')
NORMAL = dict(memory_bytes=512*1024**2, cpu_seconds=15, processes=4, wall_seconds=30)
ROOT = Path(__file__).resolve().parents[1]
PYTHON = getattr(sys, '_base_executable', sys.executable)
WORLD_ID = 'resource02-reference'


def settings(case):
    if case not in CASES:
        raise ValueError('Frozen RESOURCE-02 case required')
    return dict(memory_bytes=(512 if case == 'memory-control' else 128)*1024**2,
                cpu_seconds=1 if case == 'cpu' else 5, processes=4,
                wall_seconds=2 if case == 'wall' else 15)


def command(output, revision, resume=False):
    args = [PYTHON, '-m', 'experiments.heartbeat_template', '--output-dir', str(output),
            '--world-id', WORLD_ID, '--source-revision', revision,
            '--work', '2', '--max-ticks', '32', '--seed', '1']
    return args + (['--resume'] if resume else [])


def pressure_fixture(case, output, revision):
    """Inject pressure while the unmodified worker holds its cooperative lock."""
    settings(case)
    original = world.write_file

    # Hold the child object across the pressure and normal worker completion.
    children = []

    def inject(path, frame):
        original(path, frame)
        if path.name != 'checkpoint.pending' or frame['state']['simulation_tick'] != 5 or frame['reason'] != 'advanced':
            return
        child = subprocess.Popen([PYTHON, '-c', 'import time; time.sleep(60)'],
                                 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, close_fds=True)
        children.append(child)
        print(json.dumps(dict(boundary_tick=5, child_pid=child.pid)), flush=True)
        kind = case.split('-')[0]
        if kind == 'cpu':
            end = time.process_time() + 1.5
            value = 1
            while time.process_time() < end:
                value = (value*1664525+1013904223) % 2**32
            print(json.dumps(dict(cpu_pressure_complete=True)), flush=True)
        elif kind == 'memory':
            try:
                allocation = bytearray(256*1024**2)
            except MemoryError:
                print(json.dumps(dict(memory_denied=True)), flush=True)
                # Immediate authored root exit; job closure kills the child.
                os._exit(42)
            print(json.dumps(dict(allocation_bytes=len(allocation))), flush=True)
            del allocation
        else:
            time.sleep(4)
            print(json.dumps(dict(wall_pressure_complete=True)), flush=True)

    world.write_file = inject
    try:
        world.run(output, WORLD_ID, revision, work=2, max_ticks=32, seed=1)
    finally:
        world.write_file = original
    # Return promptly without waiting for/rescuing the sleeping descendant.
    # Native exit closes local handles; supervisor job closure kills the child.
    os._exit(0)


def run_panel(output, revision):
    if len(revision) != 40 or any(c not in '0123456789abcdef' for c in revision):
        raise ValueError('Exact source revision required')
    if os.name != 'nt':
        raise OSError('RESOURCE-02 requires real Windows enforcement')
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    reference = resource.run(command(output/'reference', revision), resource.Limits(**NORMAL), cwd=ROOT)
    data = dict(schema='resource02-panel-v1', revision=revision,
                source_sha256=source_hashes(ROOT), reference=reference, records=[])

    def save():
        (output/'evidence.json').write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')

    save()
    if reference['exit_code'] != 0:
        raise RuntimeError('Reference failed; preserved evidence')
    for trial in (0, 1):
        for case in CASES:
            label = f'{trial}-{case}'
            folder = output/label
            args = [PYTHON, '-m', 'experiments.resource_continuity', '--fixture', case,
                    '--output-dir', str(folder/'world'), '--source-revision', revision]
            stopped = resource.run(args, resource.Limits(**settings(case)), cwd=ROOT)
            row = dict(trial=trial, case=case, interrupted=stopped)
            data['records'].append(row)
            save()
            shutil.copytree(folder/'world', folder/'before')
            row['resume'] = resource.run(command(folder/'world', revision, True),
                                         resource.Limits(**NORMAL), cwd=ROOT)
            save()
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--source-revision', required=True)
    parser.add_argument('--fixture', choices=CASES)
    args = parser.parse_args()
    if args.fixture:
        pressure_fixture(args.fixture, Path(args.output_dir), args.source_revision)
    else:
        run_panel(args.output_dir, args.source_revision)
