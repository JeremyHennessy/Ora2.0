"""Separate DFS and factorial-weight stationary-flow interpreter."""
import argparse,hashlib,json,math
from fractions import Fraction
from .local_audit import interpret,thermal

NAMES=('candidate','independent','shuffled')
def encode(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def ratio(n,d=1):
    q=Fraction(n,d);return [q.numerator,q.denominator]
def measure(arm):
    stack=[(10,0,0,0,0,0)];visited=set(stack);count=0;normal=0;protected=conditional=0
    densities=[{}, {}, {}, {}];sums=[Fraction(0) for _ in range(5)]
    actions=[(k,0,d) for k in ('capture','decay','work') for d in (-1,1)]+[('activate',j,d) for j in range(2) for d in (-1,1)]+[('bond',0,d) for d in (-1,1)]+[('hop',j,1) for j in range(2)]
    def degeneracy(v):return math.factorial(10)//(math.factorial(v[0])*math.factorial(v[1])*math.factorial(10-v[0]-v[1]))*2**thermal(v)
    def choices(v,a):
        k,j,d=a
        if k not in ('capture','decay','work'):return 1
        index={'capture':(1,0),'decay':(2,1),'work':(2,1)}[k][d==1]
        return [v[0],v[1],10-v[0]-v[1]][index]
    while stack:
        v=stack.pop();g=degeneracy(v);normal+=g
        values=(v[3],v[2].bit_count(),v[5],thermal(v))
        for table,value in zip(densities,values):table[value]=table.get(value,0)+g
        if thermal(v)>=8:protected+=g;conditional+=g*v[3]
        for a in actions:
            step=interpret(v,a,arm)
            if step is None:continue
            u,r=step;k,j,d=a;reverse=(k,j,1 if k=='hop' else -d);previous,q=interpret(u,reverse,arm);assert previous==v
            current=g*r*choices(v,a)/68;opposite=degeneracy(u)*q*choices(u,reverse)/68;assert current==opposite
            sums[4]+=(u[5]-v[5])*current
            if k=='work':sums[int(d==-1)]+=2*current
            if k=='activate':sums[2+int(d==-1)]+=3*current
            count+=1
            if u not in visited:visited.add(u);stack.append(u)
            if count>4000000 or len(visited)>250000:raise ValueError('Independent cap')
    assert sums[4]==0 and all((10,0,0,0,p,0) in visited for p in range(4))
    labels=('bound','active','work','heat');means={key:ratio(sum(k*v for k,v in tab.items()),normal) for key,tab in zip(labels,densities)}
    return dict(arm=arm,states=len(visited),edges=count,state_sha256=hashlib.sha256(encode(sorted(visited))).hexdigest(),normalizer=normal,histograms={key:{str(k):ratio(v,normal) for k,v in sorted(tab.items())} for key,tab in zip(labels,densities)},expectations=means,bound_probability=means['bound'],protected_heat_probability=ratio(protected,normal),conditional_bound_probability=ratio(conditional,protected),flows={k:ratio(q/normal) for k,q in zip(('work_forward','work_reverse','activation_debit','activation_refund','total_net'),sums)},connected=True)

def audit(data,revision):
    assert data['schema']=='equilibrium01' and data['source_revision']==revision and data['law_revision']=='cb2b08c94475bfb96333817f448cd4a4037c7e42' and data['natural_worlds']==0
    expected=[measure(a) for a in NAMES];assert expected==data['records']
    distributions=[{k:v for k,v in r.items() if k not in ('arm','flows')} for r in expected];assert distributions.count(distributions[0])==3
    assert all(r['flows']['work_forward']==r['flows']['work_reverse'] and r['flows']['activation_debit']==r['flows']['activation_refund'] and r['flows']['total_net']==[0,1] for r in expected)
    prob=Fraction(*expected[0]['bound_probability'])
    return dict(verified=True,source_revision=revision,natural_worlds=0,unchanged_law=True,states_per_arm=expected[0]['states'],edges_per_arm=expected[0]['edges'],identical_stationary_distributions=True,bound_probability=ratio(prob),bound_probability_decimal=float(prob),stationary_expected_bound_in_32=ratio(32*prob),stationary_expected_bound_in_32_decimal=float(32*prob),stationary_net_work_per_attempt=[0,1],finite_time_exposure_bound=False,old_endpoints_changed=False,new_mechanism_admitted=False,self_maintenance_demonstrated=False)
def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
    try:
        with open(a.input,encoding='utf-8') as f:data=json.load(f)
        print(json.dumps(audit(data,a.revision),sort_keys=True))
    except (AssertionError,KeyError,ValueError,TypeError) as error:print(json.dumps(dict(verified=False,error=str(error))));raise SystemExit(2)
if __name__=='__main__':main()
