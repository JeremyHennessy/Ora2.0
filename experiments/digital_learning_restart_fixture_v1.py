"""Finite supplied-program learning persistence fixture; no primary admission.

Four manually registered roles. Never schedules, repairs or retries itself.
"""
import hashlib
import json
import os
from pathlib import Path
import sys


def enc(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('ascii')


def sha(b):
    return hashlib.sha256(b).hexdigest()


def save(path, value, limit=2*1024**2):
    raw = value if isinstance(value, bytes) else enc(value)
    assert len(raw) <= limit
    with path.open('xb') as stream:
        assert stream.write(raw) == len(raw)
        stream.flush(); os.fsync(stream.fileno())
    return dict(path=str(path), extent=len(raw), sha256=sha(raw))


def main():
    assert len(sys.argv) == 4 and not sys.flags.optimize
    role, config_path, config_hash = sys.argv[1:]
    raw = Path(config_path).read_bytes(); assert sha(raw) == config_hash
    config = json.loads(raw); assert enc(config) == raw
    assert config['schema'] == 'ORA-LEARNING-RESTART-SOFTWARE-v1'
    assert config['primary_admission'] is False
    root = Path(config['root']); source = root / 'source/learning'
    for name, value in config['source_pins'].items():
        b = (source / name).read_bytes()
        assert len(b) == value['extent'] and sha(b) == value['sha256']
    sys.path.insert(0, str(source))
    from experiments.digital_budgeted_transfer_v1 import Fixture, SOFTWARE_ONLY
    from experiments.digital_budgeted_transfer_referee_v1 import verify
    # Previously disclosed authored reachability witness, used ONLY as apparatus.
    code = [[7,4,1],[0,1,0],[19,0,1],[25,5,7],[6,0,0],[1,0,0],
            [25,0,1],[24,0,1],[20,1,0],[25,5,4],[7,0,1]]
    def cut():
        f = Fixture(code, mask=9, admission=SOFTWARE_ONLY)
        blank = json.loads(json.dumps(f.world.entities[0]['memory']))
        for _ in range(256):
            assert f.step()
            if f.completed == 4 and f.world.entities[0]['pc'] == 1:
                assert f.world.entities[0]['memory'] != blank
                return f, blank
        raise AssertionError('Declared acquisition checkpoint not reached')
    if role == 'reference':
        f, blank = cut(); checkpoint = f.snapshot()
        result = f.run_fixture(); assert verify(code, 9, f.order, f.rows, result)
        save(root / 'reference.json', dict(checkpoint=checkpoint, final=f.snapshot(), result=result,
                                           blank_memory=blank, supplied_program=True))
    elif role == 'crash':
        f, blank = cut()
        checkpoint = f.snapshot(); committed = save(root / 'checkpoint.json', checkpoint)
        head = dict(schema='ORA-LEARNING-RESTART-HEAD-v1', checkpoint=committed,
                    source_sha256=config['source_sha256'], committed_tick=f.world.tick)
        save(root / 'head.json', head, 4096)
        for _ in range(3):
            assert f.step()
        orphan = enc(f.snapshot())
        save(root / 'orphan.json', orphan)
        save(root / 'next.pending', orphan[:len(orphan)//2])
        print(enc(dict(role=role, committed_tick=head['committed_tick'], observed_tick=f.world.tick,
                       crash_exit=78, primary_admission=False)).decode(), flush=True)
        os._exit(78)
    elif role == 'recover':
        head = json.loads((root / 'head.json').read_bytes())
        assert head['source_sha256'] == config['source_sha256']
        assert Path(head['checkpoint']['path']) == root / 'checkpoint.json'
        raw = (root / 'checkpoint.json').read_bytes()
        assert len(raw) == head['checkpoint']['extent'] and sha(raw) == head['checkpoint']['sha256']
        sealed = json.loads(raw)
        f = Fixture.restore(sealed, admission=SOFTWARE_ONLY)
        assert f.snapshot() == sealed and f.world.tick == head['committed_tick']
        recovered_memory = json.loads(json.dumps(f.world.entities[0]['memory']))
        result = f.run_fixture(); assert verify(code, 9, f.order, f.rows, result)
        reference = json.loads((root / 'reference.json').read_bytes())
        assert sealed == reference['checkpoint'] and f.snapshot() == reference['final'] and result == reference['result']
        assert recovered_memory != reference['blank_memory']
        orphan = json.loads((root / 'orphan.json').read_bytes())
        assert orphan['payload']['world']['tick'] == head['committed_tick'] + 3
        save(root / 'recovery.json', dict(exact_checkpoint=True, exact_final_state=True,
             exact_decisions_and_costs=True, acquired_memory_retained=True,
             committed_tick=head['committed_tick'], discarded_uncommitted_steps=3,
             orphan_promoted=False, result=result, primary_admission=False,
             limitation='Supplied authored fixture. Restore constructs a validation object and independently replays the saved prefix; no real-world power-loss or continuous-run proof.'))
    elif role == 'tamper':
        head = json.loads((root / 'head.json').read_bytes())
        raw = (root / 'checkpoint.json').read_bytes()
        corrupted = raw[:-1] + bytes([raw[-1] ^ 1])
        save(root / 'corrupted-copy.json', corrupted)
        assert sha(corrupted) != head['checkpoint']['sha256']
        save(root / 'tamper.json', dict(corruption_refused_before_restore=True,
             committed_file_unchanged=sha(raw) == head['checkpoint']['sha256'],
             limitation='Digest corruption only; no adversarial authenticated-head replacement proof.'))
    else:
        raise ValueError('Undeclared role')
    print(enc(dict(role=role, passed=True, primary_admission=False)).decode(), flush=True)


if __name__ == '__main__':
    main()
