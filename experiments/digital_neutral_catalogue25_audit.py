"""Independent catalogue reconstruction and static bills, no producer import."""
import hashlib,json,sys
from .digital_affine_source18 import compile_program

def digest(program):return hashlib.sha256(json.dumps(program,separators=(',',':')).encode()).hexdigest()

def audit(data):
    assert data['contract']=='DIGITAL-NEUTRAL-CATALOGUE-25-v1' and data['world_histories']==0 and data['seeds_executed']==[]
    parent=compile_program(3);flat=[v for triple in parent for v in triple]
    assert data['parent_program']==parent and data['parent_sha256']==digest(parent)
    assert data['candidate_count']==744 and len(data['candidates'])==744 and data['mutable_flat_addresses']==list(range(15,39))
    expected={(i,v) for i in range(15,39) for v in range(32) if v!=flat[i]};seen=set();hashes=set();classes={k:0 for k in ('immutable_no_copy_or_division','copy_without_division','division_without_copy','self_write_bit_closed')};bills=[]
    for index,c in enumerate(data['candidates']):
        assert type(c['candidate_id']) is int and c['candidate_id']==index
        code=c['program'];assert len(code)==13 and all(type(t) is list and len(t)==3 and all(type(v) is int and v in range(32) for v in t) for t in code)
        changed=[(i,v) for i,v in enumerate(sum(code,[])) if v!=flat[i]];assert len(changed)==1
        address,value=changed[0];assert (address,value) in expected and (address,value) not in seen;seen.add((address,value))
        assert code[:5]==parent[:5] and c['mutation']==dict(flat_address=address,old=flat[address],new=value)
        assert c['program_sha256']==digest(code) and c['parent_sha256']==digest(parent);assert digest(code) not in hashes;hashes.add(digest(code))
        # Lexicographic order is recovered independently from the changed cell.
        assert index==31*(address-15)+value-int(value>flat[address])
        ops=[t[0] for t in code]
        if 9 in ops:
            assert ops.count(9)==1 and 10 not in ops and 12 not in ops
            sw=next(t for t in code if t[0]==9);assert sw[2] in (0,1,5)
            assert all(op in (2,3,4,5,6,7,9,18) for op in ops)
            assert all(t[2]==1 for t in code if t[0]==4)
            category='self_write_bit_closed'
        elif 10 in ops:
            assert ops.count(10)==1 and 12 not in ops;category='copy_without_division'
        elif 12 in ops:
            assert ops.count(12)==1 and 10 not in ops;category='division_without_copy'
        else:category='immutable_no_copy_or_division'
        classes[category]+=1
        bills.append(dict(candidate_id=index,formation_energy=55,code_material=39,state_material=16,free_material=457,startup_energy=12,constructor_after_formation=73,release_reserved=16,constructor_after_release_if_reached=57,cold_instruction_cost=5,cold_successes=1,cold_failures=1,cold_cap_loss=0,cold_live_energy=27,post_boot_viability=None,lifecycle_class=category,maximum_nursery_words=39 if category=='copy_without_division' else 0,maximum_additional_copy_energy=39 if category=='copy_without_division' else 0,candidate_can_produce_offspring=False))
    assert seen==expected and classes==dict(immutable_no_copy_or_division=720,copy_without_division=8,division_without_copy=8,self_write_bit_closed=8)
    return dict(verified=True,classification='EXHAUSTIVE_EXTERNAL_SOURCE_AND_STATIC_BUDGET_ONLY',candidate_count=744,genome_hashes=len(hashes),classes=classes,static_bills=bills,world_histories=0,seeds_executed=[],post_boot_viability=None,learning=False,evolution=False,stage_credit=False)

if __name__=='__main__':print(json.dumps(audit(json.load(open(sys.argv[1],encoding='utf-8'))),sort_keys=True,separators=(',',':')))
