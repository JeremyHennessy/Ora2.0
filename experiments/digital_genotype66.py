"""Source-bound, full-audit-first matched genotype measurement; no World import.
Controlled paid initialization is researcher assistance, not natural selection.
"""
import json
from pathlib import Path
from experiments import digital_renewable64_interpret as full
from experiments import digital_renewable65 as projection
from experiments import digital_genotype66_projection as genotype_projection

PRIMARY=tuple(range(67000,67004));UNSEEN=tuple(range(67200,67204));SEEDS=PRIMARY+UNSEEN
SOURCE_SEEDS=tuple(range(66000,66008))+tuple(range(66200,66208))
CATALOG_HASH='78eed0bf8e94d2def49de35f476da3d2041a51d061c87d69df8f59747c799446'
ANCESTOR=full.ANCESTOR_WORDS


def catalog(registration):
    assert registration['contract']=='DIGITAL-MATCHED-GENOTYPE-66-v1'
    assert registration['law']=='DIGITAL-RENEWABLE-ECOLOGY-64-v1' and not registration['law_changed']
    records=registration['neutral_source_records']
    assert full.h(records)==CATALOG_HASH and type(records) is list and len(records)==16
    assert [r['seed'] for r in records]==list(SOURCE_SEEDS)
    result={}
    for r in records:
        s=r['slot'];assert s is not None and s['parent']==0 and s['child']==1
        assert s['parent_program_at_division']==ANCESTOR
        words=s['newborn_program']
        assert type(words) is list and len(words)==27 and all(type(v) is int and 0<=v<32 for v in words)
        assert full.h(words)==s['newborn_program_hash']
        assert s['paid_copy_words']==27 and s['state_formation_words']==16 and s['startup_energy']==12 and s['release_energy']==2
        assert r['seed'] not in result;result[r['seed']]=full.clone(r)
    return result


def registered_catalog():
    p=Path(__file__).resolve().parents[1]/'docs/DIGITAL-MATCHED-GENOTYPE-66-REGISTRATION.json'
    assert p.stat().st_size<256*1024
    return catalog(json.loads(p.read_bytes()))


def bound_role(seed,source_seed,sources):
    assert type(seed) is int and seed in SEEDS
    assert set(sources)==set(SOURCE_SEEDS)
    assert full.h([sources[k] for k in SOURCE_SEEDS])==CATALOG_HASH
    if source_seed is None:return 'genotype66:parent',ANCESTOR[:]
    assert type(source_seed) is int and source_seed in SOURCE_SEEDS
    r=sources[source_seed];s=r['slot']
    assert r['seed']==source_seed and s['parent_program_at_division']==ANCESTOR
    assert full.h(s['newborn_program'])==s['newborn_program_hash']
    route='genotype66:%s:%s:%s:%s'%(source_seed,s['child'],r['history_hash'],s['newborn_program_hash'])
    return route,s['newborn_program'][:]


def generate(seed,source_seed=None):
    route,words=bound_role(seed,source_seed,registered_catalog())
    from experiments.digital_genotype66_world import history
    return history(seed,words,route)


def project_audited(row,summary):
    """Generic software fixture support; caller must provide successful full audit."""
    assert summary['verified'] is True and summary['formation_cost']==43
    p=genotype_projection._project_audited(row,summary)
    founder=projection._actor_record(p['actors'],0)
    assert founder['turns']<=256
    return dict(founder=founder,primary_endpoint=founder['births'],secondary_endpoint=founder['food'],
                projection=p,selection=False,causal_inheritance=False,learning=False,stage_credit=False)


def audit_row(row,source_seed=None):
    route,words=bound_role(row['seed'],source_seed,registered_catalog())
    assert row['route']==route and row['mode']=='faithful' and row['fuel_mode']=='renewed'
    assert row['genesis_program']==[words[i:i+3] for i in range(0,27,3)]
    summary=full.audit(row)
    assert summary['genesis_program_hash']==full.h(words)
    measured=project_audited(row,summary)
    return dict(seed=row['seed'],source_seed=source_seed,history_hash=row['hash'],summary=summary,
                measured=measured,stage_credit=False)


