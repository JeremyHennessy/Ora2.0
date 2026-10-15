"""Frozen complete-denominator arithmetic; no metric/target/World/referee imports."""
from fractions import Fraction
from math import comb

FIXED=('fixed0','fixed1','cue_identity','cue_inverse','fixed_alternation','latest_reactive')
CONTROLS=('intact','model_erased','history_misbound','update_frozen')
ROSTER=tuple((r,'intact') for r in FIXED)+tuple((f'learner{q}',c) for q in (2,4,8) for c in CONTROLS)

def fraction(value):return dict(numerator=value.numerator,denominator=value.denominator)

def signs(values):
    wins=sum(v>0 for v in values);losses=sum(v<0 for v in values);ties=len(values)-wins-losses
    n=wins+losses
    p=Fraction(sum(comb(n,k) for k in range(wins,n+1)),2**n)
    return dict(wins=wins,losses=losses,ties=ties,p=fraction(p),passed=p<=Fraction(1,180))

def window(row):
    return {(v['attempt']['packet'],v['attempt']['cue']):v['attempt']['success']
        for v in row['causal_window'] if v['attempt'] is not None}

def interpret(batches,software=False):
    assert type(software) is bool
    banks=(tuple(range(2100280,2100282)),tuple(range(2100282,2100284))) if software else (
        tuple(range(1009300,1009308)),tuple(range(1009500,1009508)))
    expected=set(banks[0]+banks[1])
    assert len(batches)==len(expected) and {b['seed'] for b in batches}==expected
    rows={}
    for b in batches:
        assert b['verified'] is True and [(r['role'],r['control']) for r in b['records']]==list(ROSTER)
        for r in b['records']:
            assert r['seed']==b['seed']
            rows[r['seed'],r['role'],r['control']]=r
    assert len(rows)==18*len(expected)
    capacities=[]
    for q in (2,4,8):
        role=f'learner{q}';all_deltas={c:[] for c in CONTROLS[1:]};decisions=[]
        for bank in banks:
            complete=True;late=True;equal=True;own_uses=0;own_seeds=0
            coverage={c:0 for c in CONTROLS[1:]};advantages={c:0 for c in CONTROLS[1:]}
            choice=0;fixed=0;retained=0;retained_fixed=0
            opportunities=[]
            for offset,seed in enumerate(bank):
                row=rows[seed,role,'intact']
                complete &= bool(row['completed'] and row['decisions']==60 and row['deaths']==0)
                late &= len(row['last_four'])==4 and all(a is not None and a['success']==1 for a in row['last_four'])
                uses=row['own']['postchange_correct_uses']
                # Software strata retain their authored registry; never science acceptance.
                mixed=(seed in (2100282,2100283)) if software else (offset>=2)
                if mixed:
                    own_uses+=len(uses);own_seeds+=int(bool(uses))
                if offset<2 and not software:
                    equal &= row['physical_sha256']==rows[seed,role,'history_misbound']['physical_sha256']
                choice+=row['choice_yield'];retained+=row['retained_operating_surplus']
                fixed+=max(rows[seed,r,'intact']['choice_yield'] for r in FIXED)
                retained_fixed+=max(rows[seed,r,'intact']['retained_operating_surplus'] for r in FIXED)
                left=window(row)
                for control in CONTROLS[1:]:
                    right=window(rows[seed,role,control]);common=set(left)&set(right)
                    delta=sum(left[k]-right[k] for k in common)
                    coverage[control]+=len(common);advantages[control]+=delta
                    all_deltas[control].append(delta)
                    opportunities.append(dict(seed=seed,control=control,common=len(common),correct_delta=delta,
                        intact_served=len(left),control_served=len(right)))
            gates=dict(complete=bool(complete),last_four_correct=bool(late),
                common_active=all(v>=80 for v in coverage.values()),
                causal_advantage=all(v>=8 for v in advantages.values()),
                changed_own_revision_use=own_uses>=4 and own_seeds>=3,
                equal_constant_invariant=bool(equal),paid_choice=choice>=fixed+16)
            decisions.append(dict(seeds=list(bank),gates=gates,common_active=coverage,
                correct_advantages=advantages,changed_own_uses=own_uses,changed_own_seed_count=own_seeds,
                choice_yield=choice,fixed_choice_oracle=fixed,retained_surplus=retained,
                fixed_retained_oracle=retained_fixed,retained_superiority=retained>retained_fixed,
                actual_opportunities=opportunities))
        tests={c:signs(v) for c,v in all_deltas.items()}
        accepted=not software and all(all(b['gates'].values()) for b in decisions) and all(t['passed'] for t in tests.values())
        capacities.append(dict(capacity=q,accepted=accepted,banks=decisions,paired_signs=tests))
    return dict(version='REVISION84-ACCEPTANCE-v1',software_only=software,
        capacities=capacities,accepted_capacities=[c['capacity'] for c in capacities if c['accepted']],
        logical_original_denominator=18*len(expected),stage_credit=False,
        scope='Supplied mechanism/acquired revisions; nominal choice is not retained energy, fitness or evolved architecture')
