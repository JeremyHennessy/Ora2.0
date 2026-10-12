"""Literal independent ancestry/edit/draw reconstruction; no source producer/VM."""
import hashlib,json
from .digital_neutral_catalogue25 import PARENT

def digest(x):return hashlib.sha256(json.dumps(x,separators=(',',':')).encode()).hexdigest()

def audit(m):
    version='DIGITAL-SOURCE-37-COVERAGE-v1';ops=(1,2,3,4,5,6,7,8,18)
    assert m['contract']==version and m['nonce']==0 and m['source_path_count']==31360 and m['paths_per_parent']==560 and m['sample_count']==112
    assert m['root_parent_program']==[list(r) for r in PARENT] and m['root_parent_sha256']==digest(PARENT)
    pairs=[(f,b) for f in range(5,13) for b in range(5,13) if f!=b];ids=[];draws=[];threshold=4294967296//560*560
    for parent_id in range(56):
        accepted=[]
        for counter in range(4096):
            raw=int(digest([version,0,parent_id,counter])[:8],16);ordinal=raw%560
            disposition='range_rejected' if raw>=threshold else ('duplicate_path_rejected' if ordinal in accepted else 'accepted')
            draws.append(dict(parent_id=parent_id,counter=counter,raw=raw,ordinal=ordinal,disposition=disposition))
            if disposition=='accepted':accepted.append(ordinal);ids.append(560*parent_id+ordinal)
            if len(accepted)==2:break
        assert len(accepted)==2
    assert m['draws']==draws and m['path_ids']==ids and len(set(ids))==112
    hashes=[]
    for identity,c in zip(ids,m['candidates']):
        parent_id,ordinal=divmod(identity,560);f,b=pairs[parent_id];parent=[list(r) for r in PARENT];first_old=parent[f][0];parent[f][0]=1;intermediate=digest(parent);second_old=parent[b][0];parent[b][0]=8
        parenthash=digest(parent);edit=[]
        for address in range(15,39):
            old=parent[address//3][address%3]
            values=ops if address%3==0 else tuple(range(32))
            edit.extend((address,old,new) for new in values if new!=old)
        assert len(edit)==560
        address,old,new=edit[ordinal];parent[address//3][address%3]=new;h=digest(parent)
        intermediate_id=(3*f-15)*31+[v for v in range(32) if v!=first_old].index(1)
        assert c['path_id']==identity and c['source30_parent_id']==parent_id and c['parent_program_sha256']==parenthash and c['root_parent_sha256']==digest(PARENT) and c['catalogue25_intermediate_id']==intermediate_id and c['intermediate_program_sha256']==intermediate
        assert c['program']==parent and c['program_sha256']==h and c['program'][:5]==[list(r) for r in PARENT[:5]]
        assert c['external_mutations']==[dict(flat_address=3*f,old=first_old,new=1),dict(flat_address=3*b,old=second_old,new=8),dict(flat_address=address,old=old,new=new)]
        assert all(t[0] in ops and len(t)==3 and all(type(v) is int and 0<=v<32 for v in t) for t in parent)
        assert (c['formation_cost'],c['state_units'],c['initial_free_material'],c['constructor_after_formation'],c['startup_endowment'])==(55,16,457,73,12)
        assert c['birth'] is c['viability_tested'] is c['primary_admitted'] is False
        hashes.append(h)
    assert len(m['candidates'])==112 and m['world_histories']==m['births']==m['deaths']==0 and m['seeds_executed']==[] and m['performance_selection'] is m['learning'] is m['evolution'] is m['stage_credit'] is False
    return dict(verified=True,path_count=31360,sample_count=112,parent_count=56,all_parents_included=True,draw_count=len(draws),range_rejections=sum(d['disposition']=='range_rejected' for d in draws),duplicate_path_rejections=sum(d['disposition']=='duplicate_path_rejected' for d in draws),distinct_genome_hashes=len(set(hashes)),formation_cost=55,world_histories=0,learning=False,stage_credit=False)

if __name__=='__main__':
    import sys
    with open(sys.argv[1],encoding='utf-8') as f:m=json.load(f)
    print(json.dumps(audit(m),sort_keys=True,separators=(',',':')))
