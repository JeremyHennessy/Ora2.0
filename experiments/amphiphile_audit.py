"""Independent queue, named species and explicit conserved inventories."""
import argparse,json
from collections import deque

NAMES=('T','B','L','A','Z','F','Q')
COMPOSITION={'T':(1,0,1,1,0),'B':(0,2,2,0,0),'L':(0,1,1,1,0),'A':(1,1,2,0,0),'Z':(2,0,2,0,0),'F':(0,0,0,2,2),'Q':(0,0,0,2,1)}
RULES=(({'T':1,'B':1},{'A':1,'L':1}),({'A':1,'T':1},{'Z':1,'L':1}),({'L':2,'F':1},{'B':1,'Q':2}))
def total(m):return tuple(sum(m.get(k,0)*v[i] for k,v in COMPOSITION.items()) for i in range(5))
def enumerate_case(t,b,f,full=False):
    first=(t,b,0,0,0,f,0,0,0);q=deque([first]);seen={first};count=0;accepted=[];origin=total(dict(zip(NAMES,first)))
    while q:
        s=q.popleft();m=dict(zip(NAMES,s));assert total(m)==origin
        if s[7]==2:accepted.append(s)
        for index,(left,right) in enumerate(RULES):
            assert total(left)==total(right)
            if any(m[k]<n for k,n in left.items()):continue
            dest=m.copy()
            for k,n in left.items():dest[k]-=n
            for k,n in right.items():dest[k]+=n
            p=s[7];post=s[8]
            if index==0 and p in (1,2):p=2;post+=1
            possibilities=[(p,post)]
            if index==1 and s[7]==0:possibilities.append((1,0))
            for phase,after in possibilities:
                nxt=tuple(dest[k] for k in NAMES)+(phase,after);count+=1
                if nxt not in seen:seen.add(nxt);q.append(nxt)
    row=[t,b,f,len(seen),count,bool(accepted),max((s[3]+s[4] for s in accepted),default=0),max((s[8] for s in accepted),default=0),min((f-s[5] for s in accepted),default=None),min((t-s[0] for s in accepted),default=None)]
    return (row,[list(s) for s in sorted(seen)]) if full else row
def audit(r,revision):
    assert r['schema']=='amphiphile01-accounting' and r['source_revision']==revision
    cases=[enumerate_case(t,b,f,True) for t in range(9) for b in range(5) for f in range(5)];rows=[x[0] for x in cases]
    assert r['rows']==rows and r['complete_state_ledgers']==[x[1] for x in cases]
    assert r['primary_arrangements']==['aggregate','independent','complete_label_shuffle'] and r['same_stoichiometric_opportunities'] is True
    assert r['natural_worlds']==0 and r['physical_law_installed'] is False
    assert r['net_cycle']==dict(consumed=dict(tail_thiol=2,peroxide=1),produced=dict(tail_disulfide=1,water=2),head_change=0)
    assert r['usable_output_J'] is None and r['full_work_cost_J'] is None and r['autonomous_catalyst_renewal_demonstrated'] is False
    assert r['classification']=='MATERIAL_FEASIBLE_KINETICS_AND_WORK_UNCALIBRATED' and r['admission_passed'] is False
    possible=[x[:3] for x in rows if x[5]]
    minimal=[x for x in possible if not any(y!=x and all(a<=b for a,b in zip(y,x)) for y in possible)]
    return dict(verified=True,source_revision=revision,cases=len(rows),reachable_states=sum(x[3] for x in rows),directed_channels=sum(x[4] for x in rows),repair_attainable_cases=len(possible),minimal_initial_inventories=minimal,maximum_total_formations=max(x[6] for x in rows),maximum_post_loss_formations=max(x[7] for x in rows),complete_tail_recycling=False,head_regeneration=True,same_control_opportunities=True,kinetic_advantage_tested=False,source_paper_reproduced=False,natural_worlds=0,self_maintenance_demonstrated=False,admission_passed=False,classification=r['classification'])
def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
    try:
        with open(a.input,encoding='utf-8') as f:r=json.load(f)
        print(json.dumps(audit(r,a.revision),sort_keys=True))
    except (AssertionError,KeyError,ValueError,TypeError) as e:print(json.dumps(dict(refused=True,error=str(e))));raise SystemExit(2)
if __name__=='__main__':main()
