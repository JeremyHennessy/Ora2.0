"""Finite primary-role worker. No controller registration on import.

Do not invoke a valid producer role until whole-controller admission and exact
source/config/input/grant/native/output qualification are complete.
"""
import gc
import hashlib
import json
import sys
from pathlib import Path

from experiments import digital_cognitive76_child as boundary
from experiments import evidence_write_grant68 as transport

PRIMARY = tuple(range(1008900, 1008908))
UNSEEN = tuple(range(1009100, 1009108))
MODES = ('variation', 'no_variation', 'inheritance_disabled', 'model_disabled', 'history_misbound')
CONFIG = dict(version='INHERITANCE83-PRIMARY-v1', primary=list(PRIMARY), unseen=list(UNSEEN),
              modes=list(MODES), capacity=2, max_population=8, expansion_tick=1536,
              horizon=16384, admission='INHERITANCE83-v1')
PROGRAM = [[7,2,1],[0,1,0],[19,0,1],[6,0,0],[1,0,0],[8,0,13],
           [4,1,1],[5,0,1],[8,0,10],[7,0,1],[10,0,0],[12,0,0],
           [7,0,1],[19,0,1],[21,0,0],[20,1,0],[7,0,1]]
enc = boundary.canonical


def role_parts(request):
    assert request['configuration'] == CONFIG, 'configuration'
    role = request['role']; kind = request['kind']
    assert type(role) is str and type(kind) is str, 'role'
    parts = role.split(':')
    if kind == 'acceptance':
        assert parts == ['final', 'acceptance'], 'role'
        assert type(request['input']) is list, 'input'
        return None, None, None
    if kind == 'metrics':
        assert len(parts) == 3 and parts[0] == 'original' and parts[2] == kind, 'role'
        export, seed_text = parts[:2]; mode = None
    else:
        assert kind in ('generate', 'audit') and len(parts) == 4 and parts[3] == kind, 'role'
        export, seed_text, mode = parts[:3]
        assert mode in MODES, 'role'
        assert (export, kind) in (('original', 'generate'), ('restored', 'generate'), ('original', 'audit')), 'role'
    seed = int(seed_text)
    assert seed_text == str(seed) and seed in PRIMARY + UNSEEN, 'role'
    if kind == 'generate':
        assert request['input'] is None, 'input'
    elif kind == 'metrics':
        assert type(request['input']) is list, 'input'
    else:
        assert type(request['input']) is dict, 'input'
    return export, seed, mode


def checked_row(spec, seed, mode):
    from experiments.digital_recording82_reader import read_spec
    row = read_spec(spec)
    assert row['configuration'] == CONFIG and row['seed'] == seed and row['mode'] == mode
    assert row['scientific_worlds'] == 1 and row['error'] is None
    assert row['state']['seed'] == seed and row['state']['mode'] == mode
    return row


def batch_metrics(seed, rows):
    """Consume one bound state/proof pair at a time; never hold five histories."""
    from experiments.digital_inheritance83_fitness import metrics
    values = []
    for mode, pair in zip(MODES, rows, strict=True):
        state, proof = pair
        assert state['seed'] == seed and state['mode'] == mode
        values.append(metrics(state, proof))
        del pair, state, proof
        gc.collect()
    assert len(values) == 5
    return dict(seed=seed, metrics=values)


def main():
    request = json.loads(boundary.bounded_bytes(Path(sys.argv[1]), 64*1024), object_pairs_hook=boundary.pairs)
    assert set(request) == {'configuration','source_files','source_sha','config_sha','role','kind','input','grant','seal'}, 'request'
    export, seed, mode = role_parts(request)
    root = Path.cwd(); pins = request['source_files']
    source = hashlib.sha256(enc(pins)).hexdigest(); config = hashlib.sha256(enc(CONFIG)).hexdigest()
    assert source == request['source_sha'] and config == request['config_sha'], 'source/config'
    assert boundary.verify_source(root, pins) == source
    kind = request['kind']; maximum = (64 if kind == 'generate' else 8)*1024**2
    assert request['grant']['limit'] == maximum, 'grant limit'
    boundary.validate_grant(dict(grant=request['grant'], grant_seal=request['seal'],
                                 configuration_sha256=config, role=request['role']),
                            source, 'recording' if kind == 'generate' else 'proof')
    if kind == 'generate':
        from experiments.digital_inheritance83_world import World
        from experiments.digital_memory80_recording import terminal_view
        world = World(seed, capacity=2, mode=mode, max_population=8, expansion_tick=1536,
                      admission='INHERITANCE83-v1')
        first_error = None
        try:
            while world.tick < 16384 and world.step(): pass
        except BaseException as error:
            first_error = repr(error)
        # Borrow only after stepping ends; never mutate while recording.
        value = dict(configuration=CONFIG, seed=seed, mode=mode, scientific_worlds=1,
                     state=terminal_view(world.__dict__), error=first_error)
    elif kind == 'audit':
        from experiments.digital_inheritance83_endpoint import evaluate
        assert 'experiments.digital_inheritance83_world' not in sys.modules
        row = checked_row(request['input'], seed, mode)
        value = evaluate(row['state'], seed=seed, mode=mode, max_population=8,
                         expansion_tick=1536, program=PROGRAM, horizon=16384,
                         admission='INHERITANCE83-v1')
    elif kind == 'metrics':
        assert 'experiments.digital_inheritance83_world' not in sys.modules
        assert 'experiments.digital_inheritance83_referee' not in sys.modules
        inputs = request['input']
        assert len(inputs) == 5 and [i['mode'] for i in inputs] == list(MODES)
        def rows():
            for item in inputs:
                assert set(item) == {'mode', 'record', 'proof'}
                row = checked_row(item['record'], seed, item['mode'])
                proof = boundary.read_spec(item['proof'], 8*1024**2)
                yield row['state'], proof
                del row, proof
        value = batch_metrics(seed, rows())
    else:
        from experiments.digital_inheritance83_acceptance import interpret
        assert all(n not in sys.modules for n in ('experiments.digital_inheritance83_world',
                   'experiments.digital_inheritance83_referee', 'experiments.digital_inheritance83_fitness'))
        assert len(request['input']) == 16
        values = [boundary.read_spec(spec, 8*1024**2) for spec in request['input']]
        value = interpret(values)
    boundary.module_origins(root, pins)
    assert boundary.verify_source(root, pins) == source
    receipt = transport.record(request['grant'], request['seal'], source, config, request['role'], value)
    print(enc(dict(role=request['role'], source_sha=source, config_sha=config,
                   receipt=receipt, error=value.get('error'))).decode())


if __name__ == '__main__':
    main()
