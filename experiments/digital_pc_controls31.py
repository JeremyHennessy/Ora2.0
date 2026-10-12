"""Prepared instruction fixtures for PC-inclusive external controls; no World."""
import hashlib,json

VERSION='DIGITAL-PC-CONTROLS-31-v1'
MODES=('intact','retained_disabled','own_disrupted')
OPS=(1,2,3,4,5,6,7,8,18)

def clone(x):return json.loads(json.dumps(x))
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def validate(code,state):
    if not 1<=len(code)<=32 or any(len(x)!=3 or any(type(v) is not int or not 0<=v<32 for v in x) or x[0] not in OPS for x in code):raise ValueError('Immutable conditional fixture scope only')
    if set(state)!=set(('r','m','pc','feedback')) or len(state['r'])!=2 or len(state['m'])!=8 or any(type(v) is not int or not 0<=v<16 for v in state['r']+state['m']) or type(state['pc']) is not int or not 0<=state['pc']<len(code) or type(state['feedback']) is not int or state['feedback'] not in (0,1):raise ValueError('Malformed fixture state')

def step(code,state,act_feedback=0,zero_feedback=False):
    validate(code,state)
    if type(act_feedback) is not int or act_feedback not in (0,1):raise ValueError('Prepared feedback must be bit')
    s=clone(state);op,a,b=code[s['pc']];s['pc']=(s['pc']+1)%len(code);r=s['r'];m=s['m']
    if op==1:r[a%2]=0 if zero_feedback else s['feedback']
    elif op==2:r[a%2]=m[b%8]
    elif op==3:m[a%8]=r[b%2]
    elif op==4:r[a%2]=b%16
    elif op==5:r[a%2]^=r[b%2]
    elif op==6:s['feedback']=act_feedback
    elif op==7:s['pc']=b%len(code)
    elif op==8 and r[a%2]==0:s['pc']=b%len(code)
    return s

class Control:
    def __init__(self,code,state,mode,seed):
        validate(code,state)
        if mode not in MODES or type(seed) is not int or seed<0:raise ValueError('Unregistered control configuration')
        self.code=clone(code);self.shadow=clone(state);self.mode=mode;self.seed=seed;self.reads=0;self.epoch=0

    def apply(self,before,after):
        validate(self.code,before);validate(self.code,after)
        op,a,b=self.code[before['pc']];self.shadow=step(self.code,self.shadow,zero_feedback=True)
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

PROGRAMS={
 'branch':[[1,0,0],[8,0,4],[4,1,7],[7,0,5],[4,1,2],[6,1,0],[7,0,0]],
 'memory':[[1,0,0],[3,2,0],[4,0,0],[6,0,0],[7,0,0]],
 'no_feedback':[[4,0,0],[8,0,3],[4,1,7],[6,0,0],[4,0,1],[8,0,0],[7,0,0]]}

def fixture(role,mode,initial_feedback,seed=31000,steps=32):
    if role not in PROGRAMS or type(steps) is not int or not 1<=steps<=64:raise ValueError('Prepared fixture only')
    state=dict(r=[0,0],m=[0]*8,pc=0,feedback=initial_feedback);code=clone(PROGRAMS[role]);control=Control(code,state,mode,seed);genesis=clone(state);events=[]
    for tick in range(1,steps+1):
        before=clone(state);decoded=code[state['pc']][:];prepared_feedback=tick%2
        native=step(code,state,prepared_feedback);state,annotation=control.apply(before,native)
        events.append(dict(tick=tick,before=before,decoded=decoded,prepared_feedback=prepared_feedback,native_after=native,after=clone(state),control=annotation))
    return dict(contract=VERSION,role=role,mode=mode,seed=seed,genesis=genesis,program=code,events=events,final=state,world=False,resource_accounting=False,learning=False)

def panel():return dict(contract=VERSION,fixtures=[fixture(role,mode,fb) for role in PROGRAMS for mode in MODES for fb in (0,1)],prepared_fixture_count=18,world_histories=0,actions=0,births=0,deaths=0,candidate_genomes_executed=0,learning=False,stage_credit=False)

if __name__=='__main__':print(json.dumps(panel(),sort_keys=True,separators=(',',':')))
