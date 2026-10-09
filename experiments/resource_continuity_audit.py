"""Independent RESOURCE-02 audit; imports no driver, worker or supervisor."""
import argparse
import hashlib
import json
from pathlib import Path

from experiments import heartbeat_template_audit as heartbeat
from experiments.process_limits_audit import exited, unique, require
from experiments.process_limits_audit import FILES as RESOURCE_FILES

CASES = ('cpu', 'cpu-control', 'memory', 'memory-control', 'wall', 'wall-control')
NORMAL = dict(memory_bytes=512*1024**2, cpu_seconds=15, processes=4, wall_seconds=30)
FILES = tuple(dict.fromkeys((*heartbeat.FILES, *RESOURCE_FILES,
              'docs/RESOURCE-02-CONTRACT.md', 'docs/RESOURCE-02-DIAGNOSTIC-ADDENDUM.md',
              'experiments/resource_continuity.py',
              'experiments/resource_continuity_audit.py', 'tests/test_resource_continuity.py')))


def source_hashes(source):
    return {name: hashlib.sha256((source/name).read_bytes()).hexdigest() for name in FILES}


def read(path):
    raw = path.read_bytes()
    require(len(raw) <= 2*1024**2, 'Bounded panel evidence')
    return json.loads(raw, object_pairs_hook=unique)


def caps(result, expected):
    require(result['schema'] == 'resource01-result-v1' and result['platform'] == 'Windows', 'Windows result required')
    require(result['limits'] == expected, 'Frozen caps differ')
    usage = result['usage']
    require(usage['configured_memory_bytes'] == expected['memory_bytes'] and
            usage['configured_cpu_ticks'] == int(expected['cpu_seconds']*10_000_000) and
            usage['configured_processes'] == 4 and usage['flags'] & 0x220c == 0x220c,
            'Queried limits differ')
    require(0 <= result['retained_bytes'] <= 1024**2 and
            result['output_bytes'] >= result['retained_bytes'] and
            not result['output_truncated'], 'Bounded complete marker output')
    require(result['isolation_verified'] is False, 'Unsupported isolation claim')


def successful(result):
    caps(result, NORMAL)
    require(result['exit_code'] == 0 and not result['timed_out'] and
            not result['supervisor_cpu_stop'], 'Reference/resume failed')


def world_command(result, output, revision, resume=False):
    expected = ['-m', 'experiments.heartbeat_template', '--output-dir', str(output),
                '--world-id', 'resource02-reference', '--source-revision', revision,
                '--work', '2', '--max-ticks', '32', '--seed', '1']
    require(result['command'][1:] == expected + (['--resume'] if resume else []), 'World command differs')
    require(result['command'][0] == result['bootstrap_python'], 'Base interpreter required')


