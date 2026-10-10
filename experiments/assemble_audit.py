"""Independent reaction interpreter, labelled cursor and full renewal audit."""
import argparse, hashlib, json, math, random, struct
from fractions import Fraction

NAMES=('candidate','independent','shuffled')
def encoded(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def thermal(v):return 68-6*v[0]-(0,1,4,3)[v[1]]-v[3]
def interpret(v,a,arm):
    kind,j,d=a;u=list(v);factor=16
    if kind in ('assemble','drive','waste'):
        u[0]-=d
        if kind=='assemble':
            if v[1]!=int(d==-1) or v[2]%3!=0:return None
            u[1]=int(d==1);factor=(32,17,2)[NAMES.index(arm)]
        elif kind=='drive':
            if v[1]!=(1 if d==1 else 2):return None
            u[1]=2 if d==1 else 1
        else:factor=(2,17,32)[NAMES.index(arm)]
    elif kind=='hop':u[2]^=3 if v[1] else 2**j
    else:
        pair={'passive':(0,1),'relax':(2,3),'load':(3,1)}[kind]
        if v[1]!=pair[0 if d==1 else 1] or kind=='passive' and v[2]%3!=0:return None
        u[1]=pair[1 if d==1 else 0]
        if kind=='load':u[3]+=2*d
    if not 0<=u[0]<=10 or u[3]<0 or thermal(u)<0:return None
    return tuple(u),Fraction(factor,64)*Fraction(1,2**max(0,thermal(v)-thermal(u)))

def physical(arm):
    known={(10,0,p,0) for p in range(4)};pending=list(sorted(known));count=0
    actions=[(kind,0,d) for kind in ('assemble','drive','waste','passive','relax','load') for d in (-1,1)]+[('hop',j,1) for j in range(2)]
    while pending:
        v=pending.pop()
        for a in actions:
            result=interpret(v,a,arm)
            if result is None:continue
            u,r=result;k,j,d=a;back,q=interpret(u,(k,j,1 if k=='hop' else -d),arm);assert back==v
            chemical=k in ('assemble','drive','waste')
            forward=(v[0] if d==1 else 10-v[0]) if chemical else 1
            reverse=(u[0] if d==-1 else 10-u[0]) if chemical else 1
            mult=lambda x:math.factorial(10)//(math.factorial(x[0])*math.factorial(10-x[0]))*2**thermal(x)
            assert mult(v)*r*forward==mult(u)*q*reverse
            count+=1
            if u not in known:known.add(u);pending.append(u)
            if len(known)>250000 or count>4000000:raise ValueError('Independent graph cap')
    return dict(arm=arm,states=len(known),edges=count,state_sha256=hashlib.sha256(encoded(sorted(known))).hexdigest(),protected_heat_work_ceiling=max(v[3] for v in known if thermal(v)>=8))

def audit_world(record):
    arm=record['arm'];witness=record['witness'];rng=random.Random(record['seed'])
    position=0 if witness else rng.getrandbits(1)+2*rng.getrandbits(1)
    v=(10,0,position,0);tokens=[0]*10;virgin=[True]*10;charge=None
    objects=[dict(id=j,atom=j,parent=None,state='raw') for j in range(2)];owners=[0,1];dimers=[]
    body=previous=rebuilt=loss=None;index=occupied=freshgross=othergross=0;digest=hashlib.sha256();states=[list(v)+[thermal(v)]]
    bill=postbill=useful=postuseful=0;before=None;beforeheat=None;prefunction=rebuiltuse=False
    def event(a,step):
        nonlocal v,index,charge,body,previous,rebuilt,loss,freshgross,othergross,bill,postbill,useful,postuseful,before,beforeheat,prefunction,rebuiltuse
        k,j,d=a;oldbody=body;e=dict(step=step,action=list(a),before=list(v),dimer=body,origin=None)
        cost=6*d if k=='assemble' else d if k=='passive' else int(k=='damage')
        if k=='damage':
            assert step==2048 and v[1] and v[3]>=1
            before=v[3];beforeheat=thermal(v);v=(v[0],0,v[2],v[3]-1);loss=step
        else:v,rate=interpret(v,a,arm);e['rate']=[rate.numerator,rate.denominator]
        bill+=cost
        if loss is not None and step>=2048:postbill+=cost
        if k in ('assemble','drive','waste'):
            assert tokens[j]==int(d==-1);tokens[j]=int(d==1)
            if k=='drive':charge=('fresh-fuel' if virgin[j] else 'regenerated-fuel') if d==1 else None
            virgin[j]=False
        if k=='load':
            e['origin']=charge if d==1 else 'paid-work-reversal'
            value=2*d if charge=='fresh-fuel' or d==-1 else 0
            useful+=value
            if d==1:
                freshgross+=2*int(charge=='fresh-fuel');othergross+=2*int(charge!='fresh-fuel')
                if charge=='fresh-fuel' and step<2048:prefunction=True
                if charge=='fresh-fuel' and loss is not None and oldbody==rebuilt:rebuiltuse=True
                charge=None
            else:charge='paid-work-reversal'
            if loss is not None and step>=2048:postuseful+=value
        if k in ('assemble','passive','damage'):
            children=[]
            for atom,parent in enumerate(owners.copy()):
                child=len(objects);objects.append(dict(id=child,atom=atom,parent=parent,state='bound' if v[1] else 'raw'));owners[atom]=child;children.append(child)
            e['objects']=children
            if v[1]:
                body=len(dimers);dimers.append(dict(id=body,parent=previous,components=owners.copy()));previous=body
                if loss is not None and rebuilt is None:rebuilt=body
            else:body=None
            charge=None;e['new_dimer']=body
        assert v[0]==tokens.count(0);e['after']=list(v)
        assert record['events'][index]==e;index+=1;states.append(list(v)+[thermal(v)])
    if witness:
        path=[('assemble',0,1)]
        for j in (1,2,3):path.extend([('drive',j,1),('relax',0,1),('load',0,1)])
        for step,a in enumerate(path):event(a,step)
        event(('damage',0,1),2048);event(('assemble',4,1),2048)
        for j in range(5,10):
            for a in [('drive',j,1),('relax',0,1),('load',0,1)]:event(a,2049+index)
    else:
        alphabet=[(k,j,d) for j in range(10) for k in ('assemble','drive','waste') for d in (-1,1)]+[(k,0,d) for k in ('passive','relax','load') for d in (-1,1)]+[('hop',j,1) for j in range(2)]
        for step in range(4096):
            if step==2048 and v[1] and v[3]>=1:event(('damage',0,1),step)
            selected=rng.randrange(68);draw=rng.getrandbits(32);noise=rng.getrandbits(32);digest.update(struct.pack('<III',selected,draw,noise));a=alphabet[selected];k,j,d=a
            legal=k not in ('assemble','drive','waste') or tokens[j]==int(d==-1)
            r=interpret(v,a,arm) if legal else None
            if r is not None and Fraction(draw,2**32)<r[1]:event(a,step)
            occupied+=int(v[1]!=0)
    assert len(record['events'])==index and record['states']==states
    expected=dict(objects=objects,owners=owners,dimers=dimers,current_dimer=body,first_rebuilt=rebuilt,damage_step=loss,token_states=tokens,virgin_tokens=virgin,charge_origin=charge,fresh_gross_work=freshgross,other_gross_work=othergross,bound_occupancy=occupied,draw_sha256=digest.hexdigest(),rng_sha256=hashlib.sha256(encoded(rng.getstate())).hexdigest())
    for key,value in expected.items():assert record[key]==value,key
    exposed=loss is not None and prefunction;w=v[3];post=None if before is None else w-before
    endpoint=exposed and rebuilt is not None and body==rebuilt and rebuiltuse and min(w,post,useful-bill,postuseful-postbill)>0 and thermal(v)>=8 and thermal(v)>=beforeheat
    scored=dict(endpoint=bool(endpoint),functioning_loss=exposed,whole_work_surplus=w,post_work_surplus=post,fresh_net_output=useful,post_fresh_net_output=postuseful,all_net_formation_damage_cost=bill,post_net_cost=postbill,functional_surplus=useful-bill,post_functional_surplus=postuseful-postbill,initial_heat_preserved=thermal(v)>=8,post_heat_preserved=beforeheat is not None and thermal(v)>=beforeheat)
    assert scored==record['score'];return scored

def audit(data,revision):
    assert data['schema']=='assemble01' and data['source_revision']==revision
    records=data['records'];gate=data['mode']=='gate';assert data['mode'] in ('gate','panel')
    expected={(0,a) for a in NAMES} if gate else {(s,a) for s in range(85000,85032) for a in NAMES}
    assert len(records)==len(expected) and {(r['seed'],r['arm']) for r in records}==expected and all(r['witness']==gate for r in records)
    for r in records:audit_world(r)
    if gate:
        graphs=[physical(a) for a in NAMES];assert graphs==data['graphs'] and all(r['score']['endpoint'] for r in records)
        return dict(verified=True,mode='gate',source_revision=revision,mechanism_admitted=True,controlled_certificates=3,natural_worlds=0,graphs=graphs,self_maintenance_demonstrated=False)
    totals={a:dict(success=sum(r['score']['endpoint'] for r in records if r['arm']==a),exposed=sum(r['score']['functioning_loss'] for r in records if r['arm']==a),net_work=sum(r['score']['whole_work_surplus'] for r in records if r['arm']==a),functional_surplus=sum(r['score']['functional_surplus'] for r in records if r['arm']==a),paid_renewals=sum(r['first_rebuilt'] is not None for r in records if r['arm']==a),fuel_exhausted=sum(r['token_states'].count(0)==0 for r in records if r['arm']==a),other_gross_work=sum(r['other_gross_work'] for r in records if r['arm']==a),bound_attempts=sum(r['bound_occupancy'] for r in records if r['arm']==a)) for a in NAMES}
    outcomes={(r['seed'],r['arm']):r['score']['endpoint'] for r in records};comparisons=[]
    for a in NAMES[1:]:
        wins=sum(outcomes[s,'candidate'] and not outcomes[s,a] for s in range(85000,85032));losses=sum(outcomes[s,a] and not outcomes[s,'candidate'] for s in range(85000,85032));n=wins+losses
        p=sum(math.comb(n,k) for k in range(wins,n+1))/2**n if n else 1;comparisons.append(dict(control=a,wins=wins,losses=losses,p=p))
    passed=True
    for rank,c in enumerate(sorted(comparisons,key=lambda c:c['p'])):passed=passed and c['p']<=.05/(2-rank);c['holm_pass']=passed
    accepted=totals['candidate']['success']>=8 and totals['candidate']['exposed']>=24 and all(c['holm_pass'] for c in comparisons)
    return dict(verified=True,mode='panel',source_revision=revision,raw_start_worlds=96,attempts=393216,arms=totals,paired=comparisons,primary_pass=accepted,classification='PASS REQUIRES REPRODUCTION AND THROUGHPUT CONTROL' if accepted else 'UNDEREXPOSED' if totals['candidate']['exposed']<24 else 'FAIL',self_maintenance_demonstrated=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
    try:
        with open(a.input,encoding='utf-8') as f:data=json.load(f)
        print(json.dumps(audit(data,a.revision),sort_keys=True))
    except (AssertionError,ValueError,KeyError,IndexError,TypeError) as error:print(json.dumps(dict(verified=False,error=str(error))));raise SystemExit(2)
if __name__=='__main__':main()
