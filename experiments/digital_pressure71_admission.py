"""Pure registered71 paid-route predicates; flags/fixtures are not admission evidence.

The parent owes fresh independent complete raw/proof replay and sealed native
custody before using these projections. No VM, seed draw, policy or repair.
"""
import hashlib
import json
from experiments.digital_functional69_contract import ANCESTOR,integer

VERSION='DIGITAL-PRESSURE-SELECTION-71-ADMISSION-v2'
PRIMARY=tuple(range(74000,74004));UNSEEN=tuple(range(74200,74204));SEEDS=PRIMARY+UNSEEN
REFERENCE_DOSE=8  # Disclosed metadata for the ONE faithful reference; changes ignored.

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def hash_string(value):
    assert type(value) is str and len(value)==64 and set(value)<=set('0123456789abcdef')
    return value

def ordinary_gate(summary):
    assert type(summary) is dict and summary['verified'] is True
    assert integer(summary['seed']) in SEEDS
    assert summary['mode']=='faithful' and summary['inheritance_mode']=='parent_copy'
    assert summary['route']=='ancestor' and summary['fuel_mode']=='renewed'
    assert integer(summary['formation_cost'])==43
    assert summary['genesis_program_hash']==digest(ANCESTOR)
    assert integer(summary['dose'])==REFERENCE_DOSE
    assert integer(summary['horizon'])==4096 and summary['software_only'] is False
    ticks=integer(summary['ticks'],0,4096);births=integer(summary['births'],0,4096)
    t=summary['turnover'];assert type(t) is dict
    for key in ('post_founder_instructions','maximum_generation','post_founder_paid_personal_births',
                'post_founder_renewed_food','living_descendants'):
        integer(t[key],0,4096)
    assert t['founder_expiry_tick'] is None or integer(t['founder_expiry_tick'],1,4096)
    edges=summary['birth_edges'];assert type(edges) is list and len(edges)==births
    parents={0:None};generations={0:0};by_id={};used=set();last=0
    root=child=None;generation_counts={3:0,4:0}
    for edge in edges:
        actor=integer(edge['parent']);target=integer(edge['child'],1,4096)
        generation=integer(edge['generation'],1,4096);tick=integer(edge['tick'],1,ticks)
        assert actor in parents and target not in parents and tick>last;last=tick
        assert generation==generations[actor]+1
        integer(edge['parent_personal_food'],0,4096)
        writes=edge['write_ids'];assert type(writes) is list and len(writes)==27
        assert all(type(i) is int and i>=0 for i in writes) and len(set(writes))==27
        assert used.isdisjoint(writes);used.update(writes)
        parents[target]=actor;generations[target]=generation;by_id[target]=edge
        if generation in generation_counts:generation_counts[generation]+=1
        if root is None and generation==2:root=target
        elif root is not None and child is None and actor==root:child=target
    # The unchanged70 personal-food chain is still owed, with bound edges.
    chains=t['paid_personal_chains'];assert type(chains) is list
    for chain in chains:
        assert type(chain) is list and len(chain)==3 and all(type(i) is int for i in chain)
        first,middle,end=(by_id[i] for i in chain)
        assert (first['generation'],middle['generation'],end['generation'])==(1,2,3)
        assert middle['parent']==first['child'] and end['parent']==middle['child']
        assert middle['parent_personal_food']>0 and end['parent_personal_food']>0
    base=(t['founder_expiry_tick'] is not None and t['post_founder_instructions']>=128
        and births>=12 and t['maximum_generation']>=3 and t['post_founder_paid_personal_births']>0
        and t['post_founder_renewed_food']>0 and bool(chains) and t['living_descendants']>=1)
    # Paid division/COPY truth belongs to literal replay, not to extra hidden prices.
    grandchild=next((e['child'] for e in edges if child is not None and e['parent']==child and e['generation']==4),None)
    extra=(generation_counts[3]>=2 and generation_counts[4]>=2 and grandchild is not None)
    return bool(base and extra)

def ordinary_admission(original,restored):
    assert type(original) is list and type(restored) is list and len(original)==len(restored)==8
    gates=[];copies=[]
    for export in (original,restored):
        seen={}
        for summary in export:
            assert summary['seed'] not in seen;seen[summary['seed']]=summary
            gates.append(ordinary_gate(summary))
        assert set(seen)==set(SEEDS);copies.append(seen)
    assert copies[0]==copies[1]
    return all(gates)  # ALL16 evaluated before aggregation; no early success shortcut.

def require_durable_admission(receipt,expected_source,expected_configuration):
    hash_string(expected_source);hash_string(expected_configuration)
    assert type(receipt) is dict and set(receipt)=={
        'version','source_sha256','configuration_sha256','references','treatment_worlds',
        'original_restored_equal','all_paid_gates','native_children','raw_proof_pairs',
        'reference_receipts','reference_bundle_sha256'}
    assert receipt['version']==VERSION
    assert receipt['source_sha256']==expected_source and receipt['configuration_sha256']==expected_configuration
    assert integer(receipt['references'])==16 and integer(receipt['treatment_worlds'])==0
    assert integer(receipt['native_children'])==34 and integer(receipt['raw_proof_pairs'])==16
    assert receipt['original_restored_equal'] is True and receipt['all_paid_gates'] is True
    rows=receipt['reference_receipts'];assert type(rows) is list and len(rows)==16
    seen=set()
    for row in rows:
        assert type(row) is dict and set(row)=={'export','seed','dose','raw_sha256','proof_sha256'}
        assert row['export'] in ('original','restored') and integer(row['seed']) in SEEDS
        assert integer(row['dose'])==REFERENCE_DOSE
        hash_string(row['raw_sha256']);hash_string(row['proof_sha256'])
        key=(row['export'],row['seed']);assert key not in seen;seen.add(key)
    assert seen=={(export,seed) for export in ('original','restored') for seed in SEEDS}
    assert hash_string(receipt['reference_bundle_sha256'])==digest(rows)
    # Hash/schema consistency alone is NEVER fresh paid replay or durable file custody.
    return True

def admit(request,provenance,receipt=None):
    """Pure child guard BEFORE any producer import. Custody truth stays with parent."""
    assert type(provenance) is dict and set(provenance)=={'source_sha256','configuration_sha256'}
    for value in provenance.values():hash_string(value)
    assert type(request) is dict and integer(request['seed']) in SEEDS
    dose=integer(request['dose']);assert dose in (1,8)
    kind=request['kind'];assert kind in ('population','population_ref','fork','fork_ref')
    if kind.startswith('population'):
        assert (request['mode'],request['inheritance_mode']) in (
            ('faithful','parent_copy'),('mutating','parent_copy'),('mutating','ancestor_copy'))
        treatment=request['mode']=='mutating'
        assert treatment or dose==REFERENCE_DOSE
    else:
        assert request['slot_kind'] in ('parent','child')
        assert request['fork_role'] in (('sham','ancestor_value_control') if request['slot_kind']=='parent'
                                       else ('sham','inherited_source_control'))
        treatment=True
    if treatment:
        assert receipt is not None
        require_durable_admission(receipt,provenance['source_sha256'],provenance['configuration_sha256'])
    return treatment
