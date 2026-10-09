"""Independent STORAGE-01 fault reconstruction and full-world replay."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from experiments import heartbeat_template_audit as heartbeat
from experiments import world_snapshot_audit as snapshot

CASES = ('missing-checkpoint', 'stale-checkpoint', 'junk-pending', 'partial-checkpoint',
         'rehashed-checkpoint', 'partial-journal', 'corrupt-journal', 'missing-journal',
         'bad-manifest', 'bad-lock')


def contents(directory):
    return {p.name: p.read_bytes() for p in Path(directory).iterdir() if p.is_file()}


def expected_fault(original, case):
    result = dict(original)
    checkpoint = original['checkpoint.json']
    if case == 'missing-checkpoint':
        del result['checkpoint.json']
    elif case == 'stale-checkpoint':
        result['checkpoint.json'] = original['frames.jsonl'].splitlines(keepends=True)[2]
    elif case == 'junk-pending':
        result['checkpoint.pending'] = b'not-json\n'
    elif case == 'partial-checkpoint':
        result['checkpoint.json'] = checkpoint[:len(checkpoint)//2]
    elif case == 'rehashed-checkpoint':
        value = heartbeat.decode(checkpoint)
        value['state']['world']['heat'] += 1
        value['state_sha256'] = heartbeat.digest(value['state'])
        value['frame_sha256'] = heartbeat.digest({k:v for k,v in value.items() if k != 'frame_sha256'})
        result['checkpoint.json'] = (heartbeat.canonical(value)+'\n').encode()
    elif case == 'partial-journal':
        result['frames.jsonl'] += b'{"schema":'
    elif case == 'corrupt-journal':
        chain = [heartbeat.decode(line) for line in original['frames.jsonl'].splitlines()]
        chain[1]['state']['world']['heat'] += 1
        chain[1]['state_sha256'] = heartbeat.digest(chain[1]['state'])
        previous = '0'*64
        for frame in chain:
            frame['previous_sha256'] = previous
            frame['frame_sha256'] = heartbeat.digest({k:v for k,v in frame.items() if k != 'frame_sha256'})
            previous = frame['frame_sha256']
        result['frames.jsonl'] = ''.join(heartbeat.canonical(frame)+'\n' for frame in chain).encode()
        result['checkpoint.json'] = (heartbeat.canonical(chain[-1])+'\n').encode()
    elif case == 'missing-journal':
        del result['frames.jsonl']
    elif case == 'bad-manifest':
        value = heartbeat.decode(original['manifest.json'])
        value['identity']['config_sha256'] = '0'*64
        result['manifest.json'] = (heartbeat.canonical(value)+'\n').encode()
    elif case == 'bad-lock':
        result['writer.lock'] = b'XX'
    return result


def audit(output, revision):
    output = Path(output)
    evidence = heartbeat.decode(heartbeat.read_small(output/'panel.json'))
    if (set(evidence) != {'schema', 'source_revision', 'source_sha256', 'records', 'commands'}
            or evidence['schema'] != 'storage01-panel-v1' or evidence['source_revision'] != revision
            or evidence['source_sha256'] != snapshot.sources()):
        raise ValueError('Panel source/schema')
    if [record.get('case') for record in evidence['records']] != list(CASES):
        raise ValueError('Complete ordered fault panel')
    reference = heartbeat.inspect(output/'reference', revision)
    paused = heartbeat.inspect(output/'paused', revision)
    if (reference['manifest']['identity'] != paused['manifest']['identity']
            or reference['manifest']['config'] != {'seed':1, 'work':2, 'max_ticks':32}
            or reference['report']['world_id'] != 'storage01-reference'
            or reference['report']['reported_status'] != 'stopped'
            or paused['report']['verified_simulation_tick'] != 5
            or paused['report']['reported_status'] != 'paused'):
        raise ValueError('Frozen reference/capture')
    original = contents(output/'paused')
    metadata, blobs = snapshot.read_package(output/'snapshot.zip', revision)
    snapshot.compare_capture(metadata, paused)
    if blobs != original or (output/'snapshot.zip').read_bytes() != (output/'snapshot-repeat.zip').read_bytes():
        raise ValueError('Exact deterministic snapshot')
    def args(path):
        return ['--output-dir', str(path), '--world-id', 'storage01-reference', '--source-revision', revision,
                '--work', '2', '--max-ticks', '32', '--seed', '1']
    commands = [('experiments.heartbeat_template', args(output/'reference'), 'reference.log', 0),
                ('experiments.heartbeat_template', [*args(output/'paused'), '--pause-after', '5'], 'paused.log', 0)]
    for name in ('snapshot.zip', 'snapshot-repeat.zip'):
        commands.append(('experiments.world_snapshot', ['pack', '--world-dir', str(output/'paused'), '--archive',
                         str(output/name), '--source-revision', revision], name+'.log', 0))
    for index, record in enumerate(evidence['records']):
        case, code = CASES[index], 0 if index < 3 else 2
        directory = output/case
        before, after = contents(directory/'faulted-before'), contents(directory/'world')
        if before != expected_fault(original, case):
            raise ValueError('Fault mutation differs: '+case)
        if (record['direct_exit'], record['restored_resume_exit']) != (code, 0):
            raise ValueError('Direct/restore exits: '+case)
        for name, data in [('before_sha256', before), ('after_sha256', after),
                           ('restored_sha256', contents(directory/'restored'))]:
            hashes = {k:hashlib.sha256(v).hexdigest() for k,v in data.items()}
            if record[name] != hashes:
                raise ValueError('Recorded file hashes: '+case)
        if code:
            if before != after:
                raise ValueError('Rejection mutated fault evidence')
            if case != 'bad-lock':
                try:
                    heartbeat.inspect(directory/'world', revision)
                except (ValueError, OSError, KeyError, TypeError):
                    pass
                else:
                    raise ValueError('Invalid world independently accepted')
        else:
            direct = heartbeat.inspect(directory/'world', revision)
            if direct['states'] != reference['states'] or not after['frames.jsonl'].startswith(original['frames.jsonl']):
                raise ValueError('Direct continuation differs')
        if contents(directory/'restored-before') != blobs:
            raise ValueError('Restored snapshot bytes differ')
        captured = heartbeat.inspect(directory/'restored-before', revision)
        snapshot.compare_capture(metadata, captured)
        restored = heartbeat.inspect(directory/'restored', revision)
        if (restored['manifest'] != reference['manifest'] or restored['states'] != reference['states']
                or restored['report']['reported_status'] != 'stopped'
                or not (directory/'restored/frames.jsonl').read_bytes().startswith(blobs['frames.jsonl'])):
            raise ValueError('Full restored identity/history/PRNG/provenance differs')
        observer = heartbeat.decode((output/(case+'-observer.json')).read_bytes())
        for key in ('run_id', 'verified_simulation_tick', 'verified_state_sha256', 'noise_cursor',
                    'atoms', 'historic_objects', 'work', 'heat', 'process_health'):
            if observer[key] != restored['report'][key]:
                raise ValueError('Observer differs from independent replay')
        if record['observer_read_only'] is not True:
            raise ValueError('Observer read-only marker')
        commands.extend([
            ('experiments.heartbeat_template', [*args(directory/'world'), '--resume'], case+'-direct.log', code),
            ('experiments.world_snapshot', ['restore', '--world-dir', str(directory/'restored'), '--archive',
                                           str(output/'snapshot.zip'), '--source-revision', revision], case+'-restore.log', 0),
            ('experiments.heartbeat_template', [*args(directory/'restored'), '--resume'], case+'-continued.log', 0),
            ('experiments.heartbeat_template_audit', ['--input-dir', str(directory/'restored'), '--source-revision', revision], case+'-observer.json', 0)])
    expected = [dict(module=m, args=a, log=l, exit_code=c) for m,a,l,c in commands]
    if evidence['commands'] != expected or any(not (output/row['log']).is_file() for row in expected):
        raise ValueError('Complete exact invocation/exit evidence')
    return dict(schema='storage01-audit-v1', cases=10, direct_recoveries=3, preserved_rejections=7,
                backup_continuations=10, exact_continuations=13, states_per_continuation=33,
                captured_tick=5, canonical_state_sequence_sha256=heartbeat.digest(reference['states']),
                restored_original_identity=True, process_health='unverified', observer_checks=10,
                independent_off_drive_backup=False, physical_storage_faults=False, evolution_claim=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(audit(args.input_dir, args.source_revision), indent=2, sort_keys=True))
    except (ValueError, OSError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        parser.exit(2, f'Rejected storage evidence: {exc}\n')
