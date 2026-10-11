"""Structural feedback reachability preflight; NOT a population/world simulator.

The probe abstracts away resources and reproduction, so a reachable action is
not a viable, profitable, learned or organism-developed behavior. See protocol.
"""
import json

ANCESTOR = (4,1,1,6,0,0,5,0,1,10,0,0,12,0,0,7,0,1)
LIMIT = 64

def probe(program, feedback, previous_port, entry=2):
    assert len(program)%3 == 0 and all(type(x) is int and 0<=x<32 for x in program)
    assert type(feedback) is int and feedback in (0,1)
    assert type(previous_port) is int and previous_port in (0,1)
    code=list(program); n=len(code)//3
    assert type(entry) is int and 0<=entry<n
    registers=[previous_port,1]; memory=[0]*8; pc=entry; position=0; reads=0
    for step in range(1,LIMIT+1):
        op,a,b=code[3*pc:3*pc+3]; pc=(pc+1)%n
        if op==0: registers[a%2]=position
        elif op==1: registers[a%2]=feedback; reads+=1
        elif op==2: registers[a%2]=memory[b%8]
        elif op==3: memory[a%8]=registers[b%2]
        elif op==4: registers[a%2]=b%16
        elif op==5: registers[a%2]^=registers[b%2]
        elif op==6: return dict(status='action',port=registers[a%2]%2,steps=step,feedback_reads=reads)
        elif op==7: pc=b%n
        elif op==8:
            if registers[a%2]==0: pc=b%n
        elif op==9: code[b%len(code)]=registers[a%2]
        elif op==11: pc=b%n  # empty nursery: copy-incomplete condition true
        elif op==13: position=(position+(1 if registers[a%2]%2 else -1))%4
        elif op==17: return dict(status='halt',port=None,steps=step,feedback_reads=reads)
        # COPY/DIVIDE have no control-flow effect. All resource/body effects
        # are deliberately abstracted away. No peers/messages/transfer occur.
    return dict(status='bounded_no_action',port=None,steps=LIMIT,feedback_reads=reads)

def evaluate(program, entry=2):
    rows=[probe(program,f,p,entry) for p in (0,1) for f in (0,1)]
    pairs=[rows[0:2],rows[2:4]]
    depends=any(a['status']==b['status']=='action' and a['port']!=b['port'] for a,b in pairs)
    return dict(probes=rows,feedback_action_dependence=depends,
                retains_copy_divide=10 in program[::3] and 12 in program[::3])

def study():
    rows=[]
    for address,old in enumerate(ANCESTOR):
        for value in range(32):
            if value==old: continue
            code=list(ANCESTOR);code[address]=value
            rows.append(dict(address=address,old=old,value=value,**evaluate(code)))
    positive=evaluate([1,0,0,6,0,0,7,0,0],0)
    impossible=evaluate([4,0,0,6,0,0,7,0,0],0)
    assert positive['feedback_action_dependence'] and not impossible['feedback_action_dependence']
    return dict(version='DIGITAL-FEEDBACK-08-STRUCTURAL-v1',ancestor=list(ANCESTOR),
                limit=LIMIT,variants=rows,prepared_positive=positive,prepared_impossible=impossible,
                organism_worlds=0,resources_measured=False,viability=None,learning=False,evolution=False)

if __name__=='__main__': print(json.dumps(study(),sort_keys=True,separators=(',',':')))