def ordinary_predicates(s):
    """Same whole paid turnover predicates; exact membership in ordinary_gate."""
    assert s['verified'] is True and s['mode']=='faithful' and s['fuel_mode']=='renewed'
    assert s['formation_cost']==43 and s['genesis_program_hash']==full.h(ANCESTOR)
    t=s['turnover']
    return (t['founder_expiry_tick'] is not None and t['post_founder_instructions']>=128
            and s['births']>=12 and t['maximum_generation']>=3
            and t['post_founder_paid_personal_births']>0 and t['post_founder_renewed_food']>0
            and bool(t['paid_personal_chains']) and t['living_descendants']>=1)


def ordinary_gate(proof):
    assert proof['source_seed'] is None and type(proof['seed']) is int and proof['seed'] in SEEDS
    s=proof['summary'];assert s['seed']==proof['seed'] and s['route']=='genotype66:parent'
    return ordinary_predicates(s)


def ordinary_admission(proofs):
    assert type(proofs) is list and len(proofs)==8
    assert sorted(p['seed'] for p in proofs)==sorted(SEEDS)
    gates=[ordinary_gate(p) for p in proofs]
    return all(gates)


def cohort(proofs):
    assert type(proofs) is list and len(proofs)==136
    by={}
    for p in proofs:
        seed,source=p['seed'],p['source_seed']
        assert type(seed) is int and seed in SEEDS
        assert source is None or type(source) is int and source in SOURCE_SEEDS
        key=(seed,source);assert key not in by;by[key]=p
        assert p['summary']['verified'] is True and p['summary']['seed']==seed
        assert p['measured']['primary_endpoint']==p['measured']['founder']['births']
        assert p['measured']['secondary_endpoint']==p['measured']['founder']['food']
    expected={(seed,source) for seed in SEEDS for source in (None,)+SOURCE_SEEDS}
    assert set(by)==expected
    sources=registered_catalog()
    for (seed,source),p in by.items():
        route,words=bound_role(seed,source,sources)
        s=p['summary']
        assert s['route']==route and s['genesis_program_hash']==full.h(words)
        assert s['mode']=='faithful' and s['fuel_mode']=='renewed' and s['formation_cost']==43
        assert p['measured']['founder']['turns']==s['turns'].get('0',s['turns'].get(0))
    assert ordinary_admission([by[(seed,None)] for seed in SEEDS])
    slots=[]
    for source in SOURCE_SEEDS:
        rows=[]
        unchanged=sources[source]['slot']['newborn_program']==ANCESTOR
        for seeds in (PRIMARY,UNSEEN):
            for offset in range(0,4,2):
                pair=seeds[offset:offset+2];birth=food=0
                for seed in pair:
                    a,b=by[(seed,source)],by[(seed,None)]
                    birth+=a['measured']['primary_endpoint']-b['measured']['primary_endpoint']
                    food+=a['measured']['secondary_endpoint']-b['measured']['secondary_endpoint']
                    if unchanged:
                        assert a['history_hash']==b['history_hash']
                        assert a['measured']==b['measured']
                rows.append(dict(bank='primary' if seeds==PRIMARY else 'unseen',context=pair[0]//2,
                                 birth_difference=birth,food_difference=food,benefit=birth>0 and food>=0))
        slots.append(dict(source_seed=source,source=sources[source],unchanged=unchanged,contexts=rows,
                          benefit=all(r['benefit'] for r in rows)))
    return dict(slots=slots,parent_worlds=8,candidate_worlds=128,original_roles=136,
                candidate_promotion=False,selection=False,causal_inheritance=False,learning=False,stage_credit=False)
