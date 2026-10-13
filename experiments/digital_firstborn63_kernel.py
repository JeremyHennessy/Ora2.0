"""Prepared Firstborn63 projection kernel; full VM audit is a separate prerequisite.

No producer, World, seed evaluation, source enrollment or scientific acceptance.
Inputs to these helpers must originate from independently audited full histories
before scientific use. Partial-table tests establish software semantics only.
"""
import hashlib,json

def clone(x):return json.loads(json.dumps(x))
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def normal_prefix(events):
    """Only declared copied values and derived hashes may be normalized."""
    result=[]
    for event in events:
        item=clone(event)
        item.pop('before',None);item.pop('state_hash',None)
        for write in item.get('writes',[]):
            write['value']=None;write['mutated']=None
        for write in item.get('after',{}).get('nursery',[]):
            write['value']=None;write['mutated']=None
        if 'birth' in item:
            for cell in item['birth']['child']['code']:cell[0]=None
        result.append(item)
    return result

def prefix_fingerprint(events):
    """Independent path-based comparison, retaining every undeclared leaf."""
    leaves=[]
    def visit(value,path):
        # Exact structural paths, never generic key-name stripping.
        if len(path)==2 and path[1] in ('before','state_hash'):return
        if len(path)==4 and path[1]=='writes' and path[3] in ('value','mutated'):
            value=None
        if len(path)==5 and path[1:3]==('after','nursery') and path[4] in ('value','mutated'):
            value=None
        if len(path)==6 and path[1:4]==('birth','child','code') and path[5]==0:
            value=None
        if isinstance(value,dict):
            leaves.append((path,'dict',tuple(sorted(value))))
            for key in sorted(value):visit(value[key],path+(key,))
        elif isinstance(value,list):
            leaves.append((path,'list',len(value)))
            for index,child in enumerate(value):visit(child,path+(index,))
        else:leaves.append((path,type(value).__name__,value))
    # Excluded hashes must not survive as dict-key metadata.
    for index,event in enumerate(events):
        selected={k:v for k,v in event.items() if k not in ('before','state_hash')}
        visit(selected,(index,))
    return leaves

def paired_prefix(faithful,mutating):
    """Event-level physical comparison after independent full audits of both arms.

    Birthless pairs compare their complete founder histories. Asymmetric birth,
    source-value/unit/runtime differences and non-exact faithful birth fail.
    This does not independently validate hashes, law, prices or genesis.
    """
    assert isinstance(faithful,list) and isinstance(mutating,list)
    def first(events):return next((i for i,e in enumerate(events) if 'birth' in e),None)
    left=first(faithful);right=first(mutating);assert left==right
    a=faithful if left is None else faithful[:left+1]
    b=mutating if right is None else mutating[:right+1]
    assert normal_prefix(a)==normal_prefix(b)
    assert prefix_fingerprint(a)==prefix_fingerprint(b)
    if left is None:return dict(birth_tick=None,changed=False)
    x=a[-1];y=b[-1];assert x['actor']==y['actor']==0
    child=x['birth']['child'];other=y['birth']['child']
    assert child['id']==other['id']==1 and child['parent']==other['parent']==0
    assert len(child['code'])==len(other['code'])==27
    # DIV cannot change the parental executable program. A dying parent has no
    # 'after'; recover its pre-DIV program from the prior independently audited
    # founder state, rather than accepting a supplied parent-genome annotation.
    parent=x.get('after')
    if parent is None:
        parent=next((e['after'] for e in reversed(a[:-1]) if 'after' in e),None)
    assert parent is not None
    assert [v[0] for v in child['code']]==[v[0] for v in parent['code']]
    assert not child['nursery'] and not other['nursery']
    if 'after' in x:assert not x['after']['nursery']
    if 'after' in y:assert not y['after']['nursery']
    return dict(birth_tick=x['tick'],changed=[v[0] for v in child['code']]!=[v[0] for v in other['code']])

