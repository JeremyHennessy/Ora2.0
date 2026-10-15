"""Pure frozen v2 arithmetic. External literal/custody proof is mandatory."""
from fractions import Fraction
from math import comb

PRIMARY=tuple(range(1009700,1009708));UNSEEN=tuple(range(1009900,1009908))
DESCRIPTORS=tuple((q,r) for q in (2,4,8) for r in ('fallback0','model','fallback1'))
FIELDS={'seed','descriptor','completed','N','E','fixed_oracle_N','fixed_oracle_E',
        'common','correct_intact','correct_joint','correct_model','correct_route',
        'correct_misbound','older_uses','observed_mixed'}

def tail(wins,losses):
    assert type(wins) is int and type(losses) is int and wins>=0 and losses>=0
    n=wins+losses
    return Fraction(sum(comb(n,k) for k in range(wins,n+1)),2**n) if n else Fraction(1)

def interpret(rows):
    assert type(rows) is list and len(rows)==144
    cells={}
    for row in rows:
        assert type(row) is dict and set(row)==FIELDS
        seed=row['seed'];descriptor=row['descriptor']
        assert type(seed) is int and seed in PRIMARY+UNSEEN
        assert type(descriptor) is list and len(descriptor)==2
        assert type(descriptor[0]) is int and type(descriptor[1]) is str and tuple(descriptor) in DESCRIPTORS
        for key in FIELDS-{'descriptor'}:assert type(row[key]) is int
        assert 0<=row['completed']<=60 and 0<=row['common']<=12
        assert 0<=row['older_uses']<=12 and row['observed_mixed'] in (0,1)
        for key in ('correct_intact','correct_joint','correct_model','correct_route','correct_misbound'):
            assert 0<=row[key]<=row['common']
        cell=(seed,tuple(descriptor));assert cell not in cells
        cells[cell]=row
    assert set(cells)=={(seed,d) for seed in PRIMARY+UNSEEN for d in DESCRIPTORS}
    results=[]
    for d in DESCRIPTORS:
        banks={}
        for name,seeds in (('primary',PRIMARY),('unseen',UNSEEN)):
            current=[cells[seed,d] for seed in seeds]
            n=sum(x['N']-x['fixed_oracle_N'] for x in current)
            e=sum(x['E']-x['fixed_oracle_E'] for x in current)
            common=sum(x['common'] for x in current)
            delta={label:sum(x['correct_intact']-x[key] for x in current) for label,key in (
                ('joint','correct_joint'),('model','correct_model'),('route','correct_route'),('misbound','correct_misbound'))}
            older=sum(x['older_uses'] for x in current if x['observed_mixed']==1)
            origins=sum(x['observed_mixed']==1 and x['older_uses']>0 for x in current)
            banks[name]=dict(N_oracle_gain=n,E_oracle_gain=e,common=common,
                deltas=delta,older_uses=older,origin_contexts=origins,
                all_intact_complete=all(x['completed']==60 for x in current),
                mechanism_gates=all(x['completed']==60 for x in current) and common>=80
                    and delta['joint']>=8 and older>=4 and origins>=3 and n>=16,
                generation_strata={label:dict(contexts=len(indices),
                    N_oracle_gain=sum(current[i]['N']-current[i]['fixed_oracle_N'] for i in indices),
                    E_oracle_gain=sum(current[i]['E']-current[i]['fixed_oracle_E'] for i in indices))
                    for label,indices in (('constant',(0,1)),('independent_labels',tuple(range(2,8))))})
        contrasts=[cells[seed,d]['correct_intact']-cells[seed,d]['correct_joint'] for seed in PRIMARY+UNSEEN]
        wins=sum(x>0 for x in contrasts);losses=sum(x<0 for x in contrasts);p=tail(wins,losses)
        mechanic=all(v['mechanism_gates'] for v in banks.values()) and p<=Fraction(1,180)
        results.append(dict(descriptor=list(d),banks=banks,
            joint_sign=dict(wins=wins,losses=losses,ties=16-wins-losses,p=str(p),passes=p<=Fraction(1,180)),
            arithmetic_mechanistic_paid_choice=mechanic,
            arithmetic_finite_cohort_net_energy=mechanic and all(v['E_oracle_gain']>0 for v in banks.values())))
    return dict(descriptors=results,confirmatory_family_size=9,threshold='1/180',
        logical_original_histories=816,context_count=16,
        numeric_interface_only=True,execution_admission=False,
        requires_external_literal_parity_native_source_grant_binding=True,
        statistical_energy_population_claim=False,stage_credit=False)
