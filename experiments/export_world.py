"""Frozen raw-start portable-work panel; preserves all accepted/rejected draws."""
import argparse,hashlib,json,random,struct
from .export_gate import ARMS,transition,heat,pack

ALPHABET=[(k,j,d) for j in range(10) for k in ('assemble','drive','waste') for d in (-1,1)] + [(k,0,d) for k in ('passive','relax') for d in (-1,1)] + [('load',j,d) for j in range(10) for d in (-1,1)] + [('lhop',j,1) for j in range(10)] + [('hop',j,1) for j in range(2)]

def trajectory(seed,arm):
    rng=random.Random(seed)
    position=rng.getrandbits(1)+2*rng.getrandbits(1)
    sites=[rng.getrandbits(1) for _ in range(10)]
    loaded=[False]*10;load_origins=[None]*10;tokens=[0]*10;virgin=[True]*10
    q=0;charge=None;events=[];states=[];digest=hashlib.sha256()
    objects=[dict(id=j,atom=j,parent=None,state='raw') for j in range(2)]
    owners=[0,1];dimers=[];current=last=rebuilt=loss=None
    gross=other=net=postnet=cost=postcost=occupancy=0
    prefresh=rebuiltuse=False;prework=preheat=None
    def aggregate():
        counts=[sum(site==i%2 and flag==(i>=2) for site,flag in zip(sites,loaded)) for i in range(4)]
        return (tokens.count(0),q,position,*counts)
    states.append(list(aggregate())+[heat(aggregate())])
    def eligibility(action):
        k,j,d=action
        if k in ('assemble','drive','waste') and tokens[j]!=int(d==-1):return None
        if k=='load' and loaded[j]!=(d==-1):return None
        group=sites[j]+2*int(loaded[j]) if k=='lhop' else sites[j] if k=='load' else j if k=='hop' else 0
        return transition(aggregate(),(k,group,d),arm)
    def apply(action,step,result=None):
        nonlocal q,position,charge,current,last,rebuilt,loss,gross,other,net,postnet,cost,postcost,prefresh,rebuiltuse,prework,preheat
        k,j,d=action;s=aggregate()
        e=dict(step=step,action=list(action),before=list(s),dimer=current,origin=None)
        bill=6*d if k=='assemble' else d if k=='passive' else 2 if k=='damage' else 0
        if k=='damage':
            assert step==2048 and q and loaded[j] and sites[j]==position//3
            prework=2*sum(loaded);preheat=heat(s);loaded[j]=False;load_origins[j]=None;q=0;loss=step;charge=None;e['target_atom']=0
        else:
            t,rate,_=result;e['rate']=[rate.numerator,rate.denominator];q,position=t[1:3]
            if k in ('assemble','drive','waste'):
                if k=='drive':charge=('fresh-fuel' if virgin[j] else 'regenerated-fuel') if d==1 else None
                tokens[j]=int(d==1);virgin[j]=False
            if k=='lhop':sites[j]^=1
            if k=='load':
                e['origin']=charge if d==1 else 'paid-load-reversal'
                loaded[j]=d==1;load_origins[j]=charge if d==1 else None
                value=2*d if d==-1 or charge=='fresh-fuel' else 0
                net+=value
                if loss is not None:postnet+=value
                if d==1:
                    gross+=2*int(charge=='fresh-fuel');other+=2*int(charge!='fresh-fuel')
                    if step<2048 and charge=='fresh-fuel':prefresh=True
                    if loss is not None and current==rebuilt and charge=='fresh-fuel':rebuiltuse=True
                charge=None if d==1 else 'paid-load-reversal'
            assert aggregate()==t
        cost+=bill
        if loss is not None:postcost+=bill
        if k in ('assemble','passive','damage'):
            children=[]
            for atom,parent in enumerate(owners.copy()):
                child=len(objects);objects.append(dict(id=child,atom=atom,parent=parent,state='bound' if q else 'raw'));owners[atom]=child;children.append(child)
            e['objects']=children
            if q:
                current=len(dimers);dimers.append(dict(id=current,parent=last,components=owners.copy()));last=current
                if loss is not None and rebuilt is None:rebuilt=current
            else:current=None
            charge=None;e['new_dimer']=current
        e['after']=list(aggregate());events.append(e);states.append(e['after']+[heat(aggregate())])
    for step in range(4096):
        if step==2048 and q:
            payment=next((j for j in range(10) if loaded[j] and sites[j]==position//3),None)
            if payment is not None:apply(('damage',payment,1),step)
        slot=rng.randrange(96);draw=rng.getrandbits(32);noise=rng.getrandbits(32)
        digest.update(struct.pack('<III',slot,draw,noise));a=ALPHABET[slot];r=eligibility(a)
        if r is not None and draw*r[1].denominator<2**32*r[1].numerator:apply(a,step,r)
        occupancy+=int(q!=0)
    final=aggregate();work=2*sum(loaded);post=None if loss is None else work-prework;exposed=loss is not None and prefresh
    endpoint=exposed and rebuilt is not None and rebuilt==current and rebuiltuse and min(work,post,net-cost,postnet-postcost)>0 and heat(final)>=max(8,preheat)
    score=dict(endpoint=bool(endpoint),functioning_loss=exposed,whole_work_surplus=work,post_work_surplus=post,fresh_net_output=net,post_fresh_net_output=postnet,all_net_formation_damage_cost=cost,post_net_cost=postcost,functional_surplus=net-cost,post_functional_surplus=postnet-postcost,initial_heat_preserved=heat(final)>=8,post_heat_preserved=preheat is not None and heat(final)>=preheat,first_rebuilt_fresh_use=rebuiltuse)
    return dict(seed=seed,arm=arm,states=states,events=events,objects=objects,owners=owners,dimers=dimers,current_dimer=current,first_rebuilt=rebuilt,damage_step=loss,token_states=tokens,virgin_tokens=virgin,charge_origin=charge,load_sites=sites,loaded=loaded,load_origins=load_origins,fresh_gross_work=gross,other_gross_work=other,bound_occupancy=occupancy,draw_sha256=digest.hexdigest(),rng_sha256=hashlib.sha256(pack(rng.getstate())).hexdigest(),score=score)

def main():
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--output-file');p.add_argument('--seed',type=int);p.add_argument('--arm',choices=ARMS);a=p.parse_args()
    if a.seed is not None:
        if a.arm is None:raise ValueError('Single replay requires arm')
        data=trajectory(a.seed,a.arm)
    else:data=dict(schema='export01-panel',source_revision=a.revision,records=[trajectory(s,arm) for s in range(86000,86032) for arm in ARMS])
    blob=json.dumps(data,sort_keys=True).encode()
    if a.output_file:
        if len(blob)>50*1024**2:raise ValueError('Prospective panel cap')
        with open(a.output_file,'r+b') as stream:
            if stream.read(1):raise ValueError('Externally reserved empty output required')
            stream.write(blob)
        print(json.dumps(dict(bytes=len(blob),records=len(data['records']))))
    else:print(blob.decode())

if __name__=='__main__':main()
