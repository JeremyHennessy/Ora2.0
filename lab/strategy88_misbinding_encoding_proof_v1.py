"""Data-only finite identity on the already qualified retained-event derivation."""
import json
from pathlib import Path
L=Path('D:/OraLab');r=json.loads((L/'reports/strategy88-closed-origins-v1.json').read_bytes())['summary']
lookup={(x['seed'],x['role']):x for x in r['all312']};pairs=0;pred_mismatches=0;encoding_mismatches=0;sequence_bad=0;changes=0
def prediction(s,c):return (0,1,c%2,1-c%2)[s]
assert all((s+e+2)%4==((s+2)%4+e)%4 for s in range(4) for e in (0,1))
assert all(prediction((s+2)%4,0)==prediction(s,0) for s in range(4))
for seed,role in lookup:
 if not role.startswith('adaptive:'):continue
 prior=int(role[-1]);a=lookup[seed,role];m=lookup[seed,'credit_misbound:'+str(prior)]
 aa=[x for x in a['predictions'] if x['late']];mm=[x for x in m['predictions'] if x['late']]
 assert len(aa)==len(mm)==12;changes+=m['actual_entry_changes']
 for k,(x,y) in enumerate(zip(aa,mm,strict=True)):
  assert (x['packet'],x['cue'])==(y['packet'],y['cue']);pairs+=1
  pred_mismatches+=x['port']!=y['port'];encoding_mismatches+=y['strategy']!=(x['strategy']+2*(k+1))%4;sequence_bad+=x['cue']%2!=k%2
assert pairs==576 and changes==576 and pred_mismatches==encoding_mismatches==sequence_bad==0
v=dict(verified=True,scope='Conditional finite state-encoding proof on ALL48 retained pairs,not new physics or acceptance',common_late_pairs=pairs,actual_semantic_entry_changes=changes,
 port_mismatches=pred_mismatches,strategy_encoding_mismatches=encoding_mismatches,cue_parity_sequence_mismatches=sequence_bad,finite_transition_identity=True,
 relation='misbound_strategy[k]=(adaptive_strategy[k]+2*(k+1)) mod4. Paid feedback advances both by the same error bit;P=+2 commutes with advance. At even k cue parity0 makes P prediction-invariant;odd k uses identity.',
 conclusion='This intervention preserves acquired route history in an alternative time-dependent encoding on these retained packet sequences. Clearing origin annotations is not a physical history ablation. No correction/rerun of closed88 is admitted.',new_worlds=0,new_targets=0)
(L/'reports/strategy88-misbinding-encoding-proof-v1.json').write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8');print(json.dumps(v,indent=2))
