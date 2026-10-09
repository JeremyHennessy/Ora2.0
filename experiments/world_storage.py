"""Disposable STORAGE-01 corruption, rejection and snapshot-continuation panel."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from experiments import world_snapshot_audit as envelope

ROOT = Path(__file__).resolve().parents[1]
CASES = ('missing-checkpoint', 'stale-checkpoint', 'junk-pending', 'partial-checkpoint',
         'rehashed-checkpoint', 'partial-journal', 'corrupt-journal', 'missing-journal',
         'bad-manifest', 'bad-lock')


def files(directory):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(directory).iterdir() if p.is_file()}


def fault(directory, case):
    directory = Path(directory)
    checkpoint, journal = directory/'checkpoint.json', directory/'frames.jsonl'
    if case == 'missing-checkpoint':
        checkpoint.unlink()
    elif case == 'stale-checkpoint':
        checkpoint.write_bytes(journal.read_bytes().splitlines(keepends=True)[2])
    elif case == 'junk-pending':
        (directory/'checkpoint.pending').write_bytes(b'not-json\n')
    elif case == 'partial-checkpoint':
        raw = checkpoint.read_bytes()
        checkpoint.write_bytes(raw[:len(raw)//2])
    elif case == 'rehashed-checkpoint':
        value = json.loads(checkpoint.read_bytes())
        value['state']['world']['heat'] += 1
        value['state_sha256'] = envelope.heartbeat.digest(value['state'])
        value['frame_sha256'] = envelope.heartbeat.digest({k:v for k,v in value.items() if k != 'frame_sha256'})
        checkpoint.write_bytes((envelope.heartbeat.canonical(value)+'\n').encode())
    elif case == 'partial-journal':
        with journal.open('ab') as stream:
            stream.write(b'{"schema":')
    elif case == 'corrupt-journal':
        frames = [json.loads(line) for line in journal.read_bytes().splitlines()]
        frames[1]['state']['world']['heat'] += 1
        frames[1]['state_sha256'] = envelope.heartbeat.digest(frames[1]['state'])
        previous = '0'*64
        for value in frames:
            value['previous_sha256'] = previous
            value['frame_sha256'] = envelope.heartbeat.digest({k:v for k,v in value.items() if k != 'frame_sha256'})
            previous = value['frame_sha256']
        journal.write_bytes(b''.join((envelope.heartbeat.canonical(v)+'\n').encode() for v in frames))
        checkpoint.write_bytes((envelope.heartbeat.canonical(frames[-1])+'\n').encode())
    elif case == 'missing-journal':
        journal.unlink()
    elif case == 'bad-manifest':
        value = json.loads((directory/'manifest.json').read_bytes())
        value['identity']['config_sha256'] = '0'*64
        (directory/'manifest.json').write_bytes((envelope.heartbeat.canonical(value)+'\n').encode())
    elif case == 'bad-lock':
        (directory/'writer.lock').write_bytes(b'XX')
    else:
        raise ValueError('Unknown frozen fault')


def run_panel(output, revision):
    if not envelope.revision_valid(revision):
        raise ValueError('Exact revision required')
    output = Path(output)
    output.mkdir(exist_ok=False)
    evidence = dict(schema='storage01-panel-v1', source_revision=revision,
                    source_sha256=envelope.sources(), records=[], commands=[])
    def execute(module, args, log, expected=0):
        command = [sys.executable, '-B', '-m', module, *map(str, args)]
        with (output/log).open('w', encoding='utf-8') as stream:
            code = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=30).returncode
        evidence['commands'].append(dict(module=module, args=list(map(str,args)), log=log, exit_code=code))
        (output/'panel.json').write_text(json.dumps(evidence, indent=2)+'\n', encoding='utf-8')
        if code != expected:
            raise ValueError(f'Unexpected {log} exit: {code}, expected {expected}')
        return code
    def world_args(path):
        return ['--output-dir', path, '--world-id', 'storage01-reference', '--source-revision', revision,
                '--work', '2', '--max-ticks', '32', '--seed', '1']
    execute('experiments.heartbeat_template', world_args(output/'reference'), 'reference.log')
    execute('experiments.heartbeat_template', [*world_args(output/'paused'), '--pause-after', '5'], 'paused.log')
    original = files(output/'paused')
    for name in ('snapshot.zip', 'snapshot-repeat.zip'):
        execute('experiments.world_snapshot', ['pack', '--world-dir', output/'paused', '--archive', output/name,
                                              '--source-revision', revision], name+'.log')
    if original != files(output/'paused') or (output/'snapshot.zip').read_bytes() != (output/'snapshot-repeat.zip').read_bytes():
        raise ValueError('Snapshot read-only/determinism failure')
    for index, case in enumerate(CASES):
        case_dir = output/case
        case_dir.mkdir()
        world = case_dir/'world'
        shutil.copytree(output/'paused', world)
        fault(world, case)
        shutil.copytree(world, case_dir/'faulted-before')
        expected = 0 if index < 3 else 2
        direct = execute('experiments.heartbeat_template', [*world_args(world), '--resume'], case+'-direct.log', expected)
        if direct and files(world) != files(case_dir/'faulted-before'):
            raise ValueError('Rejected fault input mutated')
        restored = case_dir/'restored'
        execute('experiments.world_snapshot', ['restore', '--world-dir', restored, '--archive', output/'snapshot.zip',
                                              '--source-revision', revision], case+'-restore.log')
        shutil.copytree(restored, case_dir/'restored-before')
        resumed = execute('experiments.heartbeat_template', [*world_args(restored), '--resume'], case+'-continued.log')
        before_observer = files(restored)
        execute('experiments.heartbeat_template_audit', ['--input-dir', restored, '--source-revision', revision], case+'-observer.json')
        if before_observer != files(restored):
            raise ValueError('Observer mutated world')
        evidence['records'].append(dict(case=case, direct_exit=direct, restored_resume_exit=resumed,
                                        before_sha256=files(case_dir/'faulted-before'), after_sha256=files(world),
                                        restored_sha256=files(restored), observer_read_only=True))
        (output/'panel.json').write_text(json.dumps(evidence, indent=2)+'\n', encoding='utf-8')
    return evidence


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    try:
        result = run_panel(args.output_dir, args.source_revision)
        print(json.dumps(dict(records=len(result['records'])), sort_keys=True))
    except (ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        parser.exit(2, f'Rejected panel: {exc}\n')
