"""Performance-blind external two-opcode catalogue; never instantiates a VM."""
import json
from .digital_neutral_catalogue25 import PARENT,candidate as first,digest

VERSION='DIGITAL-BRANCH-SOURCE-30-v1'
PAIRS=tuple((f,b) for f in range(5,13) for b in range(5,13) if f!=b)

def candidate(identity):
    if type(identity) is not int or not 0<=identity<56:raise ValueError('Source30 identity must be integer0..55')
    feedback,branch=PAIRS[identity];address=3*feedback
    old=PARENT[feedback][0];values=[v for v in range(32) if v!=old];intermediate_id=(address-15)*31+values.index(1)
    ancestor=first(intermediate_id);code=[r[:] for r in ancestor['program']];previous=code[branch][0];assert previous not in (1,8);code[branch][0]=8
    return dict(candidate_id=identity,parent_sha256=digest(PARENT),catalogue25_intermediate_id=intermediate_id,intermediate_program_sha256=ancestor['program_sha256'],program=code,program_sha256=digest(code),external_mutations=[ancestor['mutation'],dict(flat_address=3*branch,old=previous,new=8)],feedback_slot=feedback,branch_slot=branch,branch_register=code[branch][1]%2,branch_target=code[branch][2]%13,source='external exhaustive ordered FEEDBACK/JZ opcode substitution pair; operands unchanged; no fitness query',birth=False,viability_tested=False,primary_admitted=False)

def manifest():
    return dict(contract=VERSION,parent_program=[list(r) for r in PARENT],parent_sha256=digest(PARENT),candidate_count=56,candidates=[candidate(i) for i in range(56)],order='feedback opcode slot5..12 ascending, branch opcode slot5..12 ascending excluding same slot',preserved_prefix_triples=5,program_triples=13,formation_cost=55,state_units=16,initial_free_material=457,initial_constructor_remaining=73,startup_endowment=12,source25_denominator=744,source25_replaced=False,structural_bias='exactly one feedback and one conditional branch; all original operands retained; chosen before outcomes, not uniform over all genomes',performance_selection=False,world_histories=0,actions=0,seeds_executed=[],births=0,deaths=0,learning=False,evolution=False,stage_credit=False,required_next_dependency='PC-inclusive lawful history controls, broadened independent VM/paid endpoint scope, and actual cold/personal-opportunity admission before any new source World or primary')

if __name__=='__main__':print(json.dumps(manifest(),sort_keys=True,separators=(',',':')))
