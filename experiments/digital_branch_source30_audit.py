"""Independent source/ancestry reconstruction with literal frozen ancestor."""
import hashlib,json

def h(x):return hashlib.sha256(json.dumps(x,separators=(',',':')).encode()).hexdigest()

def audit(data):
    parent=[[4,1,1],[6,0,0],[5,0,1],[6,0,0],[3,1,0],[2,0,1],[18,0,0],[18,0,0],[4,1,1],[5,0,1],[3,1,0],[6,0,0],[7,0,5]]
    assert data['contract']=='DIGITAL-BRANCH-SOURCE-30-v1' and data['parent_program']==parent and data['parent_sha256']==h(parent)
    assert type(data['candidate_count']) is int and data['candidate_count']==56 and len(data['candidates'])==56
    hashes=set();ids=[];targets={0:0,1:0,5:0};registers={0:0,1:0};index=0
    for f in range(5,13):
        for b in range(5,13):
            if f==b:continue
            x=data['candidates'][index];assert type(x['candidate_id']) is int and x['candidate_id']==index
            middle=[r[:] for r in parent];middle[f][0]=1;code=[r[:] for r in middle];code[b][0]=8
            source25_id=(3*f-15)*31+[v for v in range(32) if v!=parent[f][0]].index(1)
            assert x['catalogue25_intermediate_id']==source25_id and x['intermediate_program_sha256']==h(middle)
            assert x['program']==code and x['program_sha256']==h(code) and x['parent_sha256']==h(parent)
            assert x['external_mutations']==[dict(flat_address=3*f,old=parent[f][0],new=1),dict(flat_address=3*b,old=parent[b][0],new=8)]
            assert x['feedback_slot']==f and x['branch_slot']==b and x['branch_register']==code[b][1]%2 and x['branch_target']==code[b][2]%13
            assert x['birth'] is x['viability_tested'] is x['primary_admitted'] is False
            assert code[:5]==parent[:5] and sum(r[0]==1 for r in code)==sum(r[0]==8 for r in code)==1
            hashes.add(h(code));ids.append(source25_id);targets[x['branch_target']]+=1;registers[x['branch_register']]+=1;index+=1
    assert len(hashes)==56 and len(set(ids))==8
    assert data['source25_denominator']==744 and data['source25_replaced'] is False
    assert data['preserved_prefix_triples']==5 and data['program_triples']==13 and data['state_units']==16
    assert data['formation_cost']==3*13+16==55 and data['initial_free_material']==512-55==457 and data['initial_constructor_remaining']==128-55==73 and data['startup_endowment']==12
    assert data['performance_selection'] is False and data['world_histories']==data['births']==data['deaths']==data['actions']==0 and data['seeds_executed']==[]
    assert data['learning'] is data['evolution'] is data['stage_credit'] is False
    return dict(verified=True,candidate_count=56,unique_programs=56,intermediate_catalogue25_ids=sorted(set(ids)),branch_target_counts=targets,branch_register_counts=registers,cold_prefix_preserved=True,formation_cost=55,world_histories=0,viability_tested=False,primary_admitted=False,learning=False,stage_credit=False)

if __name__=='__main__':
    import sys
    print(json.dumps(audit(json.load(open(sys.argv[1],encoding='utf-8'))),sort_keys=True))