def audit(output, revision, source):
    output, source = Path(output).resolve(), Path(source).resolve()
    data = read(output/'evidence.json')
    require(data['schema'] == 'resource02-panel-v1' and data['revision'] == revision and
            isinstance(revision, str) and len(revision) == 40 and
            all(c in '0123456789abcdef' for c in revision), 'Exact source identity')
    require(data['source_sha256'] == source_hashes(source), 'Source inventory/checksum differs')
    require([(r['trial'], r['case']) for r in data['records']] ==
            [(trial, case) for trial in (0, 1) for case in CASES], 'Complete ordered panel required')
    successful(data['reference'])
    world_command(data['reference'], output/'reference', revision)
    reference = heartbeat.inspect(output/'reference', revision)
    require(reference['manifest']['config'] == dict(seed=1, work=2, max_ticks=32) and
            reference['frames'][-1]['status'] == 'stopped', 'Frozen reference horizon')
    expected_states = reference['states']
    require(len(expected_states) == 33, 'Complete reference states')
    checks = []
    for row in data['records']:
        case, r = row['case'], row['interrupted']
        folder = output/f"{row['trial']}-{case}"
        expected_caps = dict(memory_bytes=(512 if case == 'memory-control' else 128)*1024**2,
                             cpu_seconds=1 if case == 'cpu' else 5, processes=4,
                             wall_seconds=2 if case == 'wall' else 15)
        caps(r, expected_caps)
        require(r['command'][1:] == ['-m', 'experiments.resource_continuity', '--fixture', case,
                '--output-dir', str(folder/'world'), '--source-revision', revision] and
                r['command'][0] == r['bootstrap_python'], 'Pressure command differs')
        markers = [json.loads(line, object_pairs_hook=unique) for line in r['output'].splitlines()]
        require(markers and set(markers[0]) == {'boundary_tick', 'child_pid'} and
                markers[0]['boundary_tick'] == 5 and type(markers[0]['child_pid']) is int and
                markers[0]['child_pid'] > 0, 'Durable pressure boundary missing')
        require(r['elapsed_seconds'] < expected_caps['wall_seconds']+5, 'Cleanup exceeded fixture margin')
        if case == 'cpu':
            require(r['exit_code'] != 0 and not r['timed_out'] and
                    r['usage']['user_cpu_seconds'] >= 0.8 and len(markers) == 1,
                    'CPU pressure not stopped before wall')
        elif case == 'memory':
            require(r['exit_code'] == 42 and not r['timed_out'] and
                    markers[1:] == [dict(memory_denied=True)], 'Causal memory denial missing')
        elif case == 'wall':
            require(r['exit_code'] != 0 and r['timed_out'] and len(markers) == 1,
                    'Wall pressure not stopped by deadline')
        else:
            marker = {'cpu-control': dict(cpu_pressure_complete=True),
                      'memory-control': dict(allocation_bytes=256*1024**2),
                      'wall-control': dict(wall_pressure_complete=True)}[case]
            require(r['exit_code'] == 0 and not r['timed_out'] and
                    not r['supervisor_cpu_stop'] and markers[1:] == [marker], 'Causal control failed')
        require(exited(markers[0]['child_pid']), 'Surviving pressure descendant')
        before = heartbeat.inspect(folder/'before', revision)
        after = heartbeat.inspect(folder/'world', revision)
        control = case.endswith('-control')
        require(before['report']['verified_simulation_tick'] == (32 if control else 5) and
                before['report']['checkpoint_current'] == control and
                before['frames'][-1]['status'] == ('stopped' if control else 'running'),
                'Unexpected durable boundary/checkpoint')
        require((folder/'world/frames.jsonl').read_bytes().startswith((folder/'before/frames.jsonl').read_bytes()),
                'Committed prefix altered')
        require((folder/'world/manifest.json').read_bytes() == (folder/'before/manifest.json').read_bytes() and
                before['manifest'] == reference['manifest'] and after['manifest'] == reference['manifest'],
                'Original world identity changed')
        require(before['states'] == expected_states[:len(before['states'])] and after['states'] == expected_states,
                'Canonical world/random/ancestry/provenance continuity differs')
        require(after['frames'][-1]['status'] == 'stopped' and after['report']['checkpoint_current'],
                'Original horizon not completed')
        require(before['report']['process_health'] == after['report']['process_health'] == 'unverified',
                'Unsupported observer process-health claim')
        successful(row['resume'])
        world_command(row['resume'], folder/'world', revision, True)
        if control:
            inventory = lambda p: {x.name: x.read_bytes() for x in p.iterdir() if x.is_file()}
            require(inventory(folder/'before') == inventory(folder/'world'), 'Terminal resume mutated control')
        checks.append(dict(trial=row['trial'], case=case, original_identity=True,
                           exact_canonical_states=True, committed_prefix=True,
                           independent_child_exit=True, verified_terminal_tick=32))
    return dict(schema='resource02-audit-v1', revision=revision, passed=True, records=12,
                canonical_sequences=12, independent_os_child_exit_checks=12, checks=checks,
                terminal_state_sha256=heartbeat.digest(expected_states[-1]),
                input_sha256=hashlib.sha256((output/'evidence.json').read_bytes()).hexdigest(),
                memory_peak_bound_unverified=True, exact_cpu_ceiling_unverified=True,
                power_loss_unverified=True, hardened_isolation_unverified=True,
                independent_natural_worlds=0, continuous_runtime=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.input_dir, args.source_revision, Path(__file__).resolve().parents[1]), indent=2))
