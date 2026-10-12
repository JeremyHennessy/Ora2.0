"""Full-event measurement after independent VM/custody verification by caller.

No World execution. Reading events cannot authenticate their physical truth;
the caller must bind them to complete independent VM proof and source seals.
"""
import hashlib
import json
from .digital_history33_endpoint import validate


def extract(row):
    events = row['final']['events']; program = row['genesis_program']
    if (row['control_mode'] not in ('intact','retained_disabled','own_disrupted')
            or not 1 <= len(events) <= 512 or not 1 <= len(program) <= 32
            or any(type(t) is not list or len(t) != 3 or any(type(v) is not int or not 0 <= v < 32 for v in t)
                   or t[0] not in (1,2,3,4,5,6,7,8,18) for t in program)):
        raise ValueError('input scope')
    won = {}; last = None; reads = []; death = None
    for tick,e in enumerate(events,1):
        if type(e['tick']) is not int or e['tick'] != tick or type(e['actor']) is not int or e['actor'] != 0:
            raise ValueError('event identity/order')
        op = e['decoded'][0]
        if type(op) is not int or op not in (1,2,3,4,5,6,7,8,18):
            raise ValueError('used channel outside scope')
        if death is not None: raise ValueError('events after death')
        if 'death' in e: death=tick
        if op == 6:
            a=e.get('attempt'); last=None
            if a is not None:
                if any(type(a[k]) is not int for k in ('packet','port','success')) or not 0 <= a['packet'] < 32 or a['port'] not in (0,1) or a['success'] not in (0,1):
                    raise ValueError('attempt')
                last=(tick,a['success'])
                if a['success']:
                    if a['packet'] in won: raise ValueError('duplicate packet win')
                    won[a['packet']]=tick
        elif 'attempt' in e: raise ValueError('attempt outside ACT')
        if op == 1:
            sample=e['control']['personal_read'];origin,value=last if last is not None else (None,0)
            if ((origin is not None and type(sample['own_source_tick']) is not int)
                    or sample['own_source_tick'] != origin
                    or type(sample['original']) is not int or sample['original'] != value
                    or type(sample['value']) is not int or sample['value'] not in (0,1)):
                raise ValueError('false origin/outcome')
            if row['control_mode'] != 'own_disrupted' and sample['value'] != value:
                raise ValueError('non-own delivered value')
            reads.append((tick,origin,value))
    completion = max(won.values()) if len(won)==32 else None
    cutoff = completion if completion is not None else len(events)+1
    origins={o:v for t,o,v in reads if t < cutoff and o is not None and o >= 64}
    delivered=row['control_mode'] != 'own_disrupted' and bool(origins)
    metric=dict(formation=3*len(program)+16,food=len(won),fresh=sum(p>=16 for p in won),
                own_origins=len(origins) if delivered else 0,terminal_tick=len(events),
                completed=completion is not None,survived64=len(events)>=64 and (death is None or death>64),
                delivered_own=delivered,both_own_outcomes=delivered and set(origins.values())=={0,1},
                completion_tick=completion,paid_work=3*len(program)+16+completion if completion is not None else None)
    validate(metric)
    return dict(metric=metric,diagnostic=dict(native_distinct_origins_before_cutoff=len(origins),
                native_outcomes_before_cutoff=sorted(set(origins.values())),
                ignored_post_completion_reads=sum(t>=cutoff for t,_,_ in reads),
                before_completion_cutoff=completion,death_tick=death,
                scope='measurement only; no historical endpoint rescore'),
                input_sha256=hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':')).encode()).hexdigest())


if __name__ == '__main__':
    import sys
    with open(sys.argv[1],encoding='utf-8') as f: batch=json.load(f)
    print(json.dumps([dict(role=item['role'],**extract(item['row'])) for item in batch['histories']],sort_keys=True))
