"""Independent Cartesian/DFS admission and authored-path interpreter."""
import argparse
import hashlib
import itertools
import json
import math

def encoded(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def thermal(s):return 68-6*(s[0]+s[1]+s[2])-2*sum((s[3]>>i)&1 for i in range(3))-s[4]

def successor(s,kind,index,sign):
    f=list(s[:3]);bits=s[3];work=s[4]
    if kind=='activate':
        old=(bits>>index)&1
        if old!=(sign<0):return None
        bits^=1<<index;work-=3*sign;count=1
    else:
        count=f[index] if sign>0 else (4,3,3)[index]-f[index]
        if count==0:return None
        f[index]-=sign
        if kind=='capture':work+=2*sign
    target=(*f,bits,work)
    if work<0 or thermal(target)<0:return None
    return target,count

def graph(initial):
    initial=tuple(initial);stack=[initial];seen={initial};edges=weighted=0
    while stack:
        s=stack.pop()
        g=math.comb(4,s[0])*math.comb(3,s[1])*math.comb(3,s[2])
        for i in range(3):
            for direction in (1,-1):
                for kind in ('activate','waste','capture'):
                    result=successor(s,kind,i,direction)
                    if result is None:continue
                    t,count=result;reverse=successor(t,kind,i,-direction)
                    assert reverse and reverse[0]==s
                    gt=math.comb(4,t[0])*math.comb(3,t[1])*math.comb(3,t[2])
                    assert g*count==gt*reverse[1]
                    # Independently verify thermal weighted rates as integers.
                    hf,ht=thermal(s),thermal(t)
                    assert g*count*2**min(hf,ht)==gt*reverse[1]*2**min(ht,hf)
                    edges+=1;weighted+=count
                    if t not in seen:seen.add(t);stack.append(t)
        assert len(seen)<=100000 and edges<=2000000
    parity=(initial[4]+3*initial[3].bit_count())%2
    compatible=set()
    for f0,f1,f2,bits in itertools.product(range(5),range(4),range(4),range(8)):
        budget=68-6*(f0+f1+f2)-2*bits.bit_count()
        for work in range(budget+1):
            if (work+3*bits.bit_count())%2==parity:compatible.add((f0,f1,f2,bits,work))
    # A Cartesian energy/parity bound is not automatically a reachable census.
    assert seen<=compatible
    return dict(start=list(initial),states=len(seen),directed_channels=edges,labelled_proposals=weighted,
                state_sha256=hashlib.sha256(encoded(sorted(seen))).hexdigest(),maximum_work=max(s[4] for s in seen),parity=parity)

def context_check():
    entries=[];links=[(j,i) for j in range(3) for i in range(3) if i!=j]
    def rate(mask,bits,i,j,arm,coin):
        if i==j or not (bits>>j)&1 or arm=='independent':return 4
        row=[int(bool(mask&(1<<k))) for k,(src,dst) in enumerate(links) if src==j]
        if arm=='annealed':return 64 if coin<sum(row) else 4
        return 64 if mask&(1<<links.index((j,i))) else 4
    for mask in range(64):
        for bits in range(8):
            for i in range(3):
                for j in range(3):
                    for arm in ('candidate','independent','annealed'):
                        for coin in (0,1):
                            r=rate(mask,bits,i,j,arm,coin)
                            assert r==rate(mask,bits^(1<<i),i,j,arm,coin);entries.append(r)
        for j in range(3):
            targets=[i for i in range(3) if i!=j]
            quenched=sum(rate(mask,7,i,j,'candidate',0) for i in targets)
            annealed=sum(rate(mask,7,i,j,'annealed',c) for i in targets for c in (0,1))
            assert 2*quenched==annealed
    return dict(catalogues=64,active_contexts=8,entries=len(entries),sha256=hashlib.sha256(encoded(entries)).hexdigest(),
                shared_positive_basal_support=True,all_forward_reverse_prefactors_equal=True)

def path(cert):
    s=(4,3,3,0,0);gross=activation=loss=0;pre=None;postgross=postactivation=0
    expected=[('capture',0),('capture',1),('activate',0),('capture',0),('activate',1),('capture',1),
              ('capture',2),('activate',2),('capture',0),('capture',2),('loss',0),('activate',0),
              ('capture',0),('capture',1),('capture',2)]
    assert len(cert['rows'])==len(expected)
    for row,(kind,i) in zip(cert['rows'],expected):
        assert row['action']==[kind,i,1] and row['before']==list(s)
        if kind=='loss':
            assert s==(1,1,1,7,5);pre=s;loss+=2;s=(*s[:3],6,s[4]-2)
        else:
            result=successor(s,kind,i,1);assert result;s=result[0]
            if kind=='capture':gross+=2;postgross+=2 if pre else 0
            else:activation+=3;postactivation+=3 if pre else 0
        assert row['after']==list(s) and row['heat']==thermal(s)
    score=dict(gross=gross,activation=activation,loss=loss,whole_surplus=gross-activation-loss,
               post_surplus=postgross-postactivation-loss,actual_final_work=s[4],post_work_gain=s[4]-pre[4],final_heat=thermal(s))
    assert cert['score']==score and min(score['whole_surplus'],score['post_surplus'])>0
    assert thermal(s)>=thermal(pre)>=8 and s[3]==7 and cert['resource_yoked_state']==[1,1,1,6,3]
    assert cert['attainable_catalogues']==64 and cert['attainable_arms']==['candidate','independent','annealed'] and cert['controlled_only'] is True
    return score

def audit(record,revision):
    assert record['schema']=='maintain01-admission' and record['source_revision']==revision and record['natural_worlds']==0
    assert [g['start'] for g in record['graphs']]==[[4,3,3,0,0],[1,1,1,6,3]]
    assert record['contexts']==context_check()
    for g in record['graphs']:assert g==graph(g['start'])
    score=path(record['certificate'])
    return dict(schema='maintain01-decision',source_revision=revision,admission_passed=True,natural_worlds=0,
        graphs=record['graphs'],catalogues=64,controlled_score=score,independent_complete_reachability=True,
        self_maintenance_demonstrated=False,next_decision='Freeze reviewed dynamics and independent interpreter, then execute unscreened registered panel.')

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
    try:
        with open(a.input,encoding='utf-8') as f:r=json.load(f)
        print(json.dumps(audit(r,a.revision),sort_keys=True))
    except (AssertionError,ValueError,KeyError,TypeError) as e:
        print(json.dumps(dict(verified=False,error=str(e))));raise SystemExit(2)
if __name__=='__main__':main()
