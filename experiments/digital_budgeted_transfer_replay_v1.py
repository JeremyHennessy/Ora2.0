"""Independent scalar interpreter/resource replay. Imports no producer or VM code.

Single-actor, immutable-program, unit-price opcode subset only. No primary launcher.
"""
import hashlib
import json

def clone(v):
    return json.loads(json.dumps(v))

def digest(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def replay(code, mask, order, mode, budget, limit=None):
    if mode not in ("intact", "memory_disabled", "history_disrupted"):
        raise ValueError("control")
    if (type(code) is not list or not 1<=len(code)<=32 or
        any(type(t) is not list or len(t)!=3 or
            any(type(v) is not int or not 0<=v<32 for v in t) for t in code)):
        raise ValueError("programme shape")
    if code[0][0]!=7 or code[0][2]>=len(code):raise ValueError("header")
    for op,a,b in code:
        if op==24 and (a>1 or b>15):raise ValueError("XORI bounds")
        if op==25 and (a>7 or b>=len(code)):raise ValueError("JBIT bounds")
    if type(mask) is not int or type(budget) is not int:raise ValueError("integer types")
    if type(order) is not tuple or len(order)!=8 or any(type(x) is not int for x in order):raise ValueError("order shape")
    q = code[0][1]
    if q not in (2,4,8) or len(code)>32 or not 0<=mask<16 or not 0<=budget<=328:
        raise ValueError("bounds")
    if sorted(order[:4]) != list(range(4)) or sorted(order[4:]) != list(range(4,8)):
        raise ValueError("request order")
    formation=3*len(code)+q+8
    if formation>budget: raise ValueError("formation")
    if any(t[0] not in (0,1,2,3,4,5,6,7,8,19,20,24,25) for t in code):
        raise ValueError("opcode")
    n=3*len(code)
    e=dict(id=0,parent=None,generation=0,lineage=[],code=[[v,i] for i,v in enumerate(sum(code,[]))],
           state_units=list(range(n,formation)),memory=[0]*q,registers=[0,0],pc=0,feedback=0,
           cue=0,pos=0,energy=200,nursery=[],pending=None,lease=None,turns=0,copy_sessions=0,children=0)
    w=dict(seed=2100790,mode="no_variation",max_population=1,expansion_tick=0,tick=0,last=-1,next_id=1,
           writes=0,births=0,deaths=0,offered=0,admitted=0,rejected=0,next_packet=64,
           heat=formation,constructor_remaining=328-formation-200,
           food={i:i%8 for i in range(64)},leases={},free=list(range(formation,512)),entities={0:e})
    events=[];rows=[];count=0;cost=formation;refused=False
    def packet():
        if e['lease'] is not None: return e['lease']
        candidates=[p for p in w['food'] if p not in w['leases'] and (not 16<=p<32 or w['tick']>=64)]
        return min(candidates) if candidates else None
    while count<8 and w['entities'] and w['tick']<2048 and cost<budget:
        if limit is not None and w['tick']>=limit: break
        pc=e['pc'];op,a,b=code[pc]
        required=1+(4 if op==6 else 0)+(16 if w['tick']+1==64 else 0)
        if cost+required>budget: refused=True;break
        cue=order[count];before=clone(e);w['tick']+=1;w['last']=0;e['turns']+=1
        event=dict(tick=w['tick'],actor=0,before=digest(e),energy_before=e['energy'],input=[])
        if w['tick']%64==0:
            for i in range(16):
                p=w['next_packet'];w['next_packet']+=1;w['offered']+=1
                resource_cue=(i+w['tick']//64)%8;ok=len(w['food'])<64
                if ok: w['food'][p]=resource_cue;w['admitted']+=1
                else: w['rejected']+=1
                event['input'].append(dict(packet=p,cue=resource_cue,energy=20,outcome='admitted' if ok else 'external_rejected'))
        if w['tick']==64:
            w['constructor_remaining']-=16;w['heat']+=16;event['release_energy']=16
        p=packet();e['energy']-=1;w['heat']+=1;e['pc']=(pc+1)%len(code)
        event.update(kind='ordinary',decoded=[op,a,b]);regs=e['registers'];mem=e['memory']
        if op==0:
            if p is not None:e['lease']=p;w['leases'][p]=0
            e['cue']=0 if p is None else w['food'][p];regs[a%2]=e['cue']
            event['sense']=dict(packet=p,cue=e['cue'])
        elif op==1:regs[a%2]=e['feedback'];event['read_feedback']=e['feedback']
        elif op==2:regs[a%2]=mem[b%q]
        elif op==3:mem[a%q]=regs[b%2]
        elif op==4:regs[a%2]=b%16
        elif op==5:regs[a%2]^=regs[b%2]
        elif op==6:
            e['feedback']=2;event['penalty']=0
            if p is not None:
                rc=w['food'].pop(p);target=((mask//(2**(cue%4)))%2+cue//4)%2
                action=regs[a%2]%2;e['feedback']=int(action==target)
                if p in w['leases']:del w['leases'][p];e['lease']=None
                event['attempt']=dict(packet=p,cue=rc,target=target,port=action,success=e['feedback'])
                if e['feedback']:
                    gain=min(20,224-e['energy']);e['energy']+=gain;w['heat']+=20-gain;event['captured']=gain
                else:
                    penalty=min(4,e['energy']);e['energy']-=penalty;w['heat']+=20+penalty;event['penalty']=penalty
            event['feedback']=e['feedback']
        elif op==7:e['pc']=b%len(code)
        elif op==8:
            if regs[a%2]==0:e['pc']=b%len(code)
        elif op==19:regs[a%2]=mem[regs[b%2]%q]
        elif op==20:mem[regs[a%2]%q]=regs[b%2]
        elif op in (24,25):
            if op==24:regs[a]^=b
            elif (regs[a%2]//(2**(a//2)))%2:e['pc']=b
            event['packed']=dict(version='CONTEXT90-PACKED-ACCESS-v2',decoded=[op,a,b],cpu=1,logic_fee=0,
                                 actor_cost=1,required=1,completed=True,read=None,write=None)
            event['logic_fee']=0
        else:raise ValueError('opcode')
        if e['energy']==0 or e['turns']==2048:
            units=[v[1] for v in e['code']]+e['state_units']
            if e['lease'] is not None:del w['leases'][e['lease']]
            w['heat']+=e['energy'];w['free']=sorted(w['free']+units);w['entities']={};w['deaths']+=1
            event['death']=dict(cause='energy' if e['energy']==0 else 'installed_age_law',released=units,dissipated=e['energy'])
        after=bool(w['entities']);intervention=None
        if op==0 and after:
            e['cue']=cue;regs[a%2]=cue;event['sense']['request_cue']=cue
        if mode=='history_disrupted' and op==1 and after:
            regs[a%2]=0;intervention=dict(channel='OBS',physical=event['read_feedback'],delivered=0)
        if mode=='memory_disabled' and after:
            if op in (2,19):regs[a%2]=0
            if op in (3,20):e['memory']=before['memory']
            if op in (2,3,19,20):intervention=dict(channel='memory',persistence=False)
        response=None;request=count
        if op==6 and 'attempt' in event:
            response=dict(request=count,cue=cue,packet=p,action=event['attempt']['port'],correct=bool(e['feedback']),phase='acquisition' if count<4 else 'transfer')
            count+=1
        if after:event['after']=clone(e)
        # Reconstruct every persistent resource field and event; do not trust
        # producer hashes, cost totals, state, labels, PC or terminal reason.
        event['state_hash']=digest(clone(w));events.append(event)
        charged=1+event.get('penalty',0)+event.get('release_energy',0);cost+=charged
        rows.append(dict(tick=w['tick'],pc=pc,request=request,cue=cue,response=response,charged=charged,cost=cost,intervention=intervention))
        assert sum(x['energy'] for x in w['entities'].values())+w['constructor_remaining']+w['heat']+20*len(w['food'])==1608+20*w['admitted']
    reason=('responses' if count==8 else 'death' if not w['entities'] else 'horizon' if w['tick']>=2048 else 'budget' if cost>=budget or refused else None)
    responses=[x['response'] for x in rows if x['response'] is not None]
    planned=[next((x for x in responses if x['request']==i),dict(request=i,cue=order[i],delivered=False,correct=None,reason=reason)) for i in range(8)]
    result=dict(version='BUDGETED-FIRST-RESPONSE-SOFTWARE-v1',software_only=True,completed=count,cost=cost,unused=budget-cost,stop=reason,planned=planned,ticks=w['tick'],transfer_correct=sum(x.get('correct') is True for x in planned[4:]))
    w['events']=events
    return dict(world=clone(w),rows=rows,result=result,budget_refused=refused)

def verify(code, mask, order, mode, budget, rows, result, world):
    expected=replay(code,mask,order,mode,budget)
    if (digest(clone(rows))!=digest(expected['rows']) or digest(clone(result))!=digest(expected['result']) or digest(clone(world))!=digest(expected['world'])):
        raise ValueError('independent VM/resource replay mismatch')
    return True
