"""Separate remaining-role custody interface. No execution admission or VM.

The stopped primary and its failed metric role remain closed. Cached metric
materialization is a new read-only derivation, never another producer attempt.
"""
import json
from pathlib import Path

from experiments import digital_inheritance83_custody as old

CACHED = old.PRIMARY[:3]
REMAINING = old.PRIMARY[3:] + old.UNSEEN
VERSION = 'INHERITANCE83-REMAINING-INTERFACE-v1'


def plan():
    return [r for r in old.plan() if r == 'final:acceptance' or int(r.split(':')[1]) in REMAINING]


def guard(request):
    """Called by a future separately pinned worker BEFORE delegating any role."""
    from experiments.digital_inheritance83_primary_child import role_parts
    role_parts(request)
    assert request['role'] in plan(), 'cached or foreign remaining role'


def allocations():
    result = {}
    names = old.allocations()
    for role in plan():
        stem = role.replace(':', '-')
        for directory in ('data', 'native', 'request'):
            name = directory+'/'+stem+'.json'
            result[name] = names[name]
    for name, limit in names.items():
        if '/bad-' in name:
            result[name] = limit
    for seed in CACHED:
        result[f'cached-metrics/{seed}.json'] = 8*old.M
    return result


def spec(path):
    """Plain identity/extent/hash guard, streaming even for cached histories."""
    from experiments import evidence_write_grant68 as transport
    import hashlib
    import os
    path = Path(path)
    assert path.is_absolute()
    for parent in path.parents:
        transport.plain(parent, True)
    before = transport.plain(path)
    assert before.st_size > 0
    h = hashlib.sha256()
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        assert (opened.st_dev, opened.st_ino, opened.st_size) == (before.st_dev, before.st_ino, before.st_size)
        for block in iter(lambda: stream.read(old.M), b''):
            h.update(block)
    after = transport.plain(path)
    assert (after.st_dev, after.st_ino, after.st_size) == (before.st_dev, before.st_ino, before.st_size)
    return dict(path=str(path), extent=before.st_size, sha256=h.hexdigest())


def pinned_read(value, cap, canonical=True):
    from experiments.digital_cognitive76_child import read_spec, bounded_bytes, pairs
    assert spec(value['path']) == value, 'cache bytes changed'
    if canonical:
        return read_spec(value, cap)
    import hashlib
    raw = bounded_bytes(Path(value['path']), cap, value['extent'])
    assert hashlib.sha256(raw).hexdigest() == value['sha256']
    return json.loads(raw, object_pairs_hook=pairs)


def native_binding(request_spec, native_spec):
    """Bind a retained native command to its sealed canonical output and source."""
    from experiments import digital_cognitive76_child as boundary
    from experiments import evidence_write_grant68 as transport
    req = pinned_read(request_spec, 65536)
    native = pinned_read(native_spec, old.M)
    assert native['command'][-1] == request_spec['path'], 'native input'
    assert native['limits'] == dict(memory_bytes=512*old.M, cpu_seconds=60, wall_seconds=90, processes=3)
    assert native['exit_code'] == 0 and not native['timed_out'] and not native['output_truncated']
    assert native['post_close_processes_exited'] and native['usage']['active_before_close'] == 0
    assert req['source_sha'] == old.digest(req['source_files'])
    assert req['config_sha'] == old.digest(req['configuration'])
    # Requests and their source exports are pinned separately, never inferred
    # from a successful stdout flag. The source files remain at archived paths.
    root = Path(req['grant']['root'])/'raw'/req['role'].split(':')[0]
    assert boundary.verify_source(root, req['source_files']) == req['source_sha']
    output = json.loads(native['output'], object_pairs_hook=boundary.pairs)
    g = req['grant']; receipt = output['receipt']
    assert req['seal'] == transport.digest(g) == receipt['grant_sha256']
    for key, expected in (('role', req['role']), ('source_sha', req['source_sha']), ('config_sha', req['config_sha'])):
        assert output[key] == receipt[key] == g[key] == expected
    assert output.get('error') is None
    path = Path(g['root'])/g['phase']/g['name']
    info = transport.plain(path)
    assert (info.st_dev, info.st_ino) == (g['device'], g['inode'])
    result = spec(path)
    assert 0 < result['extent'] == receipt['extent'] <= g['limit']
    assert result['sha256'] == receipt['sha256']
    return req, native, result


def qualified_summary(value, summary):
    """The earlier report intentionally omits only its large metric_batches."""
    assert set(value) == set(summary) | {'metric_batches'}
    assert 'metric_batches' not in summary
    assert {k: v for k, v in value.items() if k != 'metric_batches'} == summary


