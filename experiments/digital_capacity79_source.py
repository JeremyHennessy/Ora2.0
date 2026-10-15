"""Neutral capacity/layout descriptors; emits VM data, never executes a World."""
import hashlib,json
VERSION='DIGITAL-CAPACITY79-SOURCE-v1'
DOMAIN=tuple((family,k) for family in (0,1) for k in range(1,7))
OPS=(0,1,6,7,8,19,20,21)
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def compile_programme(family,k):
 if type(family) is not int or type(k) is not int or (family,k) not in DOMAIN:raise ValueError('Frozen descriptor required')
 if family==0:
  code=[[7,0,3],[21,0,0],[7,0,3]]+[[6,0,0],[1,1,0],[8,1,1]]*k
 else:
  code=[[7,0,5],[19,0,1],[21,0,0],[20,1,0],[7,0,5]]+[[0,1,0],[19,0,1],[6,0,0],[1,0,0],[8,0,1]]*k
 return [t[:] for t in code]
def source(family,k):
 code=compile_programme(family,k);n=len(code);formation=3*n+16
 reasons=[]
 if n>32:reasons.append('instruction_capacity')
 if formation+32+16>128:reasons.append('factory_lifecycle_budget')
 return dict(version=VERSION,descriptor=[family,k],programme=code,programme_sha256=digest(code),parent=None,source_assistance='AUTHOR-SUPPLIED generic reactive/model controller and shared unrolled layout',performance_selection=False,acquired_state=dict(r=[0,0],m=[0]*8,pc=0,feedback=0),formation_cost=formation,startup_cost=32,release_cost=16,source_admissible=not reasons,source_refusals=reasons,success_cycle_instructions=(3 if family==0 else 5)*k+1,wrong_cycle_instructions=5 if family==0 else 9,wrong_penalty=4,entry_instructions=1,conditional_copy_and_div_cost=4*n+51,reproduction_admitted=False)
def manifest():
 return dict(version=VERSION,domain=[list(x) for x in DOMAIN],sources=[source(*x) for x in DOMAIN],scientific_worlds=0,scientific_targets=0,learning_claim=False,evolution_claim=False)
