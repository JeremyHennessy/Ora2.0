"""Independent ISOLATION-01 evidence acceptance; no worker imports or execution."""
import argparse
import hashlib
import json
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(output, source, revision):
    output, source = Path(output), Path(source)
    data = json.loads((output/'evidence.json').read_text(encoding='utf-8'))
    require(data['schema'] == 'isolation01-v1' and data['revision'] == revision, 'Source identity')
    names = {'experiments/isolation_capability.py', 'experiments/isolation_worker.py',
             'experiments/isolation_capability_audit.py', 'experiments/process_limits.py',
             'docs/ISOLATION-01-CONTRACT.md'}
    require(set(data['source_sha256']) == names, 'Complete source manifest')
    for name, digest in data['source_sha256'].items():
        require(sha(source/name) == digest, 'Source hash '+name)
    actual_runtime = {p.relative_to(output/'runtime').as_posix(): sha(p)
                      for p in (output/'runtime').rglob('*') if p.is_file()}
    require(actual_runtime == data['runtime_sha256'], 'Runtime copy changed')
    require(actual_runtime['worker.py'] == sha(source/'experiments/isolation_worker.py'), 'Worker copy mismatch')
    require(data['cleanup'] is True and data['cleanup_hresult'] == 0, 'Profile cleanup')
    require(0 < data['elapsed_seconds'] < 300, 'Finite panel time')
    cases = {'control', 'confined', 'missing', 'job', 'token'}
    require(len(data['rows']) == 10 and {(r['trial'], r['case']) for r in data['rows']} ==
            {(t, case) for t in range(2) for case in cases}, 'Frozen complete matrix')
    for row in data['rows']:
        case = row['case']
        require(row['stopped'] is True and row['elapsed_seconds'] < 10, 'Worker not stopped / timeout')
        require(row['confined'] is (case != 'control'), 'Wrong confinement mode')
        folder = output/f'{row["trial"]}-{case}'
        require(row['marker'] == (folder/'started').exists(), 'Marker mismatch')
        if case in {'missing', 'job', 'token'}:
            require(row['resumed'] is False and row['marker'] is False and row['worker_sha256'] is None,
                    'Fail-closed worker executed')
            require('error' in row and not row['connections'] and row['canary_before'] == row['canary_after'], 'Failure side effects')
            require(not (folder/'worker.json').exists(), 'Unexpected failure worker report')
            if case == 'missing':
                require(row['pid'] is None and row['winerror'] == 2, 'Missing executable creation failure')
            else:
                require(row['pid'] is not None and row['exit_code'] == 125, 'Suspended process cleanup')
                require(row['fault'] == case, 'Wrong injected gate')
            continue
        require(row['resumed'] is True and row['marker'] is True and row['exit_code'] == 0 and 'error' not in row, 'Successful worker missing')
        expected_token = dict(is_appcontainer=True, capabilities=0, package_sid=data['package_sid']) if case == 'confined' else dict(is_appcontainer=False, capabilities=0, package_sid=None)
        require(row['token'] == expected_token, 'Kernel token gate')
        for key in ('job_before', 'job_after'):
            usage = row[key]
            require(usage['configured_memory_bytes'] == 128*1024**2 and
                    usage['configured_processes'] == (1 if case == 'confined' else 2) and
                    usage['configured_cpu_ticks'] == 50_000_000 and usage['flags'] & 0x220c == 0x220c,
                    'Job caps readback')
        require(sha(folder/'worker.json') == row['worker_sha256'], 'Worker raw hash')
        worker = json.loads((folder/'worker.json').read_text(encoding='utf-8'))
        require(worker['pid'] == row['pid'], 'Worker identity')
        require(worker['workspace_write']['ok'] is True and worker['workspace_read'] == dict(ok=True, value='allowed'), 'Allowed workspace denied')
        require((folder/'allowed').read_text(encoding='utf-8') == 'allowed', 'Parent workspace observation')
        if case == 'control':
            require(all(worker[name]['ok'] is True for name in ('outside_read', 'outside_write', 'network', 'parent_handle', 'child')), 'Unrestricted control failed')
            require(worker['outside_read']['value'] == 'outside-canary-'+str(row['trial']) and worker['child']['value'] == 0, 'Control action result')
            require(row['canary_after'] == hashlib.sha256(b'control-write').hexdigest() and row['canary_after'] != row['canary_before'], 'Control write observation')
            require(len(row['connections']) == 1 and row['connections'][0]['payload'] == b'inert-probe'.hex(), 'Control listener observation')
            require(row['job_after']['started_processes'] == 2, 'Control child not accounted')
        else:
            require(all(worker[name]['ok'] is False for name in ('outside_read', 'outside_write', 'network', 'parent_handle', 'child')), 'Confined prohibited action succeeded')
            require(all(worker[name]['winerror'] == 5 for name in ('outside_read', 'outside_write', 'parent_handle')), 'Expected native access denial')
            require(worker['network']['winerror'] == 10013, 'Expected native socket access denial')
            require(worker['child']['winerror'] == 1816, 'Expected native process quota denial')
            require(row['canary_before'] == row['canary_after'] and not row['connections'], 'External effects observed')
            require(row['job_after']['started_processes'] == 1, 'Confined descendant launched')
    return dict(schema='isolation01-audit-v1', cases=10, controls=2, confined=2,
                fail_closed=6, evidence_sha256=sha(output/'evidence.json'),
                production_world_verified=False, hardened_runtime_verified=False,
                physical_power_loss_verified=False, continuous_operation=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--source-dir', required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    try:
        result = audit(args.output_dir, args.source_dir, args.source_revision)
    except (ValueError, KeyError, OSError) as error:
        print('Rejected:', error)
        raise SystemExit(2)
    print(json.dumps(result, indent=2))
