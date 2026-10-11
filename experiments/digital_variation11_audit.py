"""Independent full transition interpretation and unconditional role inheritance."""
import json
from .digital_singlecopy09_audit import audit as matched_audit
from .digital_release07_audit import audit as ordinary_audit
DOUBLE=[[4,1,1],[6,0,0],[5,0,1],[6,0,0],[5,0,1],[10,0,0],[12,0,0],[7,0,1]]
ANCESTOR=[[4,1,1],[6,0,0],[5,0,1],[10,0,0],[12,0,0],[7,0,1]]

def transmission_endpoint(parent_remote,child_remote,child_births,inherited_executed_role,novel_born_parent):
    return parent_remote>=1 and child_remote>=1 and child_births>=1 and inherited_executed_role and novel_born_parent

def lineage_inventory(row):
    genome=sum(row['genesis_program'],[]);states={0:dict(code=[[v,i] for i,v in enumerate(genome)],pc=0)}
    stats={0:dict(parent=None,birth_tick=0,born_genome=genome,remote=[],births=0,moves={},inherited=[])};writes={};pairs=[]
    for event in row['final']['events']:
        actor=event['actor'];s=stats[actor];before=states[actor]
        if event['decoded'][0]==13:
            unit=before['code'][3*before['pc']][1];s['moves'].setdefault(unit,event['tick'])
        if event.get('attempt',{}).get('success') and event['attempt']['position']!=0:s['remote'].append(event['tick'])
        for w in event.get('writes',[]):writes[w['write_id']]=w
        if 'birth' in event:
            child=event['birth']['child'];identity=child['id'];s['births']+=1;inherited=[]
            for index,wid in enumerate(event['birth']['write_ids']):
                w=writes[wid]
                if index%3==0 and w['source_value']==w['value']==13 and not w['mutated']:
                    inherited.append(dict(parent_unit=w['source_unit'],child_unit=w['unit'],write_id=wid))
            stats[identity]=dict(parent=actor,birth_tick=event['tick'],born_genome=[v[0] for v in child['code']],remote=[],births=0,moves={},inherited=inherited)
            states[identity]=child
        if 'after' in event:states[actor]=event['after']
        elif 'death' in event:del states[actor]
    for identity,s in stats.items():
        parent=s['parent']
        if parent is None:continue
        p=stats[parent];role=any(r['parent_unit'] in p['moves'] and p['moves'][r['parent_unit']]<s['birth_tick'] and r['child_unit'] in s['moves'] for r in s['inherited'])
        if transmission_endpoint(sum(t<s['birth_tick'] for t in p['remote']),len(s['remote']),s['births'],role,parent!=0 and p['born_genome']!=genome):pairs.append(dict(parent=parent,child=identity,inherited_roles=s['inherited']))
    return dict(born_entities=len(stats)-1,novel_born_entities=sum(i!=0 and s['born_genome']!=genome for i,s in stats.items()),qualified_pairs=pairs,all_entities=stats)

def audit(record):
    assert set(record)=={'contract','configuration','history'} and record['contract']=='DIGITAL-VARIATION-11-v1'
    name=record['configuration'];row=record['history'];assert type(row['seed']) is int and 25900<=row['seed']<25908
    if name=='actual_ordinary':
        assert row['route']=='ancestor' and row['mode']=='faithful' and row['genesis_program']==ANCESTOR;m=ordinary_audit(row)
    else:
        assert name in ('single','per_word','faithful') and row['route']=='variation11_double' and row['mode']==name and row['genesis_program']==DOUBLE;m=matched_audit(row)
    events=row['final']['events']
    m['fresh_packets']=sum(bool(e.get('attempt',{}).get('success')) and 16<=e['attempt']['packet']<32 for e in events if 'attempt' in e)
    m['descendant_fresh']=sum(bool(e.get('attempt',{}).get('success')) and e['actor']!=0 and 16<=e['attempt']['packet']<32 for e in events if 'attempt' in e)
    m['ordinary_endpoint']=m['births']>=1 and m['descendant_births']>=1 and m['fresh_packets']>=1 and m['descendant_fresh']>=1
    m['configuration']=name;m['lineages']=lineage_inventory(row)
    return m

if __name__=='__main__':
    import sys
    with open(sys.argv[1],encoding='utf-8') as f:print(json.dumps(audit(json.load(f)),sort_keys=True))
