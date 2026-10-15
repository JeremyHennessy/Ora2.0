"""Finite primary receipt orchestration, never a VM or physics validator.

All grants/source/requests/native slots must be precharged by the trusted parent.
The launcher preserves the raw native result before this module can refuse it.
No function here creates a World, computes a label or grants primary admission.
"""
import hashlib
import json
from pathlib import Path

PRIMARY = tuple(range(1008900, 1008908))
UNSEEN = tuple(range(1009100, 1009108))
MODES = ('variation', 'no_variation', 'inheritance_disabled', 'model_disabled', 'history_misbound')
CONFIG = dict(version='INHERITANCE83-PRIMARY-v1', primary=list(PRIMARY), unseen=list(UNSEEN),
              modes=list(MODES), capacity=2, max_population=8, expansion_tick=1536,
              horizon=16384, admission='INHERITANCE83-v1')
M = 1024**2


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode('ascii')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def plan():
    result = []
    for seed in PRIMARY + UNSEEN:
        for mode in MODES:
            result.extend((f'original:{seed}:{mode}:generate', f'restored:{seed}:{mode}:generate',
                           f'original:{seed}:{mode}:audit'))
        result.append(f'original:{seed}:metrics')
    result.append('final:acceptance')
    assert len(result) == len(set(result)) == 257
    return result


def allocations():
    result = {}
    for role in plan():
        stem = role.replace(':', '-')
        result['data/'+stem+'.json'] = (64 if role.endswith(':generate') else 8)*M
        result['native/'+stem+'.json'] = M
        result['request/'+stem+'.json'] = 65536
    for bad in ('role', 'configuration', 'source', 'seal'):
        result['native/bad-'+bad+'.json'] = M
        result['request/bad-'+bad+'.json'] = 65536
    assert sum(result.values())+64*M < 12288*M
    return result


def consume(role, expected_input, request, native, pins, expected_grant):
    """Bind one already-retained native response to its exact sealed output."""
    from experiments import evidence_write_grant68 as transport
    from experiments.digital_cognitive76_child import pairs
    source = digest(pins); config = digest(CONFIG)
    assert request['configuration'] == CONFIG and request['source_files'] == pins
    assert (request['role'], request['kind'], request['input']) == (role, role.split(':')[-1], expected_input)
    assert request['source_sha'] == source and request['config_sha'] == config
    grant = request['grant']; signature = request['seal']
    assert grant == expected_grant, 'unregistered output grant'
    assert transport.digest(grant) == signature
    assert (grant['source_sha'], grant['config_sha'], grant['role']) == (source, config, role)
    maximum = (64 if role.endswith(':generate') else 8)*M
    assert type(grant['limit']) is int and grant['limit'] == maximum
    assert native['exit_code'] == 0 and not native['timed_out'] and not native['output_truncated']
    assert native['post_close_processes_exited'] and native['usage']['active_before_close'] == 0
    output = json.loads(native['output'], object_pairs_hook=pairs)
    assert output['role'] == role and output['source_sha'] == source and output['config_sha'] == config
    assert output.get('error') is None
    receipt = output['receipt']
    assert receipt['grant_sha256'] == signature
    assert (receipt['source_sha'], receipt['config_sha'], receipt['role']) == (source, config, role)
    path = Path(grant['root'])/grant['phase']/grant['name']
    # Reviewed plain-file/inode/hash guards; do not trust stdout's verified flags.
    for parent in path.parents: transport.plain(parent, True)
    info = transport.plain(path)
    assert (info.st_dev, info.st_ino) == (grant['device'], grant['inode'])
    assert type(receipt['extent']) is int and 0 < receipt['extent'] == info.st_size <= maximum
    # Streaming hash avoids loading a64MiB original into the controller.
    h = hashlib.sha256()
    with path.open('rb') as stream:
        import os
        opened = os.fstat(stream.fileno())
        assert (opened.st_dev, opened.st_ino, opened.st_size) == (info.st_dev, info.st_ino, info.st_size)
        for block in iter(lambda: stream.read(M), b''): h.update(block)
    after = transport.plain(path)
    assert (after.st_dev, after.st_ino, after.st_size) == (info.st_dev, info.st_ino, info.st_size)
    assert h.hexdigest() == receipt['sha256']
    return dict(path=str(path), extent=info.st_size, sha256=h.hexdigest())


def pipeline(launcher, pins, grants, progress=None):
    """Complete257 successful roles after four independently checked refusals.

    launcher(role, input) must save raw request/native/partials even on failure.
    It returns the exact request and native result. A refusal stops immediately;
    no later seed, replay, metric or final acceptance is selected in its place.
    """
    from experiments.digital_cognitive76_child import validate_grant
    # Freeze the preflight roster before any launcher can mutate an aliased dict.
    grants = json.loads(canonical(grants))
    assert set(grants) == set(plan())
    assert len({(g['device'], g['inode']) for g in grants.values()}) == 257
    for role in plan():
        g = grants[role]
        assert g['limit'] == (64 if role.endswith(':generate') else 8)*M
        validate_grant(dict(grant=g, grant_seal=digest(g),
                            configuration_sha256=digest(CONFIG), role=role),
                       digest(pins), 'recording' if role.endswith(':generate') else 'proof')
    completed = {}; metric_inputs = []
    def one(role, inputs=None):
        assert role == plan()[len(completed)], 'role order'
        request, native = launcher(role, inputs)
        spec = consume(role, inputs, request, native, pins, grants[role])
        completed[role] = spec
        if progress is not None: progress.append(role)
        return spec
    for seed in PRIMARY + UNSEEN:
        inputs = []
        for mode in MODES:
            original = one(f'original:{seed}:{mode}:generate')
            replay = one(f'restored:{seed}:{mode}:generate')
            assert (original['extent'], original['sha256']) == (replay['extent'], replay['sha256']), 'producer parity'
            proof = one(f'original:{seed}:{mode}:audit', original)
            inputs.append(dict(mode=mode, record=original, proof=proof))
        metric_inputs.append(one(f'original:{seed}:metrics', inputs))
    final = one('final:acceptance', metric_inputs)
    assert list(completed) == plan()
    return dict(final=final, completed=completed, original_cells=80, producer_replays=80,
                literal_audits=80, per_seed_metrics=16, final_acceptance_roles=1,
                primary_admitted=False, scope='Complete receipt orchestration only; physics and criteria are separate')
