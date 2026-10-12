"""Descriptive paired bills only; sealed full VM/origin proof is a precondition."""
SEEDS=tuple(range(44200,44208))
def identities(): return tuple(range(256))
from .digital_history33_endpoint import validate, MODES, REFERENCES


def diagnose(bank):
    expected={(f'candidate{i}',s,c) for i in identities() for s in SEEDS for c in MODES}
    expected|={(r,s,c) for r in REFERENCES for s in SEEDS for c in MODES}
    rows=bank['rows'];by={}
    for row in rows:
        k=(row['role'],row['seed'],row['control'])
        if type(row['seed']) is not int or k in by: raise ValueError('identity')
        validate(row['metric']);by[k]=row['metric']
    if set(by)!=expected: raise ValueError('whole sealed census required')
    out=[]
    for i in sorted(identities()):
        for s in SEEDS:
            a={c:by[f'candidate{i}',s,c] for c in MODES};x=a['intact']
            if a['own_disrupted']['delivered_own']: raise ValueError('unrelated labelled own')
            if len({m['formation'] for m in a.values()})!=1: raise ValueError('unmatched formation')
            refs={r:by[r,s,'intact'] for r in REFERENCES}
            if not all(refs[r]['completed'] for r in ('affine3','alternating')): raise ValueError('ordinary precondition')
            complete=all(m['completed'] for m in a.values())
            personal=x['delivered_own'] and x['both_own_outcomes'] and x['own_origins']>=16
            rs=[m for m in refs.values() if m['completed']]
            best_t=min(m['completion_tick'] for m in rs);best_w=min(m['paid_work'] for m in rs)
            gaps={c:[x['completion_tick']-a[c]['completion_tick'],x['paid_work']-a[c]['paid_work']] if x['completed'] and a[c]['completed'] else None for c in MODES[1:]}
            control=complete and all(all(v<0 for v in gaps[c]) for c in MODES[1:])
            fixed=x['completed'] and x['completion_tick']<best_t and x['paid_work']<best_w
            out.append(dict(path_id=i,seed=s,complete_all=complete,personal=personal,
                control_gaps=gaps,fixed_gaps=[x['completion_tick']-best_t,x['paid_work']-best_w] if x['completed'] else None,
                best_latency_roles=[r for r in REFERENCES if refs[r]['completed'] and refs[r]['completion_tick']==best_t],
                best_work_roles=[r for r in REFERENCES if refs[r]['completed'] and refs[r]['paid_work']==best_w],
                strict_control_benefit=control,strict_fixed_benefit=fixed))
    return finish(out)


def finish(cells):
    return dict(cells=cells,summary=dict(cells=len(cells),complete_all=sum(c['complete_all'] for c in cells),
        personal_complete=sum(c['complete_all'] and c['personal'] for c in cells),
        strict_control_benefit=sum(c['strict_control_benefit'] for c in cells),
        personal_control_benefit=sum(c['personal'] and c['strict_control_benefit'] for c in cells),
        personal_complete_fixed_benefit=sum(c['complete_all'] and c['personal'] and c['strict_fixed_benefit'] for c in cells),
        personal_control_benefit_without_fixed=sum(c['personal'] and c['strict_control_benefit'] and not c['strict_fixed_benefit'] for c in cells)),
        classification='descriptive_paired_bills_no_rescore',learning=False,stage_credit=False)


if __name__=='__main__':
    import json,sys
    print(json.dumps(diagnose(json.load(open(sys.argv[1]))),sort_keys=True,separators=(',',':')))
