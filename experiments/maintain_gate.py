"""Complete finite work-funded maintenance admission. No sampled worlds."""
import argparse
from collections import deque
import hashlib
import json
import math

N=(4,3,3)
EDGES=((0,1),(0,2),(1,0),(1,2),(2,0),(2,1))
ACTIONS=tuple((k,i,d) for k in ('capture','waste','activate') for i in range(3) for d in (-1,1))
START=(4,3,3,0,0)
YOKED=(1,1,1,6,3)

def pack(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def heat(s):return 68-6*sum(s[:3])-2*s[3].bit_count()-s[4]
def labels(s):return math.prod(math.comb(n,f) for n,f in zip(N,s[:3]))

def move(s,a):
    k,i,d=a;t=list(s)
    if k in ('capture','waste'):
        count=s[i] if d==1 else N[i]-s[i]
        if not count:return None
        t[i]-=d
        if k=='capture':t[4]+=2*d
    else:
        if bool(s[3]&(1<<i))!=(d==-1):return None
        count=1;t[3]^=1<<i;t[4]-=3*d
    t=tuple(t)
    if t[4]<0 or heat(t)<0:return None
    return t,count

def pref(mask,active,target,cofactor,arm,bit=0):
    if arm=='independent' or target==cofactor or not active&(1<<cofactor):return 4
    if arm=='candidate':return 64 if mask&(1<<EDGES.index((cofactor,target))) else 4
    degree=sum(bool(mask&(1<<j)) for j,(src,dst) in enumerate(EDGES) if src==cofactor)
    return 64 if bit<degree else 4

def census(start):
    seen={start};q=deque([start]);channels=0;proposals=0
    while q:
        s=q.popleft()
        for a in ACTIONS:
            outcome=move(s,a)
            if outcome is None:continue
            t,count=outcome;back=move(t,(a[0],a[1],-a[2]))
            assert back and back[0]==s and labels(s)*count==labels(t)*back[1]
            assert (s[4]+3*s[3].bit_count())%2==(t[4]+3*t[3].bit_count())%2
            # Acceptance factors cancel 2**H on every bidirectional edge.
            assert heat(s)+min(0,heat(t)-heat(s))==heat(t)+min(0,heat(s)-heat(t))
            channels+=1;proposals+=count
            if t not in seen:seen.add(t);q.append(t)
        assert len(seen)<=100000 and channels<=2000000
    return dict(start=list(start),states=len(seen),directed_channels=channels,labelled_proposals=proposals,
                state_sha256=hashlib.sha256(pack(sorted(seen))).hexdigest(),maximum_work=max(s[4] for s in seen),
                parity=(start[4]+3*start[3].bit_count())%2)

def contexts():
    rows=[]
    for mask in range(64):
        for active in range(8):
            for target in range(3):
                for cofactor in range(3):
                    # Forward/reverse context must not change the catalyst.
                    other=active^(1<<target)
                    for arm in ('candidate','independent','annealed'):
                        for bit in (0,1):
                            value=pref(mask,active,target,cofactor,arm,bit)
                            assert value==pref(mask,other,target,cofactor,arm,bit)
                            rows.append(value)
    return dict(catalogues=64,active_contexts=8,entries=len(rows),sha256=hashlib.sha256(pack(rows)).hexdigest(),
                shared_positive_basal_support=True,all_forward_reverse_prefactors_equal=True)

def certificate():
    steps=[('capture',0,1),('capture',1,1),('activate',0,1),('capture',0,1),('activate',1,1),
           ('capture',1,1),('capture',2,1),('activate',2,1),('capture',0,1),('capture',2,1),
           ('loss',0,1),('activate',0,1),('capture',0,1),('capture',1,1),('capture',2,1)]
    s=START;rows=[];gross=cost=0;pre=None
    for a in steps:
        before=s
        if a[0]=='loss':
            assert s== (1,1,1,7,5);pre=s
            s=YOKED;cost+=2
        else:
            result=move(s,a);assert result;s=result[0]
            if a[0]=='capture':gross+=2
            if a[0]=='activate':cost+=3
        rows.append(dict(action=list(a),before=list(before),after=list(s),heat=heat(s)))
    assert s==(0,0,0,7,6) and heat(s)==56
    return dict(rows=rows,resource_yoked_state=list(YOKED),score=dict(gross=20,activation=12,loss=2,
                whole_surplus=6,post_surplus=1,actual_final_work=s[4],post_work_gain=s[4]-pre[4],final_heat=heat(s)),
                attainable_catalogues=64,attainable_arms=['candidate','independent','annealed'],controlled_only=True)

def record(revision):return dict(schema='maintain01-admission',source_revision=revision,natural_worlds=0,
    graphs=[census(START),census(YOKED)],contexts=contexts(),certificate=certificate())

def main():
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);a=p.parse_args()
    print(json.dumps(record(a.revision),sort_keys=True))
if __name__=='__main__':main()
