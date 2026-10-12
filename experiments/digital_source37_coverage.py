"""Externally supplied neutral mutation paths; no World or performance query."""
import hashlib,json
from functools import lru_cache
from .digital_branch_source30 import candidate as ancestor
from .digital_neutral_catalogue25 import PARENT,digest

VERSION='DIGITAL-SOURCE-37-COVERAGE-v1'
OPS=(1,2,3,4,5,6,7,8,18)
PATHS_PER_PARENT=560
COUNT=56*PATHS_PER_PARENT
NONCE=0

@lru_cache(maxsize=56)
def edits(parent_id):
    p=ancestor(parent_id)
    return tuple((3*slot+word,old,new) for slot in range(5,13) for word in range(3)
                 for old in (p['program'][slot][word],)
                 for new in (OPS if word==0 else range(32)) if new!=old)

def candidate(identity):
    if type(identity) is not int or not 0<=identity<COUNT:raise ValueError('Source37 path identity 0..31359 required')
    parent_id,ordinal=divmod(identity,PATHS_PER_PARENT);p=ancestor(parent_id);address,old,new=edits(parent_id)[ordinal]
    code=[r[:] for r in p['program']];assert code[address//3][address%3]==old;code[address//3][address%3]=new
    return dict(path_id=identity,source30_parent_id=parent_id,parent_program_sha256=p['program_sha256'],root_parent_sha256=p['parent_sha256'],catalogue25_intermediate_id=p['catalogue25_intermediate_id'],intermediate_program_sha256=p['intermediate_program_sha256'],external_mutations=p['external_mutations']+[dict(flat_address=address,old=old,new=new)],program=code,program_sha256=digest(code),formation_cost=55,state_units=16,initial_free_material=457,constructor_after_formation=73,startup_endowment=12,birth=False,viability_tested=False,primary_admitted=False,source='external legal one-word substitution after every Source30 parent; no performance query')

def selection():
    selected=[];draws=[];threshold=(2**32//560)*560
    for parent_id in range(56):
        used=set()
        for counter in range(4096):
            payload=[VERSION,NONCE,parent_id,counter];raw=int(hashlib.sha256(json.dumps(payload,separators=(',',':')).encode()).hexdigest()[:8],16)
            ordinal=raw%560;disposition='range_rejected' if raw>=threshold else ('duplicate_path_rejected' if ordinal in used else 'accepted')
            draws.append(dict(parent_id=parent_id,counter=counter,raw=raw,ordinal=ordinal,disposition=disposition))
            if disposition=='accepted':used.add(ordinal);selected.append(parent_id*560+ordinal)
            if len(used)==2:break
        else:raise ValueError('Finite source draw budget exhausted')
    return selected,draws

def manifest():
    ids,draws=selection()
    return dict(contract=VERSION,nonce=NONCE,source_path_count=COUNT,paths_per_parent=560,sample_count=112,path_ids=ids,draws=draws,candidates=[candidate(i) for i in ids],parent_count=56,all_source30_parents_included=True,root_parent_program=[list(r) for r in PARENT],root_parent_sha256=digest(PARENT),preserved_prefix_triples=5,program_triples=13,legal_opcodes=list(OPS),performance_selection=False,unique_mutation_paths_not_unique_genomes=True,aliases_and_duplicate_genomes_retained=True,structural_bias='Source30 F/JZ structural family plus one legal tail-word edit; stratified two paths per parent; effective operand aliases retained; not uniform over unique genomes or all programs',developer_assistance='fixed non-learning ancestor/cold prefix, external F/JZ edits and external additional word edit; host sampler is not an organism instruction or discovery',world_histories=0,seeds_executed=[],births=0,deaths=0,learning=False,evolution=False,stage_credit=False,next_dependency='Review guarded unchanged-law input scope and whole-cost unscreened candidate/ordinary-reference viability and personal opportunities before any learning primary')

if __name__=='__main__':print(json.dumps(manifest(),sort_keys=True,separators=(',',':')))
