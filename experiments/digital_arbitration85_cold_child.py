"""Frozen diagnostic roles only; all custody guards precede World imports."""
import hashlib
import json
import sys
from pathlib import Path
from experiments import digital_cognitive76_child as boundary
from experiments import evidence_write_grant68 as transport
from experiments.digital_arbitration85_source import programme

M = 1024**2
CONFIG = dict(version='ARBITRATION85-COLD-REFERENCE-v1', seed=2100081,
              cases=[[8, 0, 'constant'], [8, 0, 'model']], mode='no_variation',
              max_population=1, expansion_tick=0, horizon=128, software_only=True,
              contract_sha256='01367ae6c8a5b7fdd1cee93f1af9c08ba268154402c7bd1db5ffca9c1ad94187')
ROLES = ('original:generate', 'original:audit', 'restored:generate')
enc = boundary.canonical


def scope(request):
    assert type(request) is dict and set(request) == {
        'configuration', 'source_files', 'source_sha', 'config_sha', 'role',
        'kind', 'input', 'grant', 'seal'}
    assert enc(request['configuration']) == enc(CONFIG)
    assert request['role'] in ROLES
    assert request['kind'] == request['role'].split(':')[1]
    if request['kind'] == 'generate':
        assert request['input'] is None
    else:
        assert type(request['input']) is dict
    return request['kind']


def main():
    request = json.loads(boundary.bounded_bytes(Path(sys.argv[1]), 64*1024),
                         object_pairs_hook=boundary.pairs)
    kind = scope(request)
    root = Path.cwd()
    assert Path(__file__).resolve() == root/'experiments/digital_arbitration85_cold_child.py'
    pins = request['source_files']
    assert 'experiments/digital_arbitration85_cold_child.py' in pins
    source = hashlib.sha256(enc(pins)).hexdigest()
    config = hashlib.sha256(enc(CONFIG)).hexdigest()
    assert source == request['source_sha'] and config == request['config_sha']
    assert boundary.verify_source(root, pins) == source
    assert request['grant']['limit'] == (8*M if kind == 'generate' else M)
    boundary.validate_grant(dict(grant=request['grant'], grant_seal=request['seal'],
        configuration_sha256=config, role=request['role']), source,
        'recording' if kind == 'generate' else 'proof')
    error = None
    if kind == 'generate':
        from experiments.digital_memory80 import World
        records = []
        attempts = 0
        for descriptor in CONFIG['cases']:
            world = None
            code = programme(*descriptor)
            try:
                attempts += 1
                world = World(CONFIG['seed'], descriptor[0], CONFIG['mode'],
                              CONFIG['max_population'], CONFIG['expansion_tick'], code=code)
                state = world.run(CONFIG['horizon'])
                records.append(dict(descriptor=descriptor, programme=code, state=state))
            except BaseException as exc:
                error = repr(exc)
                partial = None
                partial_error = None
                try:
                    if world is not None:
                        partial = world.snapshot()
                except BaseException as recovery:
                    partial_error = repr(recovery)
                records.append(dict(descriptor=descriptor, programme=code, error=error,
                                    state=partial, partial_error=partial_error))
                break
        value = dict(version=CONFIG['version'], software_only=True,
                     scientific_worlds=0, scientific_targets=0,
                     software_genesis_attempts=attempts, records=records, error=error)
    else:
        from experiments.digital_memory80_referee import audit
        assert 'experiments.digital_memory80' not in sys.modules
        data = boundary.read_spec(request['input'], 8*M)
        assert data['version'] == CONFIG['version'] and data['software_only'] is True
        assert data['scientific_worlds'] == data['scientific_targets'] == 0
        assert data['error'] is None and data['software_genesis_attempts'] == 2
        assert [r['descriptor'] for r in data['records']] == CONFIG['cases']
        summaries = []
        for row in data['records']:
            code = programme(*row['descriptor'])
            assert row['programme'] == code
            state = row['state']
            proof = audit(state, seed=CONFIG['seed'], mode=CONFIG['mode'],
                          max_population=CONFIG['max_population'],
                          expansion_tick=CONFIG['expansion_tick'], program=code,
                          horizon=CONFIG['horizon'])
            actions = [e for e in state['events'] if 'attempt' in e]
            summaries.append(dict(descriptor=row['descriptor'], proof=proof,
                attempts=len(actions), acquisitions=sum(e['attempt']['success'] for e in actions),
                captured=sum(e.get('captured', 0) for e in actions),
                penalties=sum(e.get('penalty', 0) for e in state['events']),
                last_opcode=state['events'][-1]['decoded'][0],
                birth_count=state['births'], dna_writes=state['writes']))
        value = dict(verified=True, version=CONFIG['version'], software_only=True,
                     scientific_worlds=0, scientific_targets=0, producer_imported=False,
                     evidence_inputs=request['input'], summaries=summaries, stage_credit=False)
    boundary.module_origins(root, pins)
    assert boundary.verify_source(root, pins) == source
    receipt = transport.record(request['grant'], request['seal'], source, config,
                               request['role'], value)
    print(enc(dict(role=request['role'], source_sha=source, config_sha=config,
                   receipt=receipt)).decode())
    assert error is None, error


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        print(enc(dict(rejected_before_world='experiments.digital_memory80' not in sys.modules)).decode())
        raise
