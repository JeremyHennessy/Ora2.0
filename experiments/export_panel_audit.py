"""Independent labelled-event, rejected-draw and ancestry interpreter."""
import argparse,hashlib,json,math,random,struct
from fractions import Fraction
from .export_audit import NAMES,moves,thermal,canonical

def audit_world(record):
    arm=record['arm'];rng=random.Random(record['seed'])
    bits=rng.getrandbits(1)+2*rng.getrandbits(1)
    loc=[rng.getrandbits(1) for _ in range(10)]
    fuel=[True]*10;unused=[True]*10;work=[0]*10;origins=[None]*10
    form=0;origin=None;identity=previous=first=lost=None
    components=[dict(id=i,atom=i,parent=None,state='raw') for i in range(2)]
    owners=[0,1];bodies=[];cursor=occupied=fresh=other=0
    converted=afterconverted=bill=afterbill=0;priorfunction=afterfunction=False
    lossheat=losswork=None;digest=hashlib.sha256()
    def state():
        groups=[sum(site==i%2 and w==(2 if i>=2 else 0) for site,w in zip(loc,work)) for i in range(4)]
        return (sum(fuel),form,bits,*groups)
    history=[list(state())+[thermal(state())]]
    def allowed(action):
        kind,label,sign=action
        if kind in ('assemble','drive','waste') and fuel[label]!=(sign==1):return None
        if kind=='load' and work[label]!=(0 if sign==1 else 2):return None
        group=loc[label]+int(bool(work[label]))*2 if kind=='lhop' else loc[label] if kind=='load' else label if kind=='hop' else 0
        return next(moves(state(),arm,(kind,group,sign)),None)
    def consume(action,step,result=None):
        nonlocal form,bits,origin,identity,previous,first,lost,cursor,fresh,other,converted,afterconverted,bill,afterbill,priorfunction,afterfunction,lossheat,losswork
        kind,label,sign=action;before=state()
        item=dict(step=step,action=list(action),before=list(before),dimer=identity,origin=None)
        payment=6*sign if kind=='assemble' else sign if kind=='passive' else 2 if kind=='damage' else 0
        if kind=='damage':
            assert step==2048 and form and work[label]==2 and loc[label]==bits//3
            lossheat=thermal(before);losswork=sum(work);work[label]=0;origins[label]=None;form=0;origin=None;lost=step;item['target_atom']=0
        else:
            _,destination,_,rate=result
            item['rate']=[rate.numerator,rate.denominator];form,bits=destination[1:3]
            if kind in ('assemble','drive','waste'):
                if kind=='drive':origin=('fresh-fuel' if unused[label] else 'regenerated-fuel') if sign==1 else None
                fuel[label]=sign==-1;unused[label]=False
            if kind=='load':
                item['origin']=origin if sign==1 else 'paid-load-reversal'
                credit=2*sign if sign==-1 or origin=='fresh-fuel' else 0
                converted+=credit
                if lost is not None:afterconverted+=credit
                work[label]=2 if sign==1 else 0;origins[label]=origin if sign==1 else None
                if sign==1:
                    fresh+=2*int(origin=='fresh-fuel');other+=2*int(origin!='fresh-fuel')
                    priorfunction=priorfunction or step<2048 and origin=='fresh-fuel'
                    afterfunction=afterfunction or lost is not None and identity==first and origin=='fresh-fuel'
                origin=None if sign==1 else 'paid-load-reversal'
            if kind=='lhop':loc[label]=1-loc[label]
            assert state()==destination
        bill+=payment
        if lost is not None:afterbill+=payment
        if kind in ('assemble','passive','damage'):
            children=[]
            for atom,parent in enumerate(owners.copy()):
                child=len(components);components.append(dict(id=child,atom=atom,parent=parent,state='bound' if form else 'raw'));owners[atom]=child;children.append(child)
            item['objects']=children
            if form:
                identity=len(bodies);bodies.append(dict(id=identity,parent=previous,components=owners.copy()));previous=identity
                if lost is not None and first is None:first=identity
            else:identity=None
            origin=None;item['new_dimer']=identity
        now=state();item['after']=list(now)
        assert record['events'][cursor]==item
        cursor+=1;history.append(list(now)+[thermal(now)])
        assert thermal(now)>=0 and 6*sum(fuel)+(0,1,4,3)[form]+sum(work)+thermal(now)==68
    # Different slot decoding rather than importing the producer's alphabet.
    def decode(slot):
        if slot<60:
            label,remainder=divmod(slot,6)
            return (('assemble','drive','waste')[remainder//2],label,-1 if remainder%2==0 else 1)
        if slot<64:
            v=slot-60
            return (('passive','relax')[v//2],0,-1 if v%2==0 else 1)
        if slot<84:
            label,parity=divmod(slot-64,2)
            return ('load',label,-1 if parity==0 else 1)
        if slot<94:return ('lhop',slot-84,1)
        return ('hop',slot-94,1)
    for step in range(4096):
        if step==2048 and form:
            payment=next((i for i in range(10) if work[i]==2 and loc[i]==bits//3),None)
            if payment is not None:consume(('damage',payment,1),step)
        slot=rng.randrange(96);draw=rng.getrandbits(32);noise=rng.getrandbits(32)
        digest.update(struct.pack('<III',slot,draw,noise));action=decode(slot);candidate=allowed(action)
        if candidate is not None and Fraction(draw,2**32)<candidate[3]:consume(action,step,candidate)
        occupied+=int(form!=0)
    assert len(record['events'])==cursor and record['states']==history
    expected=dict(objects=components,owners=owners,dimers=bodies,current_dimer=identity,first_rebuilt=first,damage_step=lost,token_states=[int(not v) for v in fuel],virgin_tokens=unused,charge_origin=origin,load_sites=loc,loaded=[bool(v) for v in work],load_origins=origins,fresh_gross_work=fresh,other_gross_work=other,bound_occupancy=occupied,draw_sha256=digest.hexdigest(),rng_sha256=hashlib.sha256(canonical(rng.getstate())).hexdigest())
    for key,value in expected.items():assert record[key]==value,key
    stored=sum(work);post=None if lost is None else stored-losswork;exposure=lost is not None and priorfunction
    endpoint=exposure and first is not None and first==identity and afterfunction and min(stored,post,converted-bill,afterconverted-afterbill)>0 and thermal(state())>=max(8,lossheat)
    scored=dict(endpoint=bool(endpoint),functioning_loss=exposure,whole_work_surplus=stored,post_work_surplus=post,fresh_net_output=converted,post_fresh_net_output=afterconverted,all_net_formation_damage_cost=bill,post_net_cost=afterbill,functional_surplus=converted-bill,post_functional_surplus=afterconverted-afterbill,initial_heat_preserved=thermal(state())>=8,post_heat_preserved=lossheat is not None and thermal(state())>=lossheat,first_rebuilt_fresh_use=bool(afterfunction))
    assert scored==record['score']
    return scored

def audit(data,revision):
    assert data['schema']=='export01-panel' and data['source_revision']==revision
    records=data['records'];expected={(s,a) for s in range(86000,86032) for a in NAMES}
    assert len(records)==128 and {(r['seed'],r['arm']) for r in records}==expected
    for record in records:audit_world(record)
    totals={}
    for arm in NAMES:
        rows=[r for r in records if r['arm']==arm]
        totals[arm]=dict(success=sum(r['score']['endpoint'] for r in rows),exposed=sum(r['score']['functioning_loss'] for r in rows),actual_paid_losses=sum(r['damage_step'] is not None for r in rows),first_rebuilds=sum(r['first_rebuilt'] is not None for r in rows),first_rebuild_fresh_uses=sum(r['score']['first_rebuilt_fresh_use'] for r in rows),retained_first_rebuilds=sum(r['first_rebuilt'] is not None and r['first_rebuilt']==r['current_dimer'] for r in rows),stored_work=sum(r['score']['whole_work_surplus'] for r in rows),linked_surplus=sum(r['score']['functional_surplus'] for r in rows),fresh_gross_work=sum(r['fresh_gross_work'] for r in rows),other_gross_work=sum(r['other_gross_work'] for r in rows),all_reverse_output=sum(2 for r in rows for e in r['events'] if e['action'][0]=='load' and e['action'][2]==-1),fuel_exhausted=sum(r['token_states'].count(0)==0 for r in rows),bound_attempts=sum(r['bound_occupancy'] for r in rows),phase_untouched_tokens=sum(sum(j not in {e['action'][1] for e in r['events'] if e['step']<2048 and e['action'][0] in ('assemble','drive','waste')} for j in range(10)) for r in rows if r['damage_step'] is not None))
    outcomes={(r['seed'],r['arm']):r['score']['endpoint'] for r in records};paired=[]
    for arm in NAMES[1:3]:
        wins=sum(outcomes[s,'candidate'] and not outcomes[s,arm] for s in range(86000,86032));losses=sum(outcomes[s,arm] and not outcomes[s,'candidate'] for s in range(86000,86032));n=wins+losses
        p=sum(math.comb(n,k) for k in range(wins,n+1))/2**n if n else 1
        paired.append(dict(control=arm,wins=wins,losses=losses,p=p))
    passed=True
    for rank,result in enumerate(sorted(paired,key=lambda v:v['p'])):
        passed=passed and result['p']<=.05/(2-rank);result['holm_pass']=passed
    positive=totals['candidate']['success']>=8 and totals['candidate']['exposed']>=24 and all(v['holm_pass'] for v in paired)
    return dict(verified=True,schema='export01-panel-decision',source_revision=revision,raw_start_worlds=128,primary_worlds=96,diagnostic_worlds=32,attempts=524288,arms=totals,paired=paired,primary_pass=positive,classification='PASS REQUIRES REPRODUCTION AND THROUGHPUT CONTROL' if positive else 'UNDEREXPOSED' if totals['candidate']['exposed']<24 else 'FAIL',self_maintenance_demonstrated=False,export_causal_advantage_demonstrated=False,reserved_samples_executed=False,next_decision='Independent reserved reproduction and throughput-matched controls required' if positive else 'Close exact law/endowment/horizon without tuning; inspect paid loss and retention bottlenecks before registering a genuinely different mechanism.')

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--revision',required=True);p.add_argument('--single-world',action='store_true');a=p.parse_args()
    try:
        with open(a.input,encoding='utf-8') as stream:data=json.load(stream)
        result=dict(verified=True,score=audit_world(data)) if a.single_world else audit(data,a.revision)
        print(json.dumps(result,sort_keys=True))
    except (AssertionError,ValueError,KeyError,IndexError,TypeError,StopIteration) as error:
        print(json.dumps(dict(verified=False,error=str(error))));raise SystemExit(2)

if __name__=='__main__':main()
