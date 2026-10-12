"""Independent operator reconstruction; no producer imports."""
import hashlib,json

def update(aux,e,event,mode,seed):
    op,a,b=event['decoded'];assert op in (1,2,3,4,5,6,7,18)
    sr,sm,rt,mt=aux['r'],aux['m'],aux['rt'],aux['mt'];sample=None;changes=[]
    if op==1:
        aux['reads']+=1;n=aux['reads'];old=e['registers'][a%2]
        if mode=='own_disrupted':
            encoded=json.dumps([seed//2,'own-disrupt27',n],sort_keys=True,separators=(',',':')).encode()
            value=int(hashlib.sha256(encoded).hexdigest()[:8],16)%2;origins={-n}
        else:value=old;origins=set() if aux['origin'] is None else {aux['origin']}
        e['registers'][a%2]=value;sr[a%2]=0;rt[a%2]=origins
        sample=dict(register=a%2,original=old,value=value,own_source_tick=aux['origin'],read_index=n)
    if op==2:sr[a%2]=sm[b%8];rt[a%2]=mt[b%8].copy()
    if op==3:sm[a%8]=sr[b%2];mt[a%8]=rt[b%2].copy()
    if op==4:sr[a%2]=b%16;rt[a%2]=set()
    if op==5:
        sr[a%2]=sr[a%2]^sr[b%2];rt[a%2]=rt[a%2].union(rt[b%2])
    if op==6:
        aux['origin']=event['tick'] if event.get('attempt') is not None else None
        if mode=='retained_disabled':
            for name,actual,shadow,tags in [('register',e['registers'],sr,rt),('memory',e['memory'],sm,mt)]:
                for i in range(len(tags)):
                    if len(tags[i])>0:
                        changes.append(dict(channel=name,index=i,original=actual[i],value=shadow[i],origins=sorted(tags[i])))
                        actual[i]=shadow[i];tags[i]=set()
    return dict(mode=mode,source_tick=aux['origin'],read_count=aux['reads'],shadow_registers=sr.copy(),shadow_memory=sm.copy(),register_tags=[sorted(x) for x in rt],memory_tags=[sorted(x) for x in mt],substitution=sample,rewrites=changes)
