"""REACTIVATE-01 uses existing ENERGY-02 reactions; no new physics or worlds."""
import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path

from experiments import precursor_coupling as law

ROOT = Path(__file__).resolve().parents[1]
FILES = (*law.FILES, 'docs/REACTIVATE-01-PROTOCOL.md',
         'experiments/precursor_reactivation.py', 'experiments/precursor_reactivation_audit.py')


def configs():
    for n in (2, 3, 4):
        for word in itertools.product('01', repeat=n):
            bits = ''.join(word)
            for mismatches, source, founder, refill, fresh in itertools.product(
                    range(4), ('producer','external'), (True,False), (False,True), (False,True)):
                yield dict(bits=bits, candidate=str(1-int(bits[0]))+bits[1:], budget=n,
                           fuel=2, mode='coupled', phases=1, source=source,
                           mismatches=mismatches, founder_present=founder,
                           refill=refill, fresh_donor=fresh)


def initial(c):
    state = law.initial(c)
    if not c['founder_present']:
        founder = state['objects'].pop('C')
        state['ready'].extend(founder['atoms'])
        state['environment']['founder-reserve'] = founder['work']
        state['heat'] += founder['supplied_bonds']
    return state


def requests(c):
    yield ['activate','C','M0.0','A0.0']
    for _ in range(c['mismatches']):
        yield ['recognize','C','M0.0',None]
    if c['refill']:
        yield ['harvest','C','F0.0',None]
        yield ['harvest','C','F0.1',None]
    yield ['activate','C','M0.0','A0.1' if c['fresh_donor'] else 'A0.0']


def simulate(c):
    state = initial(c)
    start, events, chain = copy.deepcopy(state), [], law.digest(state)
    before_second = None
    for tick, request in enumerate(requests(c)):
        before = law.digest(state)
        if tick > 0 and request[0] == 'activate':
            before_second = dict(ready='M0.0' in state['ready'],
                                 local_potential=len(state['activation']['M0.0']),
                                 producer_work=len(state['objects'].get('C',{}).get('work',[])))
        state, result = law.step(state,c,tick,request)
        event = dict(tick=tick, request=request, before=before, after=law.digest(state),
                     previous=chain,result=result)
        event['sha256'] = law.digest(event)
        events.append(event)
        chain = event['sha256']
    second = events[-1]['result']
    funded = second['outcome'] == 'activated' and c['source'] == 'producer' and all(
        state['units'][u]['origin'] == 'harvest' and state['units'][u]['actor'] == 'C' for u in second['spent'])
    return dict(config=c,initial=start,events=events,terminal=state,
                before_second=before_second,second_producer_funded=funded)


def counts(record):
    second = record['events'][-1]['result']['outcome']
    return dict(cases=1, first_activated=int(record['events'][0]['result']['outcome']=='activated'),
                second_activated=int(second=='activated'),
                second_producer_funded=int(record['second_producer_funded']),
                second_external=int(second=='activated' and record['config']['source']=='external'),
                partial_rejected=int(record['before_second']['local_potential']>0 and second!='activated'))


def run(output, revision):
    if len(revision)!=40 or any(c not in '0123456789abcdef' for c in revision):
        raise ValueError('Exact revision required')
    output = Path(output)
    output.mkdir(parents=True,exist_ok=False)
    total, groups = {}, {}
    with (output/'records.jsonl').open('wb') as stream:
        for c in configs():
            record = simulate(c)
            stream.write((law.encode(record)+'\n').encode())
            key = f"n{len(c['bits'])}/{c['source']}/founder-{c['founder_present']}"
            for target in (total,groups.setdefault(key,{})):
                for name,value in counts(record).items():
                    target[name]=target.get(name,0)+value
    summary = dict(schema='reactivate01-summary-v1',revision=revision,total=total,groups=groups,
                   records_sha256=hashlib.sha256((output/'records.jsonl').read_bytes()).hexdigest(),
                   source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in FILES},
                   natural_worlds=0,new_physics=False,reproduction_demonstrated=False)
    (output/'summary.json').write_bytes((law.encode(summary)+'\n').encode())
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',required=True)
    p.add_argument('--source-revision',required=True)
    a=p.parse_args()
    run(a.output_dir,a.source_revision)
