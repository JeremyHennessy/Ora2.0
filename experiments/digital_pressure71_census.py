"""All-population paid birth census; projections alone do not authenticate history."""
import hashlib
import json
from fractions import Fraction

VERSION='DIGITAL-PRESSURE-SELECTION-71-CENSUS-v2'

def integer(value,minimum=0,maximum=4096):
    assert type(value) is int and minimum<=value<=maximum
    return value

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def census_from_replayed(history,summary,root):
    """Only a binding projection. A supplied verified flag is not paid ancestry proof."""
    assert type(history) is dict and type(summary) is dict and summary['verified'] is True
    assert digest(history['final'])==history['hash']
    assert history['seed']==summary['seed'] and history['dose']==summary['dose']
    events=history['final']['events'];assert len(events)==integer(summary['ticks'])
    parents={0:None};generations={0:0};lineage=set();edges=[];deaths=[];first_root=None
    for tick,event in enumerate(events,1):
        assert integer(event['tick'],1)==tick
        actor=integer(event['actor']);assert actor in parents
        if 'birth' in event:
            birth=event['birth'];child=birth['child'];target=integer(child['id'],1)
            assert target not in parents and integer(child['parent'])==actor
            generation=integer(child['generation'],1);assert generation==generations[actor]+1
            parents[target]=actor;generations[target]=generation
            if first_root is None and generation==2:first_root=target
            if target==root or actor in lineage:lineage.add(target)
            edges.append(dict(parent=actor,child=target,generation=generation,tick=tick))
        if 'death' in event or 'expiry' in event:
            assert actor not in {record['actor'] for record in deaths}
            deaths.append(dict(actor=actor,tick=tick,cause='execution_budget' if 'expiry' in event else 'execution_death'))
    if root is not None:integer(root,1)
    assert root==first_root
    assert len(edges)==summary['births']==history['final']['births']
    assert len(deaths)==summary['deaths']==history['final']['deaths']
    assert len(edges)==len(summary['birth_edges'])
    for edge,audited in zip(edges,summary['birth_edges']):
        assert all(audited[key]==value for key,value in edge.items())
    cohorts={generation:[edge for edge in edges if edge['generation']==generation] for generation in (3,4)}
    total3,total4=(len(cohorts[g]) for g in (3,4))
    count3,count4=(sum(edge['child'] in lineage for edge in cohorts[g]) for g in (3,4))
    eligible=root is not None and total3>=2 and total4>=2
    growth=Fraction(count4,total4)-Fraction(count3,total3) if eligible else None
    frame=None if root is None else dict(root=root,early_total=total3,early_lineage=count3,late_total=total4,late_lineage=count4)
    return dict(version=VERSION,history_hash=history['hash'],root=root,frame=frame,
        birth_edges=edges,death_records=deaths,lineage_birth_ids=sorted(lineage-{root}),
        cohort_opportunity=eligible,growth=None if growth is None else [growth.numerator,growth.denominator],
        requires_authenticated_full_history=True,scientific_admission=False,stage_credit=False)

def audit_census(continuation,expected_provenance):
    """Authenticate full natural and declared branch replay before this projection."""
    from experiments.digital_pressure71_referee import audit
    assert continuation['slot_kind']=='parent' and continuation['role'] in ('sham','ancestor_value_control')
    proof=audit(continuation,expected_provenance)
    if proof['null']:
        return dict(version=VERSION,root=None,frame=None,cohort_opportunity=False,growth=None,
                    requires_authenticated_full_history=True,scientific_admission=False,stage_credit=False)
    return census_from_replayed(continuation['branch'],proof['summary'],proof['slot']['target'])
