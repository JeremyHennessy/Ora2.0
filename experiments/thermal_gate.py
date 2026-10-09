"""Finite thermal-work oracle; installed apparatus, not natural organization."""
import argparse
import hashlib
import json

ARMS=('candidate','independent','shuffled-working','shuffled-reversed')
ENERGY={-1:0,0:3,1:6,2:4}


def move(s,a,c,arm):
    h,k,w,q=s;kind,slot,d=a
    if kind=='build':
        if d==1 and q==-1:t=(h,k+c-3,w-c,0)
        elif d==-1 and q==0:t=(h,k-c+3,w+c,-1)
        else:return None
        barrier=c
    elif kind=='work':
        if q!=(2 if d==1 else 0):return None
        t=(h,k,w+d,0 if d==1 else 2);barrier=0
    else:
        if q==-1:return None
        gap,bath=slot.split(':');low,high,delta=(0,1,3) if gap=='high' else (2,1,2)
        if q!=(low if d==1 else high):return None
        normal=(gap=='high')==(bath=='hot')
        if arm in ('candidate','shuffled-working') and not normal:return None
        if arm=='shuffled-reversed' and normal:return None
        t=(h-d*delta if bath=='hot' else h,k-d*delta if bath=='cold' else k,w,high if d==1 else low)
        barrier=int(arm=='independent')
    if min(t[:3])<0:return None
    entropy=t[0]+2*t[1]-h-2*k
    return t,barrier+max(0,-entropy)


def actions():
    return sorted([('build','body',d) for d in (-1,1)]+[('work','load',d) for d in (-1,1)]+[('heat',g+':'+b,d) for g in ('high','low') for b in ('hot','cold') for d in (-1,1)])


def physical(c,arm):
    total=49+2*c;states=edges=0;signatures=set();digest=hashlib.sha256()
    for q in (-1,0,1,2):
        for h in range(total-ENERGY[q]+1):
            for k in range(total-ENERGY[q]-h+1):
                s=(h,k,total-ENERGY[q]-h-k,q);states+=1
                for a in actions():
                    result=move(s,a,c,arm)
                    if result is None:continue
                    t,p=result;back=move(t,(a[0],a[1],-a[2]),c,arm)
                    assert back is not None and back[0]==s
                    assert sum(t[:3])+ENERGY[t[3]]==total
                    assert s[0]+2*s[1]-p==t[0]+2*t[1]-back[1]
                    signatures.add((a,p,back[1]));edges+=1
                    digest.update((str(s)+'|'+str(a)+'|'+str(t)+'|'+str(p)+'\n').encode())
    return dict(states=states,edges=edges,rate_signatures=len(signatures),edge_sha256=digest.hexdigest())


def witness(c,arm,n):
    initial=2*c+1;s=(36,12,initial,-1);states=[list(s)];events=[]
    objects=[dict(id=i,atom=i,parent=None,state='raw',alive=True) for i in range(3)]
    owners=[0,1,2];bodies=[];current=None;before=None;net=0
    def apply(a):
        nonlocal s,current,before,net
        kind,slot,d=a;event=dict(action=list(a),body=current)
        if kind=='damage':
            assert s[3]==0 and net==5 and current is not None and s[2]>=1
            before=s[2];s=(s[0],s[1]+4,s[2]-1,-1);bodies[current]['alive']=False
        else:
            result=move(s,a,c,arm);assert result is not None
            s,exponent=result;event['rate_exponent']=exponent
            if kind=='work':net+=d
            if kind=='build':
                assert d==1;identity=len(bodies)
                bodies.append(dict(id=identity,parent=current,atoms=[0,1,2],alive=True));current=identity;event['new_body']=identity
        if kind in ('build','damage'):
            new=[]
            for atom,old in enumerate(owners):
                objects[old]['alive']=False;identity=len(objects)
                objects.append(dict(id=identity,atom=atom,parent=old,state='raw' if kind=='damage' else 'active',alive=True));new.append(identity)
            owners[:]=new;event['components']=new
        assert sum(s[:3])+ENERGY[s[3]]==49+2*c
        events.append(event);states.append(list(s))
    apply(('build','body',1))
    for cycle in range(n):
        if cycle==5:apply(('damage','body',1));apply(('build','body',1))
        apply(('heat','high:hot',1))
        apply(('heat','low:'+('hot' if arm=='independent' and c>=6 else 'cold'),-1))
        apply(('work','load',1))
    assert before is not None and current==1 and bodies[0]['alive'] is False
    return dict(states=states,events=events,objects=objects,bodies=bodies,owners=owners,pre_damage_work=before,net_cycles=n,total_energy=49+2*c,material_units=3,whole_surplus=s[2]-initial,post_damage_surplus=s[2]-before,endpoint=s[3]==0 and s[2]>initial and s[2]>before and s[1]>=12)


def record(c,arm):
    n=max(2*c+2,c+7)
    possible=arm=='independent' or arm!='shuffled-reversed' and n<=12
    return dict(cost=c,arm=arm,possible=possible,candidate_cycle_limit=12,whole_surplus_upper=12-(2*c+1),post_surplus_upper=12-(c+6),physical=physical(c,arm),witness=witness(c,arm,n) if possible else None)


def produce(revision):
    return dict(schema='thermal01',source_revision=revision,natural_worlds=0,controlled_cases=40,records=[record(c,a) for c in range(3,13) for a in ARMS])


def main():
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);a=p.parse_args();print(json.dumps(produce(a.revision),sort_keys=True))


if __name__=='__main__':main()
