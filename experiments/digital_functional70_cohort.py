"""Complete data projection AFTER authenticated literal replay and paid admission.

Invented proof dictionaries cannot authenticate histories or scientific claims.
The pinned operator owns raw/proof/source custody. No World or winner enrollment.
"""
from experiments.digital_functional70_admission import PRIMARY,UNSEEN,SEEDS
from experiments.digital_functional69_measure import family_comparison
from experiments.digital_functional69_contract import integer
from experiments.digital_functional69_transition import validate_provenance


def first_family(edges):
    assert type(edges) is list
    parent=child=None;last=0;identities=set()
    for edge in edges:
        tick=integer(edge['tick'],1,4096);assert tick>last;last=tick
        identity=integer(edge['child'],1);assert identity not in identities;identities.add(identity)
        integer(edge['parent']);integer(edge['generation'],1)
        if parent is None and edge['generation']==1:parent=edge
        elif parent is not None and child is None and edge['parent']==parent['child']:child=edge
    return dict(parent=parent,child=child)


def cohort(populations,forks,provenance):
    validate_provenance(provenance)
    assert type(populations) is list and type(forks) is list and len(populations)==24 and len(forks)==32
    population={};branches={}
    for proof in populations:
        assert proof['verified'] is True and proof['stage_credit'] is False and proof['provenance']==provenance
        s=proof['summary'];assert s['verified'] is True and s['stage_credit'] is False
        assert type(s['seed']) is int and s['seed'] in SEEDS
        mode,inheritance=s['mode'],s['inheritance_mode']
        assert (mode,inheritance) in (('faithful','parent_copy'),('mutating','parent_copy'),('mutating','ancestor_copy'))
        key=(s['seed'],mode,inheritance);assert key not in population;population[key]=proof
        identity=proof['natural_history_hash'];assert type(identity) is str and len(identity)==64 and set(identity)<=set('0123456789abcdef')
        for field in ('births','deaths','successful_food','paid_copy_words','mutations'):integer(s[field])
    assert set(population)=={(s,m,i) for s in SEEDS for m,i in [('faithful','parent_copy'),('mutating','parent_copy'),('mutating','ancestor_copy')]}
    for proof in forks:
        assert proof['verified'] is True and proof['stage_credit'] is False and proof['provenance']==provenance
        seed=proof['seed'];assert type(seed) is int and seed in SEEDS
        kind=proof['slot_kind'];assert kind in ('parent','child')
        assert proof['role'] in (('sham','ancestor_value_control') if kind=='parent' else ('sham','inherited_source_control'))
        key=(seed,kind,proof['role']);assert key not in branches;branches[key]=proof
        assert proof['natural_history_hash']==population[seed,'mutating','parent_copy']['natural_history_hash']
    assert len(branches)==32
    families=[];slots=[];diagnostics=[]
    for seed in SEEDS:
        natural=population[seed,'mutating','parent_copy']['summary'];chosen=first_family(natural['birth_edges'])
        pairs={}
        for kind,control in [('parent','ancestor_value_control'),('child','inherited_source_control')]:
            sham=branches[seed,kind,'sham'];other=branches[seed,kind,control];expected=chosen[kind]
            for proof in (sham,other):
                assert type(proof['null']) is bool and proof['null']==(expected is None)
                if expected is not None:
                    slot=proof['slot'];assert (slot['target'],slot['parent'],slot['generation'],slot['tick'])==(expected['child'],expected['parent'],expected['generation'],expected['tick'])
            pairs[kind]=(sham,other)
            slots.append(dict(seed=seed,kind=kind,slot=sham['slot'],null=sham['null'],endpoints=[sham['target'],other['target']]))
        result=family_comparison(*pairs['parent'],*pairs['child'],provenance)
        families.append(dict(seed=seed,orientation=seed%2,group='primary' if seed in PRIMARY else 'unseen',result=result))
        faithful=population[seed,'faithful','parent_copy']['summary'];reset=population[seed,'mutating','ancestor_copy']['summary']
        diagnostics.append(dict(seed=seed,parent_vs_ancestor_copy={k:natural[k]-reset[k] for k in ('births','successful_food')},
                                parent_vs_faithful={k:natural[k]-faithful[k] for k in ('births','successful_food')}))
    counts={group:sum(f['result']['conditional_functional_contribution'] for f in families if f['group']==group) for group in ('primary','unseen')}
    return dict(version='DIGITAL-FUNCTIONAL-CONFIRMATION-70-v1',families=families,slots=slots,population_diagnostics=diagnostics,
                qualifying_cases=counts,replicated_bounded_functional_contribution=counts['primary']>=1 and counts['unseen']>=1,
                denominator=dict(populations=24,families=8,slots=16,continuations=32),provenance=provenance,
                requires_authenticated_full_history=True,scientific_acceptance_pending_independent_interpretation=True,
                stage_credit=False,selection=False,sustained_evolution=False,learning=False)
