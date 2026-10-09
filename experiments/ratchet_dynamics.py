"""RATCHET-02 installed apparatus under unscreened, reversible random dynamics."""
import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path
import random
import struct
from .evidence_budget import Budget
from .ratchet_gate import ARMS, START, edges, heat, packed, witness


def world(seed, arm, barriers):
    noise = random.Random(seed)
    digest = hashlib.sha256()
    state = START
    token_states = ['F']*16
    path, event_steps = [], []
    stopped = False
    pre_replace = None
    depleted = None
    for step in range(4096):
        if step == 2048:
            pre_replace = list(state)+[heat(state)]
            if state[2] >= 7:
                state = dict(edges(state,arm))[(5,1)]
                path.append([5,1]);event_steps.append(step)
            else:
                stopped = True
        c = noise.randrange(5)
        d = 1 if noise.getrandbits(1) else -1
        token = noise.getrandbits(4)
        draw = noise.getrandbits(32)
        digest.update(struct.pack('<IIII',c,int(d>0),token,draw))
        if stopped:
            continue
        choices = dict(edges(state,arm))
        if (c,d) not in choices:
            continue
        chemical = c in (0,4)
        if chemical and token_states[token] != ('F' if d > 0 else 'W'):
            continue
        new = choices[(c,d)]
        barrier = barriers[0 if chemical else 2 if c == 2 else 1]
        exponent = barrier+int(chemical and arm=='isotropic')+max(0,heat(state)-heat(new))
        if not 0 <= exponent <= 32:
            raise ValueError('Exact draw precision')
        if draw < 2**(32-exponent):
            if chemical:
                token_states[token] = 'W' if d > 0 else 'F'
            state = new
            path.append([c,d]);event_steps.append(step)
            if depleted is None and state[0] == 0:
                depleted = step
    # The actual selected token is retained, not the gate's canonical witness
    # choice. Reconstruct event identities from the independently saved draws.
    noise2 = random.Random(seed)
    token_history = [dict(id=i,state='F',transformations=[]) for i in range(16)]
    objects = [dict(id=0,atoms=[0,1,2],parent=None,construction_work=6,alive=True)]
    event_tokens = []
    k = 0
    for step in range(4096):
        if k < len(path) and event_steps[k] == step and path[k][0] == 5:
            objects[0]['alive'] = False
            objects.append(dict(id=1,atoms=[0,1,2],parent=0,construction_work=6,destruction_work=1,alive=True))
            event_tokens.append(None);k += 1
        c = noise2.randrange(5);d = 1 if noise2.getrandbits(1) else -1
        token = noise2.getrandbits(4);noise2.getrandbits(32)
        if k < len(path) and event_steps[k] == step:
            if path[k] != [c,d]:
                raise ValueError('Event/draw ordering')
            if c in (0,4):
                token_history[token]['state'] = 'W' if d > 0 else 'F'
                token_history[token]['transformations'].append(dict(event=k,machine=objects[-1]['id'],route=[c,d]))
                event_tokens.append(token)
            else:
                event_tokens.append(None)
            k += 1
    if k != len(path) or token_states != [t['state'] for t in token_history]:
        raise ValueError('Labelled inventory')
    w = witness(arm,path)
    w['tokens'] = token_history
    w['objects'] = objects
    w['events'] = [dict(action=p,token=t,machine=0 if step<2048 else int(not stopped)) for p,t,step in zip(path,event_tokens,event_steps)]
    return dict(schema='ratchet02',seed=seed,arm=arm,barriers=list(barriers),attempts=4096,
                event_steps=event_steps,draw_sha256=digest.hexdigest(),
                rng_sha256=hashlib.sha256(packed(noise.getstate())).hexdigest(),
                pre_replace=pre_replace,stopped_unfunded=stopped,first_depletion=depleted,final=w)


def main():
    p = argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--revision',required=True)
    a = p.parse_args();b = Budget(a.output,dict(raw=48*1024**2,failure=2*1024**2),50*1024**2)
    try:
        with b.create('raw','manifest.json') as out:
            out.write(packed(dict(revision=a.revision,worlds=256,attempts=1048576,founder_free=False)))
        for i,barriers in enumerate(itertools.product(range(4),repeat=3)):
            for arm in ARMS:
                with b.create('raw',f'{78000+i}-{arm}.json') as out:
                    out.write(packed(world(78000+i,arm,barriers)))
    finally:
        with b.create('failure','budget.json',1024**2) as out:
            out.write(packed(copy.deepcopy(b.snapshot())))


if __name__ == '__main__':
    main()
