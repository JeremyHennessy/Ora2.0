"""Literal, independent static family/reference enumeration; no producer or VM."""
import hashlib, json

def h(x):return hashlib.sha256(json.dumps(x,separators=(',',':')).encode()).hexdigest()

def audit(m):
    p=[[4,1,1],[6,0,0],[5,0,1],[6,0,0],[3,1,0],[2,0,1],[18,0,0],[18,0,0],[4,1,1],[5,0,1],[3,1,0],[6,0,0],[7,0,5]]
    assert m['contract']=='DIGITAL-SOURCE-32-ADMISSION-v1'
    assert m['seeds']==[32100,32101] and m['controls']==['intact','retained_disabled','own_disrupted']
    assert m['horizon']==512 and m['checkpoint']==64 and m['structural_order']==list(range(56))
    assert m['candidate_histories']==336 and m['reference_histories']==66 and m['total_histories']==402
    assert m['performance_selection'] is m['primary'] is m['stage_credit'] is False and m['world_histories_executed']==0
    assert len(m['candidates'])==56 and len(m['references'])==11
    index=0
    for f in range(5,13):
        for b in range(5,13):
            if f==b:continue
            x=m['candidates'][index]; mid=[r[:] for r in p];mid[f][0]=1;code=[r[:] for r in mid];code[b][0]=8
            assert type(x['candidate_id']) is int and x['candidate_id']==index and x['program']==code
            assert x['parent_sha256']==h(p) and x['program_sha256']==h(code) and x['intermediate_program_sha256']==h(mid)
            assert x['catalogue25_intermediate_id']==(3*f-15)*31+[v for v in range(32) if v!=p[f][0]].index(1)
            assert x['external_mutations']==[dict(flat_address=3*f,old=p[f][0],new=1),dict(flat_address=3*b,old=p[b][0],new=8)]
            assert x['birth'] is x['viability_tested'] is x['primary_admitted'] is False
            assert x['feedback_slot']==f and x['branch_slot']==b and x['branch_register']==code[b][1]%2 and x['branch_target']==code[b][2]%13
            index+=1
    expected={}
    for i in range(8):
        a,b,c=i//4,(i//2)%2,i%2
        expected[f'affine{i}']=p[:5]+[[2,0,1] if b else [4,0,0],[1,1,0] if a else [18,0,0],[5,0,1] if a else [18,0,0],[4,1,c],[5,0,1],[3,1,0],[6,0,0],[7,0,5]]
    expected.update(alternating=[[4,1,1],[6,0,0],[5,0,1],[7,0,1]],fixed0=[[4,0,0],[6,0,0],[7,0,0]],fixed1=[[4,0,1],[6,0,0],[7,0,0]])
    assert [r['role'] for r in m['references']]==list(expected)
    assert all(r['program']==expected[r['role']] and r['assistance']=='authored fixed/reactive comparator' for r in m['references'])
    return dict(verified=True,complete_candidates=56,complete_references=11,planned_histories=402,world_histories=0,learning=False,stage_credit=False)

if __name__=='__main__':
    import sys
    with open(sys.argv[1],encoding='utf-8') as f:result=audit(json.load(f))
    print(json.dumps(result,sort_keys=True))
