"""Independent bytecode interpreter; imports only the unchanged task auditor."""
import hashlib, json
from experiments.digital_memory_task_audit import audit as task_audit


def h(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',',':')).encode()).hexdigest()


def audit(row):
    assert row['version'] == 'DIGITAL-MEMORY-BINDING-01'
    program = row['program']
    assert isinstance(program,list) and 1 <= len(program) <= 32
    assert all(isinstance(i,list) and len(i)==3 and all(type(v) is int and 0<=v<32 for v in i) for i in program)
    code = sum((i[:] for i in program), [])
    cells = code + [0]*13; bill = len(cells)
    assert bill <= 128
    assert row['formation'] == [dict(unit=i,value=v,energy=1,assistance='researcher assembly') for i,v in enumerate(cells)]
    metrics = task_audit(row['task'])
    registers=[0,0]; pc=0; cue=0; feedback=0; memory=[0]*8
    assert len(row['events']) == len(row['task']['events'])
    writes=0
    for tick,(event,kernel) in enumerate(zip(row['events'],row['task']['events'])):
        opcode,a,b = code[3*pc:3*pc+3]
        op='read'; arg=7
        if opcode==0: op='sense'; arg=None
        if opcode==2: arg=b%8
        if opcode==3: op='write'; arg=[a%8,registers[b%2]]
        if opcode==6: op='act'; arg=registers[a%2]%2
        assert kernel['op']==op and kernel['arg']==arg
        destination=(pc+1)%len(program); changed=None
        if opcode==0: cue=kernel['out']; registers[a%2]=cue
        if opcode==1: registers[a%2]=feedback
        if opcode==2: registers[a%2]=kernel['out']
        if opcode==3: memory[a%8]=registers[b%2]
        if opcode==4: registers[a%2]=b%16
        if opcode==5: registers[a%2]=registers[a%2]^registers[b%2]
        if opcode==6: feedback=kernel['out']
        if opcode==7: destination=b%len(program)
        if opcode==8 and registers[a%2]==0: destination=b%len(program)
        if opcode==9:
            address=b%len(code); code[address]=registers[a%2]; writes+=1
            changed=dict(unit=address,value=code[address])
        pc=destination
        state=dict(program_hash=h(code),memory_hash=h(memory),registers=registers[:],pc=pc,cue=cue,feedback=feedback)
        assert event==dict(tick=tick,decoded=[opcode,a,b],task_tick=tick,code_write=changed,state=state)
    opcode,a,b=code[3*pc:3*pc+3]; op='read';arg=7
    if opcode==0: op='sense';arg=None
    if opcode==2: arg=b%8
    if opcode==3: op='write';arg=[a%8,registers[b%2]]
    if opcode==6: op='act';arg=registers[a%2]%2
    assert row['stop']==dict(op=op,arg=arg)
    assert not metrics['energy'] or metrics['instructions']==256 or (metrics['actions']==64 and op in ('sense','act'))
    final=dict(code=code,memory=memory,registers=registers,pc=pc,cue=cue,feedback=feedback,
               constructor_remaining=128-bill,constructor_heat=bill,assigned=list(range(bill)),free=list(range(bill,512)))
    assert row['final']==final and row['state_hash']==h(final)
    assert row['task']['mode']=='normal'
    assert metrics['energy']+metrics['heat']+20*metrics['unconsumed_food']+final['constructor_remaining']+bill==1420
    return metrics | dict(formation_cost=bill,total_paid_cost=bill+metrics['instructions'],
                          code_writes=writes,change_exposed=metrics['actions']>32,
                          classification='AUTHORED_PROGRAM_MEASUREMENT_ONLY')


if __name__=='__main__':
    import sys
    print(json.dumps([audit(r) for r in json.load(open(sys.argv[1],encoding='utf-8'))],sort_keys=True))
