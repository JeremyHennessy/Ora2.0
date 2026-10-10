"""Frozen finite stoichiometric opportunities; no admitted dynamics or work yield."""
import argparse,json

VECTORS=((1,0,1,1,0),(0,2,2,0,0),(0,1,1,1,0),(1,1,2,0,0),(2,0,2,0,0),(0,0,0,2,2),(0,0,0,2,1))
STEPS=((-1,-1,1,1,0,0,0),(-1,0,1,-1,1,0,0),(0,1,-2,0,0,-1,2))

def inventory(s):return tuple(sum(s[i]*VECTORS[i][j] for i in range(7)) for j in range(5))
def case(t,b,f,full=False):
    start=(t,b,0,0,0,f,0,0,0);seen={start};stack=[start];edges=0;goals=[];original=inventory(start)
    while stack:
        s=stack.pop();assert inventory(s)==original
        if s[7]==2:goals.append(s)
        for k,delta in enumerate(STEPS):
            material=tuple(s[i]+delta[i] for i in range(7))
            if min(material)<0:continue
            phase=s[7];post=s[8]
            if k==0 and phase>0:phase=2;post+=1
            options=[material+(phase,post)]
            if k==1 and s[7]==0:options.append(material+(1,0))
            for nxt in options:
                edges+=1
                if nxt not in seen:seen.add(nxt);stack.append(nxt)
    row=[t,b,f,len(seen),edges,bool(goals),max((s[3]+s[4] for s in goals),default=0),max((s[8] for s in goals),default=0),min((f-s[5] for s in goals),default=None),min((t-s[0] for s in goals),default=None)]
    return (row,[list(s) for s in sorted(seen)]) if full else row
def record(revision):
    cases=[case(t,b,f,True) for t in range(9) for b in range(5) for f in range(5)]
    rows=[x[0] for x in cases];ledgers=[x[1] for x in cases]
    return dict(schema='amphiphile01-accounting',source_revision=revision,rows=rows,complete_state_ledgers=ledgers,primary_arrangements=['aggregate','independent','complete_label_shuffle'],same_stoichiometric_opportunities=True,natural_worlds=0,physical_law_installed=False,net_cycle=dict(consumed=dict(tail_thiol=2,peroxide=1),produced=dict(tail_disulfide=1,water=2),head_change=0),usable_output_J=None,full_work_cost_J=None,autonomous_catalyst_renewal_demonstrated=False,classification='MATERIAL_FEASIBLE_KINETICS_AND_WORK_UNCALIBRATED',admission_passed=False)
def main():
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);a=p.parse_args();print(json.dumps(record(a.revision),sort_keys=True))
if __name__=='__main__':main()
