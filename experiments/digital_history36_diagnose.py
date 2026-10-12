"""Local first-effect diagnosis of sealed traces; no World or outcome prediction."""
import hashlib
import json

MODES=('intact','retained_disabled','own_disrupted')
OPS=(1,2,3,4,5,6,7,8,18)

def clone(x):return json.loads(json.dumps(x))
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def prepare(row):
    code=row['genesis_program'];es=row['final']['events'];mode=row['control_mode']
    if mode not in MODES or not 1<=len(code)<=32 or not 1<=len(es)<=512:raise ValueError('scope')
    if any(type(t) is not list or len(t)!=3 or any(type(v) is not int or not 0<=v<32 for v in t) or t[0] not in OPS for t in code):raise ValueError('code')
    state=dict(r=[0,0],m=[0]*8,pc=0,feedback=0);before=[];after=[];origin=None;wins=[]
    for i,e in enumerate(es):
        if type(e['tick']) is not int or e['tick']!=i+1 or type(e['actor']) is not int or e['actor']!=0 or e['decoded']!=code[state['pc']]:raise ValueError('trace')
        if 'death' in e and i!=len(es)-1:raise ValueError('post-death')
        before.append(clone(state));op,a,b=e['decoded'];state['pc']=(state['pc']+1)%len(code)
        if op==1:
            s=e['control']['personal_read']
            if s['own_source_tick']!=origin or origin is not None and type(s['own_source_tick']) is not int or type(s['original']) is not int or s['original']!=state['feedback'] or type(s['value']) is not int or s['value'] not in (0,1) or mode!='own_disrupted' and s['value']!=s['original']:raise ValueError('read')
            state['r'][a%2]=s['value']
        elif op==2:state['r'][a%2]=state['m'][b%8]
        elif op==3:state['m'][a%8]=state['r'][b%2]
        elif op==4:state['r'][a%2]=b%16
        elif op==5:state['r'][a%2]^=state['r'][b%2]
        elif op==6:
            state['feedback']=e['feedback'];attempt=e.get('attempt');origin=e['tick'] if attempt is not None else None
            if type(state['feedback']) is not int or state['feedback'] not in (0,1):raise ValueError('feedback')
            if attempt is not None:
                if attempt['port']!=state['r'][a%2]%2 or attempt['success']!=state['feedback']:raise ValueError('ACT')
                if attempt['success']==1:wins.append((attempt['packet'],e['tick']))
            elif state['feedback']!=0:raise ValueError('empty ACT')
            if mode=='retained_disabled':
                shadow=e['control']['shadow_at_action']
                for k in ('r','m','pc'):state[k]=clone(shadow[k])
        elif op==7:state['pc']=b%len(code)
        elif op==8 and state['r'][a%2]==0:state['pc']=b%len(code)
        if 'after' in e:
            recorded=e['after']
            if state!=dict(r=recorded['registers'],m=recorded['memory'],pc=recorded['pc'],feedback=recorded['feedback']):raise ValueError('local after')
        after.append(clone(state))
    if len({p for p,t in wins})!=len(wins):raise ValueError('duplicate food')
    completion=max(t for p,t in wins) if {p for p,t in wins}==set(range(32)) else None
    return before,after,completion

def new_read(e,mode,completion):
    s=e['control']['personal_read'];origin=s['own_source_tick'];tick=e['tick']
    return dict(read_tick=tick,origin_tick=origin,truth=s['original'],delivered=s['value'],
                source='unrelated' if mode=='own_disrupted' else ('own' if origin is not None else 'initial_or_empty'),
                post_change_own=mode!='own_disrupted' and origin is not None and origin>=64,
                read_before_completion=completion is None or tick<completion,
                first_effect='none',effect_tick=None,real_opportunity=False,effect_before_completion=False)

def finish(row,reads,completion):
    return dict(input_sha256=digest(row),completion_tick=completion,reads=reads,
                classification='local_first_effect_only',learning=False,stage_credit=False)

def diagnose(row):
    before,after,completion=prepare(row);es=row['final']['events'];code=row['genesis_program'];mode=row['control_mode']
    r=[set(),set()];m=[set() for _ in range(8)];reads=[];by={}
    for i,e in enumerate(es):
        op,a,b=e['decoded'];effects=set();kind=None
        if op==1:
            record=new_read(e,mode,completion);reads.append(record);by[e['tick']]=record;r[a%2]={e['tick']}
        elif op==2:r[a%2]=set(m[b%8])
        elif op==3:m[a%8]=set(r[b%2])
        elif op==4:r[a%2]=set()
        elif op==5:r[a%2]=r[a%2]^r[b%2]
        elif op==6:effects=set(r[a%2]);kind='ACT_port'
        elif op==8:
            value=before[i]['r'][a%2];pc=before[i]['pc']
            if ((value==0)!=((value^1)==0)) and b%len(code)!=(pc+1)%len(code):effects=set(r[a%2]);kind='JZ_successor'
        for tick in effects:
            record=by[tick];record.update(first_effect=kind,effect_tick=e['tick'],real_opportunity=kind=='ACT_port' and 'attempt' in e,effect_before_completion=completion is None or e['tick']<completion)
        if effects:
            r=[x-effects for x in r];m=[x-effects for x in m]
        if op==6 and mode=='retained_disabled':r=[set(),set()];m=[set() for _ in range(8)]
    return finish(row,reads,completion)

if __name__=='__main__':
    import sys
    with open(sys.argv[1],encoding='utf-8') as f:batch=json.load(f)
    print(json.dumps([dict(role=x['role'],diagnosis=diagnose(x['row'])) for x in batch['histories']],sort_keys=True,separators=(',',':')))
