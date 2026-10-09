"""Independent existing-law reactivation audit; imports no worker."""
import argparse
from copy import deepcopy
import hashlib
import itertools
import json
from pathlib import Path

from experiments import precursor_coupling_audit as law

ROOT=Path(__file__).resolve().parents[1]
FILES=(*law.FILES,'docs/REACTIVATE-01-PROTOCOL.md','experiments/precursor_reactivation.py',
       'experiments/precursor_reactivation_audit.py')


def panel():
    for size in range(2,5):
        for sequence in itertools.product('01',repeat=size):
            bits=''.join(sequence)
            for misses in range(4):
                for source in ('producer','external'):
                    for present in (True,False):
                        for refuel in (False,True):
                            for donor in (False,True):
                                yield dict(bits=bits,candidate=str(1-int(bits[0]))+bits[1:],
                                           budget=size,fuel=2,mode='coupled',phases=1,source=source,
                                           mismatches=misses,founder_present=present,refill=refuel,fresh_donor=donor)


def genesis(c):
    state=law.genesis(c)
    baseline=law.balance(state)
    if not c['founder_present']:
        original=state['objects']['C']
        state['environment']['founder-reserve']=list(original['work'])
        state['heat']+=original['supplied_bonds']
        for aid in original['atoms']:
            state['ready'].append(aid)
        del state['objects']['C']
    law.need(law.balance(state)==baseline,'Ablation changed material/energy ledger')
    return state


def schedule(c):
    out=[['activate','C','M0.0','A0.0']]
    out += [['recognize','C','M0.0',None] for _ in range(c['mismatches'])]
    if c['refill']:
        out += [['harvest','C','F0.0',None],['harvest','C','F0.1',None]]
    out += [['activate','C','M0.0','A0.1' if c['fresh_donor'] else 'A0.0']]
    return out


def inspect_record(record,c):
    law.need(record['config']==c,'Frozen case/order differs')
    state=genesis(c)
    ledger=law.balance(state)
    law.need(record['initial']==state,'Initial state/ablation differs')
    chain=law.sha(state)
    requests=schedule(c)
    law.need(len(record['events'])==len(requests),'Finite requests differ')
    second_before=None
    for tick,(event,request) in enumerate(zip(record['events'],requests)):
        if tick>0 and request[0]=='activate':
            second_before=dict(ready='M0.0' in state['ready'],local_potential=len(state['activation']['M0.0']),
                               producer_work=len(state['objects']['C']['work']) if 'C' in state['objects'] else 0)
        before=law.sha(state)
        state,result=law.advance(state,c,tick,request)
        law.need(law.balance(state)==ledger,'Material/work provenance conservation')
        expected=dict(tick=tick,request=request,before=before,after=law.sha(state),previous=chain,result=result)
        expected['sha256']=law.sha(expected)
        law.need(event==expected,'Semantic state/result/event forgery')
        chain=expected['sha256']
    law.need(record['terminal']==state and record['before_second']==second_before,'Terminal/boundary differs')
    last=record['events'][-1]['result']
    renewed=last['outcome']=='activated'
    funded=renewed and c['source']=='producer' and len(last['spent'])==2
    if funded:
        for uid in last['spent']:
            meta=state['units'][uid]
            funded = funded and meta['origin']=='harvest' and meta['actor']=='C'
    law.need(type(record['second_producer_funded']) is bool and record['second_producer_funded']==funded,
             'Producer funding/subsidy forgery')
    # No reproduction action was requested: classify only activation chemistry.
    law.need(set(state['history'])=={'C'},'Unexpected child history')
    return dict(cases=1,first_activated=int(record['events'][0]['result']['outcome']=='activated'),
                second_activated=int(renewed),second_producer_funded=int(funded),
                second_external=int(renewed and c['source']=='external'),
                partial_rejected=int(second_before['local_potential']>0 and not renewed))


def audit(output,revision):
    output=Path(output)
    raw=(output/'records.jsonl').read_bytes()
    law.need(len(raw)<=128*1024**2 and raw.endswith(b'\n'),'Bounded complete records')
    records=[json.loads(line,object_pairs_hook=law.unique) for line in raw.splitlines()]
    configs=list(panel())
    law.need(len(records)==len(configs)==1792,'Complete precommitted factor cross')
    summary=json.loads((output/'summary.json').read_bytes(),object_pairs_hook=law.unique)
    law.need(summary['schema']=='reactivate01-summary-v1' and summary['revision']==revision and
             len(revision)==40 and all(x in '0123456789abcdef' for x in revision),'Exact source identity')
    law.need(summary['source_sha256']=={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in FILES},
             'Source checksum inventory')
    law.need(summary['records_sha256']==hashlib.sha256(raw).hexdigest(),'Raw records digest')
    total,groups={},{}
    for record,c in zip(records,configs):
        metrics=inspect_record(record,c)
        key=f"n{len(c['bits'])}/{c['source']}/founder-{c['founder_present']}"
        for target in (total,groups.setdefault(key,{})):
            for name,value in metrics.items():
                target[name]=target.get(name,0)+value
    law.need(summary['total']==total and summary['groups']==groups,'Independently derived counts differ')
    law.need(summary['natural_worlds']==0 and summary['new_physics'] is False and
             summary['reproduction_demonstrated'] is False,'Unsupported science claim')
    return dict(schema='reactivate01-audit-v1',revision=revision,passed=True,cases=1792,
                events=sum(len(r['events']) for r in records),total=total,groups=groups,
                material_energy_provenance=True,records_sha256=hashlib.sha256(raw).hexdigest(),
                new_physics=False,natural_worlds=0,reproduction_demonstrated=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-dir',required=True)
    p.add_argument('--source-revision',required=True)
    a=p.parse_args()
    print(json.dumps(audit(a.input_dir,a.source_revision),sort_keys=True,indent=2))
