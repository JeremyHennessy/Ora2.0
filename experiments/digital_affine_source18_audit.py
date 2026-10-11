"""Independent affine-source ISA interpreter; no producer/compiler import."""
import hashlib, json

def interpret(code, values):
    latch, port = values; storage = {i:0 for i in range(8)}; storage[1] = port
    regs = {0:0,1:0}; cursor = 5; steps = []
    for cost in range(1,9):
        address = cursor; opcode,left,right = code[address]; cursor = (cursor+1)%13
        if opcode == 1: regs[left%2] = latch
        elif opcode == 2: regs[left%2] = storage[right%8]
        elif opcode == 3: storage[left%8] = regs[right%2]
        elif opcode == 4: regs[left%2] = right%16
        elif opcode == 5: regs[left%2] = regs[left%2] ^ regs[right%2]
        elif opcode == 7: cursor = right%13
        else: assert opcode in (6,18)
        steps.append(dict(pc=address,instruction=code[address],registers=[regs[i] for i in range(2)],memory=[storage[i] for i in range(8)],next_pc=cursor))
        if opcode == 6: return dict(port=regs[left%2]%2,instructions=cost,trace=steps)
    raise AssertionError('Output missing')

def endpoint(bank):
    try:
        assert type(bank) is list and len(bank)==8
        for expected,row in enumerate(bank):
            assert type(row['identity']) is int and row['identity']==expected
            assert [p['inputs'] for p in row['probes']]==[[0,0],[0,1],[1,0],[1,1]]
            for p in row['probes']:
                f,last = p['inputs']; assert type(f) is int and type(last) is int
                assert type(p['port']) is int and p['port']==(((expected>>2)*f)^(((expected>>1)&1)*last)^(expected&1))
        return True
    except (AssertionError,KeyError,TypeError,ValueError): return False

def audit(record):
    def typed(x,key=None):
        if type(x) is dict:
            for k,v in x.items(): assert type(k) is str; typed(v,k)
        elif type(x) is list:
            for v in x: typed(v)
        elif key=='software_only': assert type(x) is bool
        else: assert type(x) in (int,str)
    typed(record)
    assert record['contract']=='DIGITAL-AFFINE-SOURCE-18-v1' and record['software_only'] is True and record['world_histories']==0
    assert endpoint(record['bank']); hashes=set(); outputs=set()
    for row in record['bank']:
        code=row['program']; assert len(code)==13
        assert all(type(r) is list and len(r)==3 and all(type(v) is int and 0<=v<32 for v in r) for r in code)
        assert code[:5]==[[4,1,1],[6,0,0],[5,0,1],[6,0,0],[3,1,0]]
        identity=row['identity']; a,b,c=identity//4,(identity//2)%2,identity%2
        assert code[5:]==[[2,0,1] if b else [4,0,0],
            [1,1,0] if a else [18,0,0], [5,0,1] if a else [18,0,0],
            [4,1,c],[5,0,1],[3,1,0],[6,0,0],[7,0,5]]
        digest=hashlib.sha256(json.dumps(code,separators=(',',':')).encode()).hexdigest()
        assert row['program_sha256']==digest; hashes.add(digest)
        outputs.add(tuple(p['port'] for p in row['probes']))
        for p in row['probes']:
            assert p==dict(inputs=p['inputs'],**interpret(code,p['inputs']))
            assert p['instructions']==7 and p['trace'][-1]['memory'][1]==p['port']
        assert code[-1]==[7,0,5]
    assert len(hashes)==len(outputs)==8
    return dict(verified=True,programs=8,truth_probes=32,unique_programs=8,distinct_functions=8,
        formation_energy=55,formation_material=55,constructor_remaining=73,release_energy=16,
        first_loop_cost=7,recurring_cycle_cost=8,software_only=True,world_histories=0,
        paid_viability=None,ordinary_advantage=None,learning=False,evolution=False,stage_credit=False)

if __name__=='__main__':
    import sys
    with open(sys.argv[1],encoding='utf-8') as f: print(json.dumps(audit(json.load(f)),sort_keys=True))
