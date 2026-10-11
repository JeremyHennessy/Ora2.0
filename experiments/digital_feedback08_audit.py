"""Independent finite-state interpretation; never imports the producer."""
import json,sys

GENOME=[4,1,1,6,0,0,5,0,1,10,0,0,12,0,0,7,0,1]

def interpret(tape, outcome, prior, start):
    cells=tape[:]; r={0:prior,1:1}; ram={i:0 for i in range(8)}
    pointer=start; site=0; count=0; size=len(cells)//3
    for elapsed in range(64):
        instruction=cells[pointer*3:pointer*3+3]
        opcode,x,y=instruction; dest=x%2; other=y%2
        pointer=(pointer+1)%size
        if opcode==6: return {'status':'action','port':r[dest]%2,'steps':elapsed+1,'feedback_reads':count}
        if opcode==17: return {'status':'halt','port':None,'steps':elapsed+1,'feedback_reads':count}
        if opcode in (0,1,2,4):
            values={0:site,1:outcome,2:ram[y%8],4:y%16}
            r[dest]=values[opcode];count+=int(opcode==1)
        if opcode==3: ram[x%8]=r[other]
        if opcode==5: r[dest]=r[dest]^r[other]
        if opcode in (7,11) or opcode==8 and r[dest]==0: pointer=y%size
        if opcode==9: cells[y%len(cells)]=r[dest]
        if opcode==13: site=(site+2*(r[dest]%2)-1)%4
    return {'status':'bounded_no_action','port':None,'steps':64,'feedback_reads':count}

def check(record,tape,start):
    assert type(record['probes']) is list and len(record['probes'])==4
    for p in record['probes']:
        assert type(p['steps']) is type(p['feedback_reads']) is int
        assert p['port'] is None or type(p['port']) is int
        assert type(p['status']) is str
    expected=[interpret(tape,answer,prior,start) for prior in range(2) for answer in range(2)]
    assert record['probes']==expected
    causal=any(expected[i]['status']==expected[i+1]['status']=='action' and expected[i]['port']!=expected[i+1]['port'] for i in (0,2))
    assert record['feedback_action_dependence'] is causal
    assert record['retains_copy_divide'] is (10 in tape[::3] and 12 in tape[::3])
    return causal

def audit(data):
    assert all(type(x) is int for x in data['ancestor'])
    assert type(data['limit']) is type(data['organism_worlds']) is int
    assert data['version']=='DIGITAL-FEEDBACK-08-STRUCTURAL-v1' and data['ancestor']==GENOME and data['limit']==64
    assert len(data['variants'])==18*31 and data['organism_worlds']==0 and data['resources_measured'] is False
    assert data['viability'] is None and data['learning'] is data['evolution'] is False
    assert check(data['prepared_positive'],[1,0,0,6,0,0,7,0,0],0)
    assert not check(data['prepared_impossible'],[4,0,0,6,0,0,7,0,0],0)
    found=[];index=0
    for address,old in enumerate(GENOME):
        for value in range(32):
            if value==old: continue
            row=data['variants'][index];index+=1
            assert all(type(row[k]) is int for k in ('address','old','value'))
            assert (row['address'],row['old'],row['value'])==(address,old,value)
            code=GENOME[:];code[address]=value
            if check(row,code,2): found.append(dict(address=address,value=value,retains_copy_divide=row['retains_copy_divide']))
    return dict(verified=True,variants=index,probes=index*4,dependent_variants=found,
                dependent_with_copy_divide=sum(x['retains_copy_divide'] for x in found),
                structural_only=True,viability=None,organism_worlds=0,learning=False,evolution=False)

if __name__=='__main__': print(json.dumps(audit(json.load(open(sys.argv[1],encoding='utf-8'))),sort_keys=True))
