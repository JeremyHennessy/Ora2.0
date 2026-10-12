"""Independent real-latch/own-PC epoch reconstruction; no producer imports."""
import hashlib,json
from .digital_pc_controls31_audit import move

def copy(x):return json.loads(json.dumps(x))
def local(e):return dict(r=e['registers'][:],m=e['memory'][:],pc=e['pc'],feedback=e['feedback'])

def update(aux,e,event,mode,seed):
    op,a,b=event['decoded'];assert op in (1,2,3,4,5,6,7,8,18)
    aux['shadow']=move(aux['program'],aux['shadow'],0,True);native=local(e);result=copy(native);sub=None;rewrites=[];personal=None
    if op==1:
        aux['reads']+=1;index=aux['reads']
        if mode=='own_disrupted':
            encoded=json.dumps([seed//2,'own-disrupt31',index],sort_keys=True,separators=(',',':')).encode();value=int(hashlib.sha256(encoded).hexdigest()[:8],16)%2
            sub=dict(read_index=index,register=a%2,original=result['r'][a%2],value=value);result['r'][a%2]=value
        personal=dict(read_index=index,own_source_tick=aux['origin'],original=native['r'][a%2],value=result['r'][a%2])
    saved=copy(aux['shadow']) if op==6 else None
    if op==6:
        if mode=='retained_disabled':
            for key in ('r','m','pc'):
                if result[key]!=aux['shadow'][key]:rewrites.append(dict(channel=key,original=copy(result[key]),value=copy(aux['shadow'][key])))
                result[key]=copy(aux['shadow'][key])
        aux['epoch']+=1;aux['shadow']=copy(result);aux['origin']=event['tick'] if event.get('attempt') is not None else None
    assert result['feedback']==native['feedback']
    e['registers']=result['r'];e['memory']=result['m'];e['pc']=result['pc']
    return dict(mode=mode,epoch=aux['epoch'],read_count=aux['reads'],substitution=sub,rewrites=rewrites,shadow_at_action=saved,shadow=copy(aux['shadow']),personal_read=personal,latest_own_source_tick=aux['origin'])
