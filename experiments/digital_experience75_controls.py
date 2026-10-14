"""Prepared instruction fixtures for PC-inclusive external controls; no World."""
import hashlib,json

VERSION='DIGITAL-EXPERIENCE75-CONTROLS-v1'
MODES=('intact','retained_disabled','own_disrupted')
OPS=(0,1,2,3,4,5,6,7,8,18,19,20)

def clone(x):return json.loads(json.dumps(x))
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def validate(code,state):
    if not 1<=len(code)<=32 or any(len(x)!=3 or any(type(v) is not int or not 0<=v<32 for v in x) or x[0] not in OPS for x in code):raise ValueError('Immutable conditional fixture scope only')
    if set(state)!=set(('r','m','pc','feedback')) or len(state['r'])!=2 or len(state['m'])!=8 or any(type(v) is not int or not 0<=v<16 for v in state['r']+state['m']) or type(state['pc']) is not int or not 0<=state['pc']<len(code) or type(state['feedback']) is not int or state['feedback'] not in (0,1):raise ValueError('Malformed fixture state')

def step(code,state,act_feedback=0,zero_feedback=False,current_cue=0):
    validate(code,state)
    if type(act_feedback) is not int or act_feedback not in (0,1):raise ValueError('Prepared feedback must be bit')
    s=clone(state);op,a,b=code[s['pc']];s['pc']=(s['pc']+1)%len(code);r=s['r'];m=s['m']
    if type(current_cue) is not int or current_cue not in (0,1):raise ValueError('Prepared cue bit')
    if op==0:r[a%2]=current_cue
    elif op==1:r[a%2]=0 if zero_feedback else s['feedback']
    elif op==2:r[a%2]=m[b%8]
    elif op==3:m[a%8]=r[b%2]
    elif op==4:r[a%2]=b%16
    elif op==5:r[a%2]^=r[b%2]
    elif op==6:s['feedback']=act_feedback
    elif op==7:s['pc']=b%len(code)
    elif op==8 and r[a%2]==0:s['pc']=b%len(code)
    elif op==19:r[a%2]=m[r[b%2]%8]
    elif op==20:m[r[a%2]%8]=r[b%2]
    return s

class Control:
    def __init__(self,code,state,mode,seed):
        validate(code,state)
        if mode not in MODES or type(seed) is not int or seed<0:raise ValueError('Unregistered control configuration')
        self.code=clone(code);self.shadow=clone(state);self.mode=mode;self.seed=seed;self.reads=0;self.epoch=0

    def apply(self,before,after,current_cue=0):
        validate(self.code,before);validate(self.code,after)
        op,a,b=self.code[before['pc']];self.shadow=step(self.code,self.shadow,zero_feedback=True,current_cue=current_cue)
        result=clone(after);sub=None;rewrites=[]
        if op==1:
            self.reads+=1
            if self.mode=='own_disrupted':
                value=int(digest([self.seed//2,'own-disrupt31',self.reads])[:8],16)%2
                sub=dict(read_index=self.reads,register=a%2,original=result['r'][a%2],value=value)
                result['r'][a%2]=value
        shadow_at_action=clone(self.shadow) if op==6 else None
        if op==6:
            if self.mode=='retained_disabled':
                for key in ('r','m','pc'):
                    if result[key]!=self.shadow[key]:
                        rewrites.append(dict(channel=key,original=clone(result[key]),value=clone(self.shadow[key])))
                    result[key]=clone(self.shadow[key])
            # Truthful latest latch is sensing, not erased or replaced.
            assert result['feedback']==after['feedback']
            self.epoch+=1;self.shadow=clone(result)
        return result,dict(mode=self.mode,epoch=self.epoch,read_count=self.reads,substitution=sub,rewrites=rewrites,shadow_at_action=shadow_at_action,shadow=clone(self.shadow))
