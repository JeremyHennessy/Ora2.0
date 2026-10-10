"""Separate physical interpreter, gather propagation and phase enumeration."""
import argparse,hashlib,json,math
from fractions import Fraction

def coded(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def thermal(s):return 20-s[2]-2*s[1]
def transition(s,kind,d):
    left,active,work=s
    if kind=='form':
        if (d>0 and active) or (d<0 and not active):return None
        target=(left,1-active,work-3*d);count=10
    else:
        count=(left,10-left)[d<0]
        if count==0:return None
        target=(left-d,active,work+d*(kind=='work'))
    if target[2]<0 or thermal(target)<0:return None
    return target,count
def rate(s,k,d,arm):
    result=transition(s,k,d)
    if result is None:return Fraction(0)
    t,n=result
    if k=='form':barrier=4
    elif arm=='independent':barrier=10
    else:
        bodyfavored=(bool(s[1]) and arm=='candidate') or (not s[1] and arm=='inverted')
        barrier=(16,4)[not bodyfavored] if k=='work' else (4,16)[not bodyfavored]
    return Fraction(n*barrier,6*10*64)*Fraction(1,2**max(0,thermal(s)-thermal(t)))
CHANNELS=[(k,d) for d in (1,-1) for k in ('form','passive','work')]
def enumerate_graph():
    seen={(10,0,0)};stack=[(10,0,0)];edges=proposals=0
    while stack:
        s=stack.pop()
        for k,d in CHANNELS:
            out=transition(s,k,d)
            if out is None:continue
            t,n=out;back=transition(t,k,-d);assert back and back[0]==s
            for arm in ('candidate','independent','inverted'):
                a=rate(s,k,d,arm);b=rate(t,k,-d,arm)
                assert a*math.comb(10,s[0])*2**thermal(s)==b*math.comb(10,t[0])*2**thermal(t)
            edges+=1;proposals+=n
            if t not in seen:seen.add(t);stack.append(t)
    assert len(seen)<=2000 and edges<=20000
    return sorted(seen),dict(states=len(seen),directed_channels=edges,labelled_proposals=proposals,
        state_sha256=hashlib.sha256(coded(sorted(seen))).hexdigest(),maximum_work=max(s[2] for s in seen))
def evidence_flag(s,kind,d,previous):return 0 if kind=='form' else int(previous or kind=='work' and d>0 and s[1])
def maximum_after_loss(left,prework):
    start=(left,0,prework-2,0);todo=[start];seen={start};best=-1
    while todo:
        node=todo.pop();s=node[:3];flag=node[3]
        if s[1] and flag:best=max(best,s[2])
        for k,d in CHANNELS:
            outcome=transition(s,k,d)
            if outcome is not None:
                t=(*outcome[0],evidence_flag(s,k,d,flag))
                if t not in seen:seen.add(t);todo.append(t)
    return best
def propagate(states,arm):
    nodes=[(*s,flag) for s in states for flag in ((0,1) if s[1] else (0,))]
    incoming={s:[] for s in nodes}
    for node in nodes:
        s=node[:3];flag=node[3];total=Fraction(0)
        for k,d in CHANNELS:
            p=rate(s,k,d,arm)
            if p:
                t=transition(s,k,d)[0];incoming[(*t,evidence_flag(s,k,d,flag))].append((node,float(p)));total+=p
        assert total<=1;incoming[node].append((node,float(1-total)))
    mass={s:float(s==(10,0,0,0)) for s in nodes}
    for _ in range(2048):mass={s:math.fsum(mass[src]*p for src,p in incoming[s]) for s in nodes}
    assert abs(math.fsum(mass.values())-1)<1e-10
    phases=[];exposed=[];feasible=[]
    for (n,b,w,f),p in mass.items():
        if b and f and w>=2:
            maximum=maximum_after_loss(n,w);okay=maximum>w
            phases.append(dict(left=n,pre_work=w,probability=p,maximum_rebuilt_work=maximum,feasible=okay));exposed.append(p)
            if okay:feasible.append(p)
    return dict(arm=arm,distribution=[[list(s),mass[s]] for s in nodes],mass=math.fsum(mass.values()),
        exposed_probability=math.fsum(exposed),feasible_exposed_probability=math.fsum(feasible),phases=phases)
def path(cert):
    expected=[('work',1)]*3+[('form',1)]+[('work',1)]*2+[('loss',1)]+[('work',1)]*3+[('form',1)]+[('work',1)]*2+[('passive',-1),('work',1)]
    s=(10,0,0);net=cost=loss=0;pre=None
    assert len(cert['rows'])==len(expected)
    for row,(k,d) in zip(cert['rows'],expected):
        assert row['action']==[k,d] and row['before']==list(s)
        if k=='loss':assert s==(5,1,2);pre=s;s=(s[0],0,s[2]-2);loss+=2
        else:
            out=transition(s,k,d);assert out;s=out[0]
            if k=='work':net+=d
            if k=='form':cost+=3*d
        assert row['after']==list(s) and row['heat']==thermal(s)
    score=dict(final_work=s[2],post_gain=s[2]-pre[2],net_transfers=net,formation=cost,loss=loss,
        source_heat_drawdown=20-thermal(s),final_bound_potential=2*s[1],whole_surplus=net-cost-loss)
    assert score==cert['score'] and score['post_gain']>0 and cert['controlled_only'] is True
    return score
def audit(record,revision):
    assert record['schema']=='entropy01-admission' and record['source_revision']==revision and record['natural_worlds']==0
    states,g=enumerate_graph();assert record['graph']==g
    assert [x['arm'] for x in record['arms']]==['candidate','independent','inverted']
    summaries=[]
    for reported in record['arms']:
        actual=propagate(states,reported['arm'])
        for key in ('mass','exposed_probability','feasible_exposed_probability'):assert abs(actual[key]-reported[key])<1e-10
        assert len(actual['distribution'])==len(reported['distribution'])
        for (s,p),(t,q) in zip(actual['distribution'],reported['distribution']):assert s==t and abs(p-q)<1e-10
        assert len(actual['phases'])==len(reported['phases'])
        for a,b in zip(actual['phases'],reported['phases']):
            assert {k:v for k,v in a.items() if k!='probability'}=={k:v for k,v in b.items() if k!='probability'}
            assert abs(a['probability']-b['probability'])<1e-10
        summaries.append({k:actual[k] for k in ('arm','exposed_probability','feasible_exposed_probability')})
    assert record['numerical_guard']==1e-6
    admitted=summaries[0]['feasible_exposed_probability']-1e-6>=.75
    assert admitted==record['admission_passed']
    return dict(schema='entropy01-decision',source_revision=revision,natural_worlds=0,graph=g,startup=summaries,
        admission_passed=admitted,classification='ADMITTED_FOR_FUTURE_PROTOCOL' if admitted else 'NOT_ADMITTED_OPPORTUNITY',
        numerical_guard=1e-6,controlled_score=path(record['certificate']),full_unconditional_distribution_independently_equal=True,
        self_maintenance_demonstrated=False,next_decision='Freeze a distinct dynamics protocol.' if admitted else 'Close exact toy law; do not execute fresh sampled worlds or tune time/endowment/costs.')
def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
    try:
        with open(a.input,encoding='utf-8') as f:r=json.load(f)
        print(json.dumps(audit(r,a.revision),sort_keys=True))
    except (AssertionError,ValueError,KeyError,TypeError) as e:
        print(json.dumps(dict(verified=False,error=str(e))));raise SystemExit(2)
if __name__=='__main__':main()
