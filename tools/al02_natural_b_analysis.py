"""Read-only AL02 natural B-use metrics. No simulator or execution entry."""
from hashlib import sha256
import json
from statistics import mean, stdev

from experiments.al02_depletion_suffix import verify_pair

DOMAIN = 'ORA-AL02-NATURAL-B-PANEL-20261109-v1'
ANCHOR = 'e136d0e1a10895b2e500766026957ed987f0a9cd4365776f589797eac9a416d7'
CONSUMED = 8195177122164069225


def contexts():
    rows = []
    seen = {CONSUMED}
    draw = 0
    while len(rows) < 128:
        label = f'{DOMAIN}|{ANCHOR}|{draw:08d}'
        digest = sha256(label.encode('ascii')).hexdigest()
        seed = int(digest[:16], 16)
        if seed not in seen:
            index = len(rows)
            rows.append(dict(index=index, draw=draw, context=label, context_sha256=digest,
                             seed=seed, attempt=f'attempt-{index:03d}'))
            seen.add(seed)
        draw += 1
    return rows


def lineage(events):
    actors, writes, origins, attempts = {}, {}, [], []
    for event in events:
        kind = event['kind']
        tick = event['tick']
        if kind == 'GENESIS':
            if 1 in event['tape_ops']:
                raise ValueError('Engineered founder is outside natural panel')
            actors[event['organism_id']] = dict(tape=event['tape_ops'], slots={}, parent=None,
                                               born=tick, children=[], same_program_children=[], death=None)
        elif kind == 'COPY_WRITE':
            origin = None
            if event['written_op'] == 1:
                if event['mutated']:
                    origin = event['event_id']
                    origins.append(dict(event_id=origin, tick=tick, parent=event['parent_id'],
                                        slot=event['nursery_index']))
                else:
                    origin = actors[event['parent_id']]['slots'][event['source_index']]
            writes[event['event_id']] = origin
        elif kind == 'BIRTH':
            parent, child = event['parent_id'], event['child_id']
            tape = event['child_genome_ops']
            slots = {i: writes[write] for i, write in enumerate(event['copy_event_ids']) if tape[i] == 1}
            actors[child] = dict(tape=tape, slots=slots, parent=parent, born=tick, children=[],
                                 same_program_children=[], death=None)
            actors[parent]['children'].append(child)
            if tape == actors[parent]['tape']:
                actors[parent]['same_program_children'].append(child)
        elif kind == 'DEATH':
            actors[event['organism_id']]['death'] = dict(tick=tick, reason=event['reason'])
        elif kind == 'EXEC' and event['opcode'] == 1:
            attempts.append(dict(tick=tick, actor=event['organism_id'], outcome=event['outcome'],
                                 stock_after=event['food_b'], net_energy=event['energy_after']-event['energy_before']))
    return dict(origins=origins, actors=actors, attempts=attempts,
                meals=sum(row['outcome']=='ate_b' for row in attempts))


def analyze_pair(seed, raw, pin, branches):
    result = verify_pair(seed, raw, pin, branches)
    prefix = json.loads(raw)['state']['events']
    return dict(result=result, prefix=lineage(prefix),
                branches={role:lineage(prefix+record['events']) for role,record in branches.items()})


def summarize(rows):
    if [row['index'] for row in rows] != list(range(128)):
        raise ValueError('Every committed context must occur exactly once in order')
    allowed = {'accepted','missing','invalid','failed','not_run'}
    if any(row['status'] not in allowed for row in rows):
        raise ValueError('Unknown evidence status')
    differences = [row['result']['contrast'] for row in rows if row['status']=='accepted']
    complete = len(differences)==128
    return dict(committed=128, counts={s:sum(row['status']==s for row in rows) for s in sorted(allowed)},
                distribution=differences, all_context_mean=mean(differences) if complete else None,
                all_context_se=stdev(differences)/128**0.5 if complete else None,
                observed_only_mean=mean(differences) if differences else None)
