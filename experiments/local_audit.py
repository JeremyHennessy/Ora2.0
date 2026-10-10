"""Independent ledger, acceptance interpreter and physical reachability audit."""
import argparse, hashlib, json, math, random, struct
from collections import deque
from fractions import Fraction

NAMES=('candidate','independent','shuffled')
def encoded(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def thermal(v):return 68-(6*v[0]+4*v[1]+2*v[2].bit_count()-v[3]+v[5])
def interpret(v,action,arm):
    kind,j,d=action;u=list(v)
    if kind in ('capture','decay','work'):
        source,target={'capture':(0,1),'decay':(1,2),'work':(1,2)}[kind]
        if d==-1:source,target=target,source
        numbers=[v[0],v[1],10-v[0]-v[1]]
        if numbers[source]==0:return None
        numbers[source]-=1;numbers[target]+=1;u[:2]=numbers[:2]
        if kind=='work':u[5]+=2*d
        factor={'candidate':[2,32],'independent':[17,17],'shuffled':[32,2]}[arm][v[3]] if kind=='work' else 4
    elif kind=='activate':
        if v[3] or ((v[2]>>j)&1)==int(d==1):return None
        u[2]^=1<<j;u[5]-=3*d;factor=16
    elif kind=='bond':
        if v[3]==int(d==1) or d==1 and (v[2]!=3 or v[4]%3!=0):return None
        u[3]=int(d==1);factor=16
    elif kind=='hop':u[4]^=3 if v[3] else 1<<j;factor=16
    else:raise ValueError('Unknown primitive')
    if min(u[0],u[1],10-u[0]-u[1],u[5],thermal(u))<0:return None
    rate=Fraction(factor,64)*Fraction(1,2**max(0,thermal(v)-thermal(u)))
    return tuple(u),rate

def physical(arm):
    roots={(10,0,0,0,x,0) for x in range(4)};known=set(roots);queue=deque(roots);count=0;checks=set()
    actions=[(k,0,d) for k in ('capture','decay','work') for d in (-1,1)]+[('activate',j,d) for j in range(2) for d in (-1,1)]+[('bond',0,d) for d in (-1,1)]+[('hop',j,1) for j in range(2)]
    def mult(v):return math.factorial(10)//(math.factorial(v[0])*math.factorial(v[1])*math.factorial(10-v[0]-v[1]))*2**thermal(v)
    while queue:
        v=queue.popleft()
        for a in actions:
            result=interpret(v,a,arm)
            if result is None:continue
            u,r=result;k,j,d=a;reverse=(k,j,1 if k=='hop' else -d);back,q=interpret(u,reverse,arm);assert back==v
            amounts=lambda x,di: [x[0],x[1],10-x[0]-x[1]][({'capture':(1,0),'decay':(2,1),'work':(2,1)}[k][di==1])] if k in ('capture','decay','work') else 10
            cf,cb=amounts(v,d),amounts(u,-d)
            signature=(v[0],v[1],u[0],u[1],thermal(u)-thermal(v),r,q,cf,cb)
            if signature not in checks:assert mult(v)*r*cf==mult(u)*q*cb;checks.add(signature)
            count+=1
            if u not in known:known.add(u);queue.append(u)
            if len(known)>250000 or count>4000000:raise ValueError('Independent graph cap')
    return dict(arm=arm,states=len(known),edges=count,state_sha256=hashlib.sha256(encoded(sorted(known))).hexdigest(),rate_signatures=len(checks),protected_heat_work_ceiling=max(v[5] for v in known if thermal(v)>=8))

def audit_world(record):
    arm=record['arm'];rng=random.Random(record['seed']);witness=record['witness']
    pos=0 if witness else rng.getrandbits(1)+2*rng.getrandbits(1)
    v=(10,0,0,0,pos,0);tokens=[0]*10;origins=[None]*10;virgin=[True]*10
    owners=[0,1];objects=[dict(id=j,atom=j,parent=None,state='raw') for j in range(2)];bonds=[]
    body=previous=rebuilt=loss=None;index=occupancy=fresh=thermalwork=0;digest=hashlib.sha256();states=[list(v)+[thermal(v)]]
    def event(action,step):
        nonlocal v,index,body,previous,rebuilt,loss,fresh,thermalwork
        k,j,d=action;before=v;e=dict(step=step,action=list(action),before=list(v),bond=body,origin=None)
        if k=='damage':
            assert step==2048 and v[3] and v[5]>=1
            v=(v[0],v[1],v[2]&~1,0,v[4],v[5]-1);loss=step;body=None
        else:
            v,r=interpret(v,action,arm);e['rate']=[r.numerator,r.denominator]
        if k in ('capture','decay','work'):
            source,target={'capture':(0,1),'decay':(1,2),'work':(1,2)}[k]
            if d==-1:source,target=target,source
            assert tokens[j]==source;tokens[j]=target
            if target==1:
                if k=='capture':origins[j]='fresh-fuel' if virgin[j] else 'thermal-reactivation';virgin[j]=False
                elif k=='decay':origins[j]='thermal-reactivation'
                else:origins[j]='paid-work-reactivation'
            if k=='work':
                e['origin']=origins[j] if d==1 else 'paid-work-reactivation'
                if d==1:fresh+=2*int(origins[j]=='fresh-fuel');thermalwork+=2*int(origins[j]=='thermal-reactivation')
            if target!=1:origins[j]=None
        elif k in ('activate','damage'):
            parent=owners[j];child=len(objects);owners[j]=child
            objects.append(dict(id=child,atom=j,parent=parent,state='active' if k=='activate' and d==1 else 'raw'));e.update(object=child,parent=parent)
        elif k=='bond':
            if d==1:
                body=len(bonds);bonds.append(dict(id=body,parent=previous,components=owners.copy()));previous=body
                if loss is not None and rebuilt is None:rebuilt=body
            else:body=None
            e['new_bond']=body
        e['after']=list(v);assert record['events'][index]==e;index+=1;states.append(list(v)+[thermal(v)])
    if witness:
        expected=[]
        for j in range(3):expected.extend([('capture',j,1),('work',j,1)])
        expected.extend([('activate',0,1),('activate',1,1),('bond',0,1),('capture',3,1),('work',3,1)])
        for step,a in enumerate(expected):event(a,step)
        event(('damage',0,1),2048)
        extra=[('capture',4,1),('work',4,1),('activate',0,1),('bond',0,1)]+[a for j in range(5,10) for a in [('capture',j,1),('work',j,1)]]
        for a in extra:event(a,2049+index)
    else:
        alphabet=[(k,j,d) for j in range(10) for k in ('capture','decay','work') for d in (-1,1)]+[('activate',j,d) for j in range(2) for d in (-1,1)]+[('bond',0,d) for d in (-1,1)]+[('hop',j,1) for j in range(2)]
        for step in range(4096):
            if step==2048 and v[3] and v[5]>=1:event(('damage',0,1),step)
            selected=rng.randrange(68);draw=rng.getrandbits(32);noise=rng.getrandbits(32);digest.update(struct.pack('<III',selected,draw,noise));a=alphabet[selected];k,j,d=a
            allowed=k not in ('capture','decay','work') or tokens[j]==({'capture':(1,0),'decay':(2,1),'work':(2,1)}[k][d==1])
            result=interpret(v,a,arm) if allowed else None
            if result is not None and Fraction(draw,2**32)<result[1]:event(a,step)
            occupancy+=v[3]
    assert index==len(record['events']) and record['states']==states
    for key,value in dict(objects=objects,owners=owners,bonds=bonds,current_bond=body,first_rebuilt=rebuilt,damage_step=loss,token_states=tokens,token_origin=origins,virgin_tokens=virgin,fresh_gross_work=fresh,thermal_gross_work=thermalwork,bound_occupancy=occupancy,draw_sha256=digest.hexdigest(),rng_sha256=hashlib.sha256(encoded(rng.getstate())).hexdigest()).items():assert record[key]==value,key
    cost=aftercost=linked=afterlinked=0;pre=False;used=False;before=None
    for e in record['events']:
        k,j,d=e['action'];bill=3*d if k=='activate' else int(k=='damage');cost+=bill
        if loss is not None and e['step']>=2048:aftercost+=bill
        if k=='work' and e['bond'] is not None and (e['origin']=='fresh-fuel' or d==-1):
            linked+=2*d
            if e['step']<2048 and d==1:pre=True
            if loss is not None and e['step']>=2048:
                afterlinked+=2*d
                if d==1 and e['bond']==rebuilt:used=True
        if k=='damage':before=e['before'][5]
    w=v[5];post=None if before is None else w-before;exposed=loss is not None and pre
    endpoint=exposed and rebuilt is not None and body==rebuilt and used and w>0 and post>0 and linked-cost>0 and afterlinked-aftercost>0 and thermal(v)>=8
    scored=dict(endpoint=bool(endpoint),functioning_loss=exposed,whole_work_surplus=w,post_work_surplus=post,bond_fresh_net_work=linked,post_bond_fresh_net_work=afterlinked,all_paid_net_cost=cost,post_paid_net_cost=aftercost,functional_surplus=linked-cost,post_functional_surplus=afterlinked-aftercost)
    assert scored==record['score'];return scored

def audit(data,revision):
    assert data['source_revision']==revision and data['schema']=='local01'
    records=data['records'];mode=data['mode']
    keys={(r['seed'],r['arm']) for r in records}
    expected={(0,a) for a in NAMES} if mode=='gate' else {(s,a) for s in range(84000,84032) for a in NAMES}
    assert keys==expected and len(records)==len(expected) and all(r['witness']==(mode=='gate') for r in records)
    for r in records:audit_world(r)
    if mode=='gate':
        graphs=[physical(a) for a in NAMES];assert graphs==data['graphs'];assert all(r['score']['endpoint'] for r in records)
        return dict(verified=True,mode=mode,mechanism_admitted=True,controlled_certificates=3,natural_worlds=0,graphs=graphs,source_revision=revision,self_maintenance_demonstrated=False)
    totals={a:dict(success=sum(r['score']['endpoint'] for r in records if r['arm']==a),exposed=sum(r['score']['functioning_loss'] for r in records if r['arm']==a),net_work=sum(r['score']['whole_work_surplus'] for r in records if r['arm']==a),functional_surplus=sum(r['score']['functional_surplus'] for r in records if r['arm']==a),paid_renewals=sum(r['first_rebuilt'] is not None for r in records if r['arm']==a),fuel_exhausted=sum(r['token_states'].count(0)==0 for r in records if r['arm']==a),thermal_gross_work=sum(r['thermal_gross_work'] for r in records if r['arm']==a),bound_attempts=sum(r['bound_occupancy'] for r in records if r['arm']==a)) for a in NAMES}
    outcomes={(r['seed'],r['arm']):r['score']['endpoint'] for r in records};comparisons=[]
    for a in NAMES[1:]:
        wins=sum(outcomes[s,'candidate'] and not outcomes[s,a] for s in range(84000,84032));losses=sum(outcomes[s,a] and not outcomes[s,'candidate'] for s in range(84000,84032));n=wins+losses
        p=sum(math.comb(n,k) for k in range(wins,n+1))/2**n if n else 1
        comparisons.append(dict(control=a,wins=wins,losses=losses,p=p))
    running=True
    for rank,c in enumerate(sorted(comparisons,key=lambda c:c['p'])):running=running and c['p']<=.05/(2-rank);c['holm_pass']=running
    accepted=totals['candidate']['success']>=8 and totals['candidate']['exposed']>=24 and all(c['holm_pass'] for c in comparisons)
    return dict(verified=True,mode=mode,source_revision=revision,raw_start_worlds=96,attempts=393216,arms=totals,paired=comparisons,primary_pass=accepted,classification='PASS REQUIRES REPRODUCTION' if accepted else 'UNDEREXPOSED' if totals['candidate']['exposed']<24 else 'FAIL',self_maintenance_demonstrated=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
    try:
        with open(a.input,encoding='utf-8') as f:data=json.load(f)
        print(json.dumps(audit(data,a.revision),sort_keys=True))
    except (AssertionError,ValueError,KeyError,IndexError,TypeError) as error:print(json.dumps(dict(verified=False,error=str(error))));raise SystemExit(2)
if __name__=='__main__':main()
