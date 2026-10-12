"""Prospective current-law ordinary admission, not a mutation or learning panel."""
import json
from experiments.digital_informative_exposure23_interpret import audit, h

PROGRAM = [[4,1,1],[6,0,0],[5,0,1],[10,0,0],[12,0,0],[7,0,1]]
SEEDS = (51000,51001)
MODES = ('faithful','copy_disabled')

def gate(summary):
    """Reject incomplete descendant viability and boolean/count aliases."""
    fields=('births','descendant_food','resource_then_birth','paid_copy_words','first_birth_tick')
    if any(type(summary.get(k)) is not int or summary[k]<0 for k in fields):return False
    if type(summary.get('seed')) is not int or summary['seed'] not in SEEDS:return False
    if summary.get('mode')=='copy_disabled':
        return summary['births']==summary['paid_copy_words']==summary['first_birth_tick']==0
    if summary.get('mode')!='faithful':return False
    return (summary['births']>=2 and summary['descendant_food']>=1 and
            summary['resource_then_birth']>=1 and summary['paid_copy_words']>=36 and
            summary['first_birth_tick']==(35 if summary['seed']%2==0 else 40))

def interpret(row):
    assert type(row['seed']) is int and row['seed'] in SEEDS and row['mode'] in MODES
    assert row['route']=='ancestor' and h(row['genesis_program'])==h(PROGRAM)
    verified=audit(row)  # Unchanged generic endpoint independently reconstructs every event.
    acquired=set();births=[];foods={};deaths=[];overflow=0;energy={0:12}
    copy_refusals=division_refusals=0
    for ev in row['final']['events']:
        actor=ev['actor'];before=energy[actor]
        success=ev.get('attempt',{}).get('success',0)
        if success:
            foods[actor]=foods.get(actor,0)+1;acquired.add(actor)
            overflow+=max(0,before-1+20-64)
        copy_refusals+=int(ev['outcome']=='copy_refused')
        division_refusals+=int(ev['outcome']=='division_refused')
        if 'birth' in ev:
            child=ev['birth']['child'];energy[child['id']]=12
            births.append(dict(tick=ev['tick'],parent=actor,child=child['id'],generation=child['generation'],
                               parent_acquired_before_birth=actor in acquired,write_ids=ev['birth']['write_ids'],
                               parent_energy=ev['after']['energy'],startup_energy=12))
        if 'after' in ev:energy[actor]=ev['after']['energy']
        if 'death' in ev:deaths.append(dict(tick=ev['tick'],actor=actor));del energy[actor]
    summary=dict(verified,descendant_food=sum(v for k,v in foods.items() if k!=0),
                 resource_then_birth=sum(b['parent']!=0 and b['parent_acquired_before_birth'] for b in births),
                 first_birth_tick=births[0]['tick'] if births else 0,birth_certificates=births,
                 actor_food=foods,death_certificates=deaths,energy_cap_loss=overflow,
                 copy_refusals=copy_refusals,division_refusals=division_refusals)
    summary['admitted']=gate(summary)
    return summary

def panel(rows):
    assert len(rows)==4 and [(r['seed'],r['mode']) for r in rows]==[(s,m) for s in SEEDS for m in MODES]
    summaries=[interpret(r) for r in rows]
    return dict(summaries=summaries,ordinary_admitted=all(s['admitted'] for s in summaries),
                supplied_fixed_ancestor=True,mutation_panel=False,learning=False,evolution=False,
                stage_credit=False,independent_context_pairs=1)

if __name__=='__main__':
    import sys
    print(json.dumps(panel(json.load(open(sys.argv[1],encoding='utf-8'))),sort_keys=True))
