"""Independent RESOURCE-01 evidence audit; imports no supervisor implementation."""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path

CASES = ('success', 'cpu', 'memory', 'memory-control', 'process', 'timeout', 'orphan', 'output')
FILES = ('docs/RESOURCE-01-CONTRACT.md', 'docs/RESOURCE-01-DIAGNOSTIC-ADDENDUM.md',
         'experiments/process_limits.py', 'experiments/process_limits_audit.py',
         'tests/resource_worker.py', 'tests/test_process_limits.py')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, 'Duplicate evidence key')
        value[key] = item
    return value


def exited(pid):
    require(os.name == 'nt', 'OS exit verification requires Windows')
    k = ctypes.WinDLL('kernel32', use_last_error=True)
    k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k.OpenProcess.restype = wintypes.HANDLE
    k.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    k.WaitForSingleObject.restype = wintypes.DWORD
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    k.CloseHandle.restype = wintypes.BOOL
    handle = k.OpenProcess(0x100000, False, pid)
    if not handle:
        require(ctypes.get_last_error() == 87, 'Cannot independently inspect child exit')
        return True
    try:
        return k.WaitForSingleObject(handle, 2000) == 0
    finally:
        k.CloseHandle(handle)


def audit(input_path, revision, source):
    raw = Path(input_path).read_bytes()
    data = json.loads(raw, object_pairs_hook=unique)
    require(data['schema'] == 'resource01-fixtures-v1' and data['revision'] == revision, 'Source identity')
    require(len(revision) == 40 and all(x in '0123456789abcdef' for x in revision), 'Exact revision')
    require(set(data['source_sha256']) == set(FILES), 'Source inventory')
    for name in FILES:
        require(hashlib.sha256((source / name).read_bytes()).hexdigest() == data['source_sha256'][name], 'Source checksum: '+name)
    require([(r['trial'], r['case']) for r in data['records']] ==
            [(trial, case) for trial in (0, 1) for case in CASES], 'Complete frozen ordered fixture set')
    normalized = {}
    for record in data['records']:
        case, r = record['case'], record['result']
        require(r['schema'] == 'resource01-result-v1' and r['platform'] == 'Windows', 'Windows report required')
        expected = dict(memory_bytes=(512 if case == 'memory-control' else 128)*1024**2,
                        cpu_seconds=0.2 if case == 'cpu' else 5, processes=3,
                        wall_seconds=0.5 if case == 'timeout' else 5)
        require(r['limits'] == expected, 'Frozen caps differ')
        require(r['usage']['configured_memory_bytes'] == expected['memory_bytes'] and
                r['usage']['configured_cpu_ticks'] == int(expected['cpu_seconds']*10_000_000) and
                r['usage']['configured_processes'] == 3 and r['usage']['flags'] & 0x220c == 0x220c,
                'Configured job enforcement differs')
        require(r['isolation_verified'] is False, 'Unsupported isolation claim')
        require(0 <= r['retained_bytes'] <= 1024**2 and r['output_bytes'] >= r['retained_bytes'], 'Output bound')
        require(r['elapsed_seconds'] < 5, 'Fixture cleanup exceeded margin')
        require(r['timed_out'] == (case == 'timeout'), 'Timeout contrast')
        command_case = 'memory' if case == 'memory-control' else case
        require(r['command'][1:] == [str(source / 'tests/resource_worker.py'), command_case], 'Fixture command')
        checks = dict(correct_limit_configuration=True, retained_output_bounded=True,
                      cleanup_within_fixture_margin=True)
        if case == 'cpu':
            require(r['exit_code'] != 0 and r['usage']['user_cpu_seconds'] >= 0.15, 'CPU worker not stopped by budget')
            checks['cpu_worker_stopped_before_wall'] = True
        elif case == 'memory':
            require(r['exit_code'] == 42 and 'memory-denied' in r['output'] and
                    'allocation-succeeded' not in r['output'], 'Memory denial')
            checks['allocation_denied'] = True
        elif case == 'memory-control':
            require(r['exit_code'] == 0 and 'allocation-succeeded 268435456' in r['output'] and
                    'memory-denied' not in r['output'], 'Causal allocation allowance')
            checks['same_allocation_allowed_with_larger_cap'] = True
        elif case in ('process', 'timeout', 'orphan'):
            rows = [json.loads(line, object_pairs_hook=unique) for line in r['output'].splitlines()]
            require(exited(rows[0]['child_pid']), 'Surviving descendant')
            if case == 'timeout':
                require(r['exit_code'] != 0, 'Timeout root survived')
            else:
                require(r['exit_code'] == 0, 'Finite parent failed')
            if case == 'process':
                require(rows[1]['fourth_denied'] is True and r['usage']['started_processes'] <= 3, 'Fourth process not rejected')
                checks['fourth_process_denied'] = True
            checks['independent_os_child_exit'] = True
        elif case == 'output':
            require(r['exit_code'] == 0 and r['output_truncated'] is True and
                    r['output_bytes'] == 2*1024**2 and r['retained_bytes'] == 1024**2, 'Output causal bound')
            checks['output_drained_and_truncated'] = True
        else:
            require(r['exit_code'] == 0 and 'finite-success' in r['output'], 'Finite success')
            checks['finite_success'] = True
        normalized.setdefault(record['trial'], {})[case] = checks
    require(normalized[0] == normalized[1], 'Deterministic assertion replay differs')
    return dict(schema='resource01-audit-v1', revision=revision, fixtures=16,
                independent_os_child_exit_checks=6, assertions_exact_replay=True,
                passed=True, no_scientific_worlds=True, windows_only=True,
                memory_peak_bound_unverified=True, exact_cpu_ceiling_unverified=True,
                assertions=normalized[0], input_sha256=hashlib.sha256(raw).hexdigest())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.input, args.source_revision, Path(__file__).resolve().parents[1]), indent=2))

