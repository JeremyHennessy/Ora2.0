"""Independent finite arithmetic/AST preflight; no producer/World/target imports."""
import ast
from fractions import Fraction
import hashlib
import json
from math import comb
from pathlib import Path

ROOT=Path('D:/OraLab');DEV=ROOT/'src/Ora2.0-recording82'
literal=DEV/'experiments/digital_credited_fallback87_referee.py'
tree=ast.parse(literal.read_bytes())
fixed=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign)
    and any(isinstance(t,ast.Name) and t.id=='REFERENCE_PROGRAMMES' for t in n.targets)))
assert fixed[0]==[[7,2,1],[4,0,0],[6,0,0],[7,0,1]]
assert fixed[1]==[[7,2,1],[4,0,1],[6,0,0],[7,0,1]]
kernel=DEV/'experiments/digital_memory80.py';kt=ast.parse(kernel.read_bytes())
step=next(n for n in ast.walk(kt) if isinstance(n,ast.FunctionDef) and n.name=='step')
fee_condition=next(n.test for n in ast.walk(step) if isinstance(n,ast.If)
    and any(isinstance(x,ast.AugAssign) and isinstance(x.target,ast.Attribute)
            and x.target.attr=='constructor_remaining' for x in n.body))
assert ast.dump(fee_condition)==ast.dump(ast.parse('self.tick==64',mode='eval').body)

# Symbolic correct-constant reference timing/resource arithmetic, NOT VM replay.
# Target identity is not evaluated: assume the authored constant's correct bit.
tick=1;energy=111;food=set(range(64));next_packet=64;acts=[];fees=0
for decision in range(60):
    for operation in ('SET','ACT','JUMP'):
        tick+=1
        if tick%64==0:
            for _ in range(16):
                if len(food)<64:food.add(next_packet)
                next_packet+=1
        if tick==64:fees+=16
        assert energy>0
        energy-=1
        if operation=='ACT':
            available=[p for p in sorted(food) if not 16<=p<32 or tick>=64]
            assert available, 'No assumed free acquisition without actual packet'
            packet=available[0];food.remove(packet)
            energy=min(224,energy+20)
            acts.append(dict(decision=decision+1,tick=tick,packet=packet))
assert tick==181 and len(acts)==60 and energy>0 and acts[32]['tick']==99
fixed_n=20*60-181-22

# Independently enumerate source86 per-decision CFG costs symbolically.
st=ast.parse((DEV/'experiments/digital_credited_fallback86_source.py').read_bytes())
function=next(n for n in st.body if isinstance(n,ast.FunctionDef) and n.name=='programme')
body=next(n.value for n in ast.walk(function) if isinstance(n,ast.Return))
code=[None]+[ast.literal_eval(n) for n in body.elts[1:]]
lengths=[]
for entry in (1,6,16):
    for outcome in (0,1,2):
        pc=entry;cpu=0;reg=0
        while True:
            op,a,b=code[pc];cpu+=1;after=pc+1
            if op==1:reg=outcome
            elif op==8:
                # At updater branch bit may be either0/15; enumerate separately.
                if pc==15:break
                if reg==0:after=b
            elif op==7:after=b
            if (pc,after) in ((4,6),(5,1),(11,6),(19,6),(20,16)):break
            pc=after
            assert cpu<=9
        lengths.append(cpu)
assert min(lengths)==4
candidate_upper={str(q):20*60-(1+60*min(lengths))-(71+q) for q in (2,4,8)}
assert all(n<fixed_n for n in candidate_upper.values())
p=Fraction(sum(comb(16,k) for k in range(12,17)),2**16)
assert p==Fraction(2517,65536) and p>Fraction(1,900)
receipt=dict(verified=True,scope='AST/finite arithmetic ONLY; no physical replay or target query',
    worlds=0,targets=0,original_contract_sha256=hashlib.sha256((ROOT/'reports/credited-fallback87-prospective-contract-v1-20261015.md').read_bytes()).hexdigest(),
    fixed_constant_cpu=tick,fixed_constant_served=60,fixed_constant_nominal=fixed_n,
    act33_tick=acts[32]['tick'],reference_packet_availability_symbolically_checked=True,
    candidate_minimum_complete_loop_cpu=min(lengths),candidate_nominal_upper=candidate_upper,
    forced_constant_losses=4,maximum_sign_wins=12,minimum_possible_all16_p=str(p),
    required_p='1/900',registered_v1_acceptance_structurally_impossible=True,
    fee_specification_mismatch='Frozen v1 prose says fee16 each64 ticks; unchanged engine charges fee16 at tick64 ONLY',
    actual_fee_condition=ast.unparse(fee_condition),source_or_price_repair=False,
    source_only_qualification_not_paid_specification_proof=True)
(ROOT/'reports/credited-fallback87-prerun-feasibility-v1.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
