"""Explicit finite sequence-world launch/resume; no background service."""
import argparse
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import random

from experiments.heartbeat_checkpoint import writer_lock, write_file, FAULTS
from experiments.heartbeat_world_audit import inspect, validate_config, source_hashes, tuples
from experiments.material_turnover import Engine, genesis, encode, digest


def initial(config, run_id):
    world, _ = genesis(config['seed'], config['work'])
    rng = random.Random(config['seed'])
    for _ in range(32):
        rng.randrange(2)
    for _ in range(32):
        rng.randrange(8)
        rng.randrange(2)
    return dict(run_id=run_id, simulation_tick=0, noise_cursor=0, rng_state=json.loads(encode(rng.getstate())),
                world=world, event_chain=digest(world), object_history=copy.deepcopy(world['objects']))


def next_state(old):
    generator = random.Random()
    generator.setstate(tuples(old['rng_state']))
    request = [generator.randrange(b) for b in (8, 8, 65536, 65536, 65536)]
    engine = Engine(old['world'], 'active')
    engine.chain = old['event_chain']
    engine.step(old['simulation_tick'], request)
    event = engine.events[0]
    history = copy.deepcopy(old['object_history'])
    oid = event['result']['product_id']
    if oid is not None:
        if oid in history:
            raise ValueError('Object ID reused')
        history[oid] = copy.deepcopy(engine.s['objects'][oid])
    return dict(run_id=old['run_id'], simulation_tick=old['simulation_tick']+1, noise_cursor=old['noise_cursor']+1,
                rng_state=json.loads(encode(generator.getstate())), world=engine.s, event_chain=event['event_sha256'],
                object_history=history), event


def run(output, world_id, revision, work=96, max_ticks=32, seed=1, resume=False,
        pause_after=None, fault_tick=None, fault_point=None):
    config = dict(seed=seed, work=work, max_ticks=max_ticks)
    validate_config(config)
    if not isinstance(world_id, str) or not 1 <= len(world_id) <= 200 or not isinstance(revision, str) or len(revision) != 40 or any(c not in '0123456789abcdef' for c in revision):
        raise ValueError('World and exact revision required')
    for tick in (pause_after, fault_tick):
        if tick is not None and (type(tick) is not int or not 1 <= tick <= max_ticks):
            raise ValueError('Control within original horizon')
    if (fault_tick is None) != (fault_point is None) or fault_point is not None and fault_point not in FAULTS:
        raise ValueError('Paired fault point and tick')
    identity = dict(world_id=world_id, source_revision=revision, config_sha256=digest(config),
                    python=platform.python_version(), source_sha256=source_hashes())
    identity['run_id'] = digest(identity)
    output = Path(output)
    if not resume:
        output.mkdir(parents=True, exist_ok=False)
    with writer_lock(output, create=not resume):
        if resume:
            evidence = inspect(output, revision)
            if encode(evidence['manifest']['identity']) != encode(identity) or encode(evidence['manifest']['config']) != encode(config):
                raise ValueError('World/source/config mismatch')
            last = evidence['frames'][-1]
            state, epoch, seq, chain = copy.deepcopy(last['state']), last['epoch'], last['seq']+1, last['frame_sha256']
            if last['status'] != 'stopped' and epoch >= 32:
                raise ValueError('Finite resume cap')
            if last['status'] != 'stopped' and any(t is not None and t <= state['simulation_tick'] for t in (pause_after, fault_tick)):
                raise ValueError('Control must target future tick')
            if not evidence['report']['checkpoint_current']:
                write_file(output/'checkpoint.pending', last)
                (output/'checkpoint.pending').replace(output/'checkpoint.json')
            if last['status'] == 'stopped':
                return last
            epoch += 1
        else:
            write_file(output/'manifest.json', dict(schema='heartbeat03-v1', config=config, identity=identity))
            state = initial(config, identity['run_id'])
            epoch, seq, chain = 0, 0, '0'*64

        def frame(status, reason, event=None):
            nonlocal seq, chain
            value = dict(schema='heartbeat03-v1', seq=seq, epoch=epoch, state=copy.deepcopy(state), event=event,
                         state_sha256=digest(state), last_heartbeat=datetime.now(timezone.utc).isoformat(),
                         status=status, reason=reason, previous_sha256=chain)
            value['frame_sha256'] = digest(value)
            def fault(point):
                if event is not None and state['simulation_tick'] == fault_tick and point == fault_point:
                    os._exit(FAULTS[point])
            fault('pre_commit')
            with (output/'frames.jsonl').open('ab') as journal:
                journal.write((encode(value)+'\n').encode())
                journal.flush()
                os.fsync(journal.fileno())
            fault('post_journal')
            write_file(output/'checkpoint.pending', value)
            fault('post_pending')
            (output/'checkpoint.pending').replace(output/'checkpoint.json')
            fault('post_checkpoint')
            seq, chain = seq+1, value['frame_sha256']
            return value
        frame('running', 'resumed' if resume else 'ready')
        while state['simulation_tick'] < max_ticks:
            state, event = next_state(state)
            frame('running', 'advanced', event)
            if state['simulation_tick'] == pause_after:
                return frame('paused', 'operator_pause')
        return frame('stopped', 'tick_limit')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--world-id', required=True)
    parser.add_argument('--source-revision', required=True)
    parser.add_argument('--work', type=int, default=96)
    parser.add_argument('--max-ticks', type=int, default=32)
    parser.add_argument('--seed', type=int, default=1)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--pause-after', type=int)
    parser.add_argument('--fault-tick', type=int)
    parser.add_argument('--fault-point', choices=FAULTS)
    args = parser.parse_args()
    try:
        run(args.output_dir, args.world_id, args.source_revision, args.work, args.max_ticks, args.seed,
            args.resume, args.pause_after, args.fault_tick, args.fault_point)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f'Rejected run: {exc}\n')
