"""Read-only HEARTBEAT-03 replay, including full PRNG and object ancestry."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import random

from experiments.heartbeat_checkpoint_audit import canonical, digest, decode, utc, hex_string, read_small
from experiments import material_turnover_audit as law

ROOT = Path(__file__).resolve().parents[1]
FILES = ('experiments/heartbeat_world.py', 'experiments/heartbeat_world_audit.py',
         'experiments/material_turnover.py', 'experiments/material_turnover_audit.py',
         'experiments/heartbeat_checkpoint.py', 'experiments/heartbeat_checkpoint_audit.py',
         'data/turnover01-law-v1.json', 'docs/HEARTBEAT-03-CONTRACT.md')


def source_hashes():
    return {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES}


def validate_config(c):
    if not isinstance(c, dict) or set(c) != {'seed', 'work', 'max_ticks'} or type(c['seed']) is not int or c['seed'] != 1:
        raise ValueError('Existing seed 1 engineering fixture only')
    if type(c['work']) is not int or not 0 <= c['work'] <= 1000 or type(c['max_ticks']) is not int or not 1 <= c['max_ticks'] <= 128:
        raise ValueError('Finite world bounds')


def tuples(v):
    return tuple(tuples(x) for x in v) if isinstance(v, list) else v


def genesis(config, run_id):
    world, _ = law.regenerate(config['seed'], config['work'])
    rng = random.Random(config['seed'])
    for bound in [2]*32+[v for _ in range(32) for v in (8, 2)]:
        rng.randrange(bound)
    return dict(run_id=run_id, simulation_tick=0, noise_cursor=0,
                rng_state=json.loads(canonical(rng.getstate())), world=world,
                event_chain=digest(world), object_history=copy.deepcopy(world['objects']))


def advance(old):
    rng = random.Random()
    rng.setstate(tuples(old['rng_state']))
    draw = [rng.randrange(b) for b in (8, 8, 65536, 65536, 65536)]
    tick = old['simulation_tick']
    world, opp, result = law.transition(old['world'], 'active', tick, draw)
    event = dict(tick=tick, draw=draw, work_before=old['world']['W'], opportunities=opp, result=result,
                 before_sha256=digest(old['world']), after_sha256=digest(world), previous_sha256=old['event_chain'])
    event['event_sha256'] = digest(event)
    history = copy.deepcopy(old['object_history'])
    if result['product_id'] is not None:
        oid = result['product_id']
        if oid in history:
            raise ValueError('Object identity reused')
        history[oid] = copy.deepcopy(world['objects'][oid])
    state = dict(run_id=old['run_id'], simulation_tick=tick+1, noise_cursor=old['noise_cursor']+1,
                 rng_state=json.loads(canonical(rng.getstate())), world=world,
                 event_chain=event['event_sha256'], object_history=history)
    if law.ledger(world) != law.ledger(old['world']):
        raise ValueError('World conservation')
    return state, event


def inspect(output, revision=None, current=None, stale_seconds=5):
    if type(stale_seconds) not in (int, float) or not 0 < stale_seconds < float('inf'):
        raise ValueError('Finite positive stale threshold')
    output = Path(output)
    manifest = decode(read_small(output/'manifest.json'))
    if set(manifest) != {'schema', 'config', 'identity'} or manifest['schema'] != 'heartbeat03-v1':
        raise ValueError('Manifest schema')
    c, identity = manifest['config'], manifest['identity']
    validate_config(c)
    if set(identity) != {'world_id', 'source_revision', 'config_sha256', 'python', 'source_sha256', 'run_id'} or not isinstance(identity['world_id'], str) or not 1 <= len(identity['world_id']) <= 200:
        raise ValueError('World identity')
    if not hex_string(identity['source_revision'], 40) or identity['config_sha256'] != digest(c) or identity['run_id'] != digest({k: v for k, v in identity.items() if k != 'run_id'}):
        raise ValueError('Identity/source digest')
    if revision is not None and identity['source_revision'] != revision:
        raise ValueError('Source revision mismatch')
    if identity['python'] != platform.python_version() or canonical(identity['source_sha256']) != canonical(source_hashes()):
        raise ValueError('Source/Python mismatch')
    raw = read_small(output/'frames.jsonl')
    if not raw or not raw.endswith(b'\n'):
        raise ValueError('Missing genesis/partial tail')
    frames = [decode(line) for line in raw.splitlines()]
    if not 1 <= len(frames) <= 230:
        raise ValueError('Finite frame bound')
    state = genesis(c, identity['run_id'])
    chain, previous, time = '0'*64, None, None
    states = []
    keys = {'schema', 'seq', 'epoch', 'state', 'event', 'state_sha256', 'last_heartbeat', 'status', 'reason', 'previous_sha256', 'frame_sha256'}
    for index, f in enumerate(frames):
        if set(f) != keys or f['schema'] != 'heartbeat03-v1' or type(f['seq']) is not int or f['seq'] != index or type(f['epoch']) is not int or not 0 <= f['epoch'] <= 32:
            raise ValueError('Frame schema/sequence/epoch')
        moment = utc(f['last_heartbeat'])
        if time is not None and moment < time:
            raise ValueError('Backward heartbeat')
        expected_event = None
        if previous is None:
            if f['epoch'] != 0 or (f['status'], f['reason']) != ('running', 'ready'):
                raise ValueError('Genesis lifecycle')
            states.append(copy.deepcopy(state))
        else:
            if previous['status'] == 'stopped':
                raise ValueError('After terminal')
            if (f['status'], f['reason']) == ('running', 'resumed'):
                if f['epoch'] != previous['epoch']+1:
                    raise ValueError('Resume epoch')
            else:
                if previous['status'] != 'running' or f['epoch'] != previous['epoch']:
                    raise ValueError('Non-running advance')
                if (f['status'], f['reason']) == ('running', 'advanced'):
                    if state['simulation_tick'] >= c['max_ticks']:
                        raise ValueError('Extended horizon')
                    state, expected_event = advance(state)
                    states.append(copy.deepcopy(state))
                elif (f['status'], f['reason']) == ('paused', 'operator_pause'):
                    pass
                elif (f['status'], f['reason']) == ('stopped', 'tick_limit') and state['simulation_tick'] == c['max_ticks']:
                    pass
                else:
                    raise ValueError('False lifecycle')
        if canonical(f['state']) != canonical(state) or canonical(f['event']) != canonical(expected_event):
            raise ValueError('World/PRNG/cursor/history/event divergence')
        if f['state_sha256'] != digest(state) or f['previous_sha256'] != chain or f['frame_sha256'] != digest({k: v for k, v in f.items() if k != 'frame_sha256'}):
            raise ValueError('Hash chain')
        previous, chain, time = f, f['frame_sha256'], moment
    checkpoint = decode(read_small(output/'checkpoint.json')) if (output/'checkpoint.json').exists() else None
    if (output/'checkpoint.json').exists():
        seq = checkpoint.get('seq') if isinstance(checkpoint, dict) else None
        if type(seq) is not int or not 0 <= seq < len(frames) or canonical(checkpoint) != canonical(frames[seq]):
            raise ValueError('Non-prefix checkpoint')
    age = ((datetime.now(timezone.utc) if current is None else utc(current))-time).total_seconds()
    if age < 0:
        raise ValueError('Future heartbeat')
    status = previous['status']
    report = dict(run_id=identity['run_id'], world_id=identity['world_id'], verified_revision=identity['source_revision'],
                  verified_simulation_tick=state['simulation_tick'], noise_cursor=state['noise_cursor'], epoch=previous['epoch'],
                  verified_frames=len(frames), verified_state_sha256=digest(state), complete_reference_state_continuity=True,
                  live_objects=len(state['world']['objects']), historic_objects=len(state['object_history']), atoms=len(state['world']['atoms']),
                  work=state['world']['W'], heat=state['world']['heat'], checkpoint_current=checkpoint is not None and checkpoint['seq'] == len(frames)-1,
                  checkpoint_seq=None if checkpoint is None else checkpoint['seq'], reported_status=status,
                  observed_status='stale' if status == 'running' and age > stale_seconds else 'reported_running' if status == 'running' else status,
                  heartbeat_age_seconds=age, process_health='unverified', evolution_claim=False)
    return dict(manifest=manifest, frames=frames, states=states, report=report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(inspect(args.input_dir, args.source_revision)['report'], sort_keys=True, indent=2))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f'Rejected evidence: {exc}\n')
