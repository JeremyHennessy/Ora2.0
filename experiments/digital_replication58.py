"""Fresh Replication58 assisted assay; immutable Transfer57 census reuse."""
from experiments.digital_transfer57 import source_bank,choice,census,natural,SOURCE_HASH,ROSTER,PROGRAM
from experiments.digital_informative_exposure23_interpret import audit,clone,h
SEEDS=tuple(range(58000,58016))
VERSION='DIGITAL-REPLICATION-58-assisted-v1'
ROUTE='replication58'

def generate(seed,arm,source,summary):
    assert type(seed) is int and seed in SEEDS
    program,origin=choice(arm,source,summary)
    from experiments import digital_informative_exposure23 as substrate
    assert ROUTE not in substrate.PROGRAMS
    before=h(substrate.PROGRAMS)
    matches=[name for name,p in substrate.PROGRAMS.items() if p==program]
    assert len(matches)<=1
    route=matches[0] if matches else ROUTE
    if not matches:substrate.PROGRAMS[ROUTE]=clone(program)
    try:
        row=substrate.history(seed,route,'faithful')
        return dict(version=VERSION,arm=arm,source=origin,source_manifest_hash=SOURCE_HASH,history=row)
    finally:
        if not matches:del substrate.PROGRAMS[ROUTE]
        assert h(substrate.PROGRAMS)==before

def ordinary_gate(s):
    keys=('seed','formation_cost','remote_food','births','paid_copy_words','descendant_food','resource_then_birth','first_birth_tick')
    if any(type(s.get(k)) is not int or s[k]<0 for k in keys):return False
    return s.get('arm')=='withheld' and s.get('mode')=='faithful' and s['seed'] in SEEDS and s['formation_cost']==43 and s['remote_food']>0 and s['births']>=2 and s['paid_copy_words']>=54 and s['descendant_food']>0 and s['resource_then_birth']>0 and s['first_birth_tick']==70


def interpret(envelope,summary):
    assert envelope['version']==VERSION and envelope['source_manifest_hash']==SOURCE_HASH
    origin=envelope['source'];source=None if origin is None else (origin['seed'],origin['child'])
    program,expected=choice(envelope['arm'],source,summary);assert origin==expected
    row=envelope['history'];assert type(row['seed']) is int and row['seed'] in SEEDS and row['mode']=='faithful' and row['genesis_program']==program
    checked=audit(row);lineage=census(program,row['final']['events'])
    assert (lineage['paid_words'],len(lineage['edges']),sum(not p['alive'] for p in lineage['actors'].values()))==(checked['paid_copy_words'],checked['births'],checked['deaths'])
    assert sum(lineage['food_by_site'])==checked['successful_food'] and sum(p['instructions'] for p in lineage['actors'].values())==checked['ticks']
    assert sum(p['endpoint_energy'] for p in lineage['actors'].values() if p['alive'])==checked['live_energy']
    assert checked['mutations']==0
    result=dict(checked,arm=envelope['arm'],source=expected,source_manifest_hash=SOURCE_HASH,site1_food=lineage['food_by_site'][1],
                stable_site1_food=lineage['stable_site1_food'],site1_after_selfwrite_food=lineage['site1_after_selfwrite_food'],
                descendant_food=lineage['descendant_food'],resource_then_birth=lineage['resource_then_birth'],first_birth_tick=lineage['first_birth_tick'],energy_cap_loss=lineage['energy_cap_loss'])
    result['ordinary_admitted']=ordinary_gate(result)
    return dict(summary=result,lineage=lineage,assisted_genesis=True,endogenous_inheritance_demonstrated=False,learning=False,evolution=False,stage_credit=False)


def compare(rows,manifest):
    """Only accepts all144 independent-referee summaries, not raw producer claims."""
    source_bank(manifest)
    assert len(rows)==144;seen={};references={};retained={key:{} for key in ROSTER}
    for row in rows:
        s=row['summary'];assert s['verified'] is True and s['source_manifest_hash']==SOURCE_HASH and s['mode']=='faithful' and s['formation_cost']==43
        seed=s['seed'];assert type(seed) is int and seed in SEEDS
        for field in ('successful_food','site1_food'):natural(s[field])
        assert s['site1_food']<=s['successful_food']
        if s['arm']=='withheld':
            assert s['source'] is None and ordinary_gate(s);key=('withheld',seed);references[seed]=s
        else:
            assert s['arm']=='retained';source=s['source'];identity=(source['seed'],source['child'])
            assert all(type(v) is int for v in identity) and identity in ROSTER
            assert source==choice('retained',identity,manifest)[1]
            key=(identity,seed);retained[identity][seed]=s
        assert key not in seen;seen[key]=s
    assert set(references)==set(SEEDS) and all(set(v)==set(SEEDS) for v in retained.values())
    admit_references([dict(summary=references[s]) for s in SEEDS])
    entries=[]
    for source,results in retained.items():
        pairs=[]
        for seed in SEEDS[::2]:
            food_delta=sum(results[s]['successful_food']-references[s]['successful_food'] for s in (seed,seed+1))
            site1_delta=sum(results[s]['site1_food']-references[s]['site1_food'] for s in (seed,seed+1))
            pairs.append(dict(context=seed//2,seeds=[seed,seed+1],food_delta=food_delta,site1_delta=site1_delta,qualified=food_delta>0 and site1_delta>0))
        entries.append(dict(source=list(source),pairs=pairs,fresh_assisted_resource_benefit=all(p['qualified'] for p in pairs)))
    return dict(entries=entries,unique_histories=144,shared_references=16,retained_histories=128,independent_context_pairs=8,
                eligible_sources=151,enrolled_sources=8,endogenous_inheritance_demonstrated=False,selection=False,evolution=False,learning=False,stage_credit=False)

def admit_references(rows):
    """Complete ordinary-only gate; runner must call before ANY candidate."""
    assert len(rows)==16
    seeds=set()
    for row in rows:
        s=row['summary'];assert s['verified'] is True and s['source_manifest_hash']==SOURCE_HASH and s['source'] is None and ordinary_gate(s)
        assert s['seed'] not in seeds;seeds.add(s['seed'])
    assert seeds==set(SEEDS)
    return dict(ordinary_references=16,admitted=True,retained_histories=0,stage_credit=False)