def firstborn_window(events,final_tick,extinct):
    """Count actual firstborn actions and reconcile transfer-adjusted gain.

    Eight GLOBAL instructions; all later births are refused within this window.
    Earlier extinction is absorbing, never fabricated continuation. Generic VM
    audit and complete-panel integrity/ordinary admission remain separate.
    """
    assert type(final_tick) is int and 0<=final_tick<=512 and type(extinct) is bool
    birth=next((e for e in events if 'birth' in e),None)
    if birth is None:return dict(F=0,G=0,birth_tick=None,complete=True,alive=False,absent=True)
    b=birth['tick'];state=clone(birth['birth']['child'])
    assert state['id']==1 and state['parent']==0 and len(state['code'])==27
    assert state['energy']==12 and not state['nursery']
    food=[0]*4;real_failed=empty=steps=copy=incoming=outgoing=cap=halt=0
    alive=True;records=[]
    for event in events:
        tick=event['tick']
        if not b<tick<=b+8:continue
        assert 'birth' not in event
        if event.get('transfer')==1:
            assert alive;incoming+=1;state['energy']+=1
        if event.get('message',{}).get('recipient')==1:
            assert alive;state['inbox']=event['message']['value']
        if event['actor']!=1:continue
        assert alive and event['before']==digest(state)
        old=clone(state);steps+=1;opcode=event['decoded'][0]
        energy=old['energy']-1;attempt=event.get('attempt')
        if opcode==6:
            if attempt is None:empty+=1
            elif attempt['success']:
                food[attempt['position']]+=1
                loss=max(0,energy+20-64);cap+=loss;energy+=20-loss
            else:real_failed+=1
        paid=len(event.get('writes',[]));copy+=paid;energy-=paid
        if 'transfer' in event:outgoing+=1;energy-=1
        if opcode==17:halt+=energy;energy=0
        assert energy>=0
        if 'death' in event:
            assert energy==0 and 'after' not in event
            state['energy']=0;alive=False
        else:
            assert event['after']['energy']==energy;state=clone(event['after'])
        # A death event has no live 'after' body. Do not fabricate a post-step
        # PC/register/memory/code state from the pre-step body with energy zero.
        records.append(dict(tick=tick,before=event['before'],program_before=digest([v[0] for v in old['code']]),
                            program=digest([v[0] for v in state['code']]) if alive else None,
                            state=digest(state) if alive else None,memory=digest(state['memory']) if alive else None,
                            registers=digest(state['registers']) if alive else None,pc=state['pc'] if alive else None,
                            inbox=state['inbox'] if alive else None,alive=alive))
    if extinct and final_tick<b+8:assert not alive
    G=state['energy']-12-incoming+outgoing
    assert G==20*sum(food)-cap-steps-copy-halt
    return dict(F=sum(food),G=G,birth_tick=b,complete=b<=504 and (final_tick>=b+8 or extinct),alive=alive,absent=False,
                food_by_site=food,failed_real=real_failed,empty=empty,instructions=steps,paid_words=copy,
                incoming=incoming,outgoing=outgoing,cap_loss=cap,halt_heat=halt,endpoint_energy=state['energy'],records=records)

def literal_gain(events,birth_tick):
    """Second cost-ledger formula, independent of firstborn_window state reducer.

    Reconstruct just child's scalar energy through actual input/output transfers;
    reconcile the literal paid-operation bill against terminal-energy gain.
    """
    energy=12;gains=losses=received=sent=0;food=0
    for e in events:
        if not birth_tick<e['tick']<=birth_tick+8:continue
        assert 'birth' not in e
        if e.get('transfer')==1:energy+=1;received+=1
        if e['actor']!=1:continue
        energy-=1;losses+=1
        if e.get('attempt',{}).get('success'):
            food+=1;retained=min(20,64-energy);energy+=retained;gains+=retained
        charge=len(e.get('writes',[]));energy-=charge;losses+=charge
        if 'transfer' in e:energy-=1;sent+=1
        if e['decoded'][0]==17:losses+=energy;energy=0
        assert energy==(0 if 'death' in e else e['after']['energy'])
    assert energy-12-received+sent==gains-losses
    return dict(F=food,G=gains-losses)
