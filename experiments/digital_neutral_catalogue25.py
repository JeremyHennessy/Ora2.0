"""Exhaustive external genotype catalogue; no performance evaluation or World."""
import hashlib,json

VERSION='DIGITAL-NEUTRAL-CATALOGUE-25-v1'
PARENT=((4,1,1),(6,0,0),(5,0,1),(6,0,0),(3,1,0),(2,0,1),(18,0,0),(18,0,0),(4,1,1),(5,0,1),(3,1,0),(6,0,0),(7,0,5))

def digest(program):
    return hashlib.sha256(json.dumps(program,separators=(',',':')).encode()).hexdigest()

def candidate(identity):
    if type(identity) is not int or not 0<=identity<744:raise ValueError('Catalogue identity must be an integer0..743')
    address=15+identity//31;old=PARENT[address//3][address%3]
    values=[v for v in range(32) if v!=old];value=values[identity%31]
    code=[list(r) for r in PARENT];code[address//3][address%3]=value
    return dict(candidate_id=identity,parent_sha256=digest(PARENT),program=code,program_sha256=digest(code),mutation=dict(flat_address=address,old=old,new=value),source='external exhaustive one-word substitution; no performance selection')

def manifest():
    return dict(contract=VERSION,parent_program=[list(r) for r in PARENT],parent_sha256=digest(PARENT),preserved_prefix_triples=5,mutable_flat_addresses=list(range(15,39)),legal_values=list(range(32)),candidate_count=744,candidates=[candidate(i) for i in range(744)],candidate_order='flat address ascending, replacement value ascending excluding original',selection='none; all744 retained',developer_assistance='authored fixed ancestor/cold-start prefix and external enumerative variation',world_histories=0,seeds_executed=[],organism_births=0,learning=False,evolution=False,stage_credit=False)

if __name__=='__main__':print(json.dumps(manifest(),sort_keys=True,separators=(',',':')))