def cached_batches(manifest, expected_sha):
    """Authenticate closed chains and return exactly three canonical batches.

    Caller pins expected_sha prospectively; changing an input cannot silently
    replace a cached result. This is custody, not another physics computation.
    """
    assert old.digest(manifest) == expected_sha, 'cache manifest'
    assert set(manifest) == {'version', 'old_report', 'old_archive', 'qualified_report',
                             'qualified_archive', 'cells', 'qualified'}
    assert manifest['version'] == VERSION
    stopped = pinned_read(manifest['old_report'], old.M, canonical=False)
    assert stopped['verified'] is False and stopped['original_cells'] == 15 and stopped['native_calls'] == 52
    assert stopped['archive_exact'] and stopped['archive_sha256'] == manifest['old_archive']['sha256']
    assert spec(manifest['old_archive']['path']) == manifest['old_archive']
    qualified = pinned_read(manifest['qualified_report'], 8*old.M, canonical=False)
    assert qualified['verified'] and qualified['custody_fix_qualified'] and qualified['new_worlds'] == 0
    assert qualified['target_queries'] == 0 and qualified['continuation_admitted'] is False
    assert qualified['archive_exact'] and qualified['archive_sha256'] == manifest['qualified_archive']['sha256']
    assert spec(manifest['qualified_archive']['path']) == manifest['qualified_archive']
    expected = [(s, m) for s in CACHED for m in old.MODES]
    assert [(x['seed'], x['mode']) for x in manifest['cells']] == expected, 'cached cells'
    outputs = {}
    for cell in manifest['cells']:
        seed, mode = cell['seed'], cell['mode']
        original = None
        for export, kind in (('original', 'generate'), ('restored', 'generate'), ('original', 'audit')):
            role = f'{export}:{seed}:{mode}:{kind}'
            chain = cell[export+'_'+kind]
            req, native, body = native_binding(chain['request'], chain['native'])
            assert req['role'] == role and req['configuration'] == old.CONFIG
            assert role in stopped['completed_valid_receipt_roles']
            inputs = original if kind == 'audit' else None
            assert req['input'] == inputs
            assert old.consume(role, inputs, req, native, req['source_files'], req['grant']) == body
            if export == 'restored':
                assert (original['extent'], original['sha256']) == (body['extent'], body['sha256']), 'cached parity'
            if export == 'original' and kind == 'generate':
                original = body
            outputs[role] = body
    combined = []
    for export in ('original', 'restored'):
        chain = manifest['qualified'][export]
        req, native, body = native_binding(chain['request'], chain['native'])
        assert req['role'] == export+':retained-metrics'
        value = pinned_read(body, 8*old.M)
        assert value['verified'] and value['new_worlds'] == value['target_queries'] == 0
        assert value['original_primary_remains_closed_incomplete'] and value['continuation_admitted'] is False
        qualified_summary(value, qualified['summary'])
        # Bind the source-qualified combined result to all fifteen exact inputs.
        assert [i['seed'] for i in req['inputs']] == list(CACHED)
        for item in req['inputs']:
            assert [r['mode'] for r in item['rows']] == list(old.MODES)
            for row in item['rows']:
                for key, kind in (('record', 'generate'), ('proof', 'audit')):
                    old_spec = outputs[f"original:{item['seed']}:{row['mode']}:{kind}"]
                    actual = spec(row[key]['path'])
                    assert actual == row[key]
                    assert (actual['extent'], actual['sha256']) == (old_spec['extent'], old_spec['sha256'])
        combined.append((body, value))
    assert (combined[0][0]['extent'], combined[0][0]['sha256']) == (combined[1][0]['extent'], combined[1][0]['sha256'])
    batches = combined[0][1]['metric_batches']
    assert [b['seed'] for b in batches] == list(CACHED)
    from experiments.digital_inheritance83_acceptance import validate_metric
    for batch in batches:
        assert [m['mode'] for m in batch['metrics']] == list(old.MODES)
        for metric in batch['metrics']:
            validate_metric(metric, batch['seed'], metric['mode'])
    return batches


def pipeline(launcher, pins, grants, cached, progress=None):
    """209 new successful roles, never regenerate a cached context.

    cached is the three materialized guarded batch specs, already authenticated
    against cached_batches by the trusted controller before this call.
    """
    from experiments.digital_cognitive76_child import validate_grant, read_spec
    grants = json.loads(old.canonical(grants))
    assert set(grants) == set(plan()) and set(cached) == set(CACHED)
    assert len({(g['device'], g['inode']) for g in grants.values()}) == len(plan())
    metric_inputs = []
    for seed in CACHED:
        value = read_spec(cached[seed], 8*old.M)
        assert value['seed'] == seed and [m['mode'] for m in value['metrics']] == list(old.MODES)
        metric_inputs.append(cached[seed])
    for role in plan():
        g = grants[role]
        assert g['limit'] == (64 if role.endswith(':generate') else 8)*old.M
        validate_grant(dict(grant=g, grant_seal=old.digest(g), configuration_sha256=old.digest(old.CONFIG), role=role),
                       old.digest(pins), 'recording' if role.endswith(':generate') else 'proof')
    completed = {}
    def one(role, inputs=None):
        assert role == plan()[len(completed)], 'role order'
        request, native = launcher(role, inputs)
        body = old.consume(role, inputs, request, native, pins, grants[role])
        completed[role] = body
        if progress is not None:
            progress.append(role)
        return body
    for seed in REMAINING:
        inputs = []
        for mode in old.MODES:
            original = one(f'original:{seed}:{mode}:generate')
            replay = one(f'restored:{seed}:{mode}:generate')
            assert (original['extent'], original['sha256']) == (replay['extent'], replay['sha256']), 'producer parity'
            proof = one(f'original:{seed}:{mode}:audit', original)
            inputs.append(dict(mode=mode, record=original, proof=proof))
        metric_inputs.append(one(f'original:{seed}:metrics', inputs))
    final = one('final:acceptance', metric_inputs)
    assert list(completed) == plan() and len(metric_inputs) == 16
    return dict(final=final, completed=completed, original_cells=80, reused_originals=15,
                new_originals=65, new_replay_inclusive_geneses=130, cumulative_geneses=160,
                original_primary_remains_closed_incomplete=True, execution_admission=False)
