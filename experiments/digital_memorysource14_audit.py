"""Independent small-step ISA interpreter and exhaustive circuit measurement."""
import hashlib,json

def interpret(code,inputs):
    older,current,previous=inputs
    storage={i:0 for i in range(8)};storage[0]=older;storage[1]=previous
    register={0:0,1:0};address=5;steps=[]
    for count in range(1,33):
        old=address;opcode,left,right=code[old];address=(old+1)%32
        if opcode==1:register[left%2]=current
        elif opcode==2:register[left%2]=storage[right%8]
        elif opcode==3:storage[left%8]=register[right%2]
        elif opcode==4:register[left%2]=right%16
        elif opcode==7:address=right%32
        elif opcode==8 and register[left%2]==0:address=right%32
        else:assert opcode in (6,8)
        steps.append(dict(pc=old,instruction=code[old],registers=[register[i] for i in range(2)],memory=[storage[i] for i in range(8)],next_pc=address))
        if opcode==6:return dict(port=register[left%2]%2,instructions=count,trace=steps)
    raise AssertionError('Prepared output unreachable')

def endpoint(bank):
    try:
        assert len(bank)==256 and [r['table'] for r in bank]==list(range(256))
        for r in bank:
            table=r['table'];assert type(table) is int and len(r['probes'])==8
            assert [p['inputs'] for p in r['probes']]==[[o,f,p] for o in (0,1) for f in (0,1) for p in (0,1)]
            for p in r['probes']:
                o,f,last=p['inputs'];assert p['port']==(table>>(4*o+2*f+last))&1
        return True
    except (AssertionError,KeyError,TypeError):return False

def audit(record):
    def typed(value,key=None):
        if isinstance(value,dict):
            for k,v in value.items():assert type(k) is str;typed(v,k)
        elif isinstance(value,list):
            for v in value:typed(v)
        elif key=='software_only':assert type(value) is bool
        else:assert type(value) in (int,str)
    typed(record)
    assert record['contract']=='DIGITAL-MEMORYSOURCE-14-v1' and record['software_only'] is True and record['world_histories']==0
    assert endpoint(record['bank']);costs=[];hashes=set();dependence=[0,0,0]
    for row in record['bank']:
        code=row['program'];assert len(code)==32 and all(len(r)==3 and all(type(v) is int and 0<=v<32 for v in r) for r in code)
        assert code[:5]==[[4,1,1],[6,0,0],[5,0,1],[6,0,0],[3,1,0]]
        digest=hashlib.sha256(json.dumps(code,separators=(',',':')).encode()).hexdigest();assert digest==row['program_sha256'];hashes.add(digest)
        values={tuple(p['inputs']):p['port'] for p in row['probes']}
        for position in range(3):
            dependence[position]+=int(any(values[k]!=values[tuple((1-v if i==position else v) for i,v in enumerate(k))] for k in values))
        for p in row['probes']:
            assert p==dict(inputs=p['inputs'],**interpret(code,p['inputs']))
            assert p['trace'][-1]['memory'][:2]==[p['inputs'][1],p['port']]
            costs.append(p['instructions'])
    assert len(hashes)==256
    # ACT's output fixture ends before loop-back JUMP; add its real cost for
    # recurring action cadence. No finite-world yields are inferred from this.
    return dict(verified=True,programs=256,truth_probes=2048,unique_programs=256,
                formation_energy=112,formation_material=112,constructor_remaining=16,release_energy=16,
                prepared_first_loop_cost=sorted(set(costs)),recurring_cycle_cost=sorted({c+1 for c in costs}),
                input_dependent_tables=dependence,software_only=True,world_histories=0,
                paid_viability=None,ordinary_advantage=None,learning=False,stage_credit=False)

if __name__=='__main__':
    import sys
    with open(sys.argv[1],encoding='utf-8') as f:print(json.dumps(audit(json.load(f)),sort_keys=True))
