"""Independent necessary-accounting proof, not natural realization or RAF detection."""
import argparse
import json
from pathlib import Path


def inspect(data):
    if data['schema']!='kinetic01-budget-v1' or data['natural_worlds']!=0 or data['seed_maps_screened']!=0 or [c['length'] for c in data['cases']]!=list(range(2,7)):
        raise ValueError('Frozen feasibility denominator')
    denominator=0
    for case in data['cases']:
        old=None; count=dict(associate=0,cut=0,regenerate=0,release=0); completed=0
        for index,event in enumerate(case['events']):
            action,state=event['action'],event['state']; denominator+=1
            if set(state)!={'monomers','polymer_atoms','bonds','fuel','waste','photons','heat'} or any(type(v) is not int or v<0 for v in state.values()): raise ValueError('Finite nonnegative ledger')
            if state['monomers']+state['polymer_atoms']!=96 or state['fuel']+state['waste']!=256 or state['fuel']+state['photons']+state['bonds']+state['heat']!=768: raise ValueError('Material/energy conservation')
            if state['polymer_atoms']>case['length'] or state['bonds']!=max(0,state['polymer_atoms']-1): raise ValueError('Finite chain size/bonds')
            if index==0:
                expected=dict(monomers=96,polymer_atoms=0,bonds=0,fuel=256,waste=0,photons=512,heat=0)
                if action!='initial' or state!=expected: raise ValueError('No supplied organization')
            else:
                expected=dict(old)
                deltas={'select':dict(monomers=-1,polymer_atoms=1),'associate':dict(monomers=-1,polymer_atoms=1,bonds=1,fuel=-2,waste=2,heat=1),
                    'cut':dict(monomers=1,polymer_atoms=-1,bonds=-1,heat=1),'regenerate':dict(fuel=1,waste=-1,photons=-2,heat=1),
                    'release':dict(monomers=1,polymer_atoms=-1),'exhausted':{}}
                if action not in deltas: raise ValueError('Unknown reaction')
                if action=='select' and old['polymer_atoms']!=0 or action=='associate' and (old['fuel']<2 or old['monomers']<1 or old['polymer_atoms']<1) or action=='cut' and old['bonds']<1 or action=='regenerate' and (old['waste']<1 or old['photons']<2) or action=='release' and (old['bonds']!=0 or old['polymer_atoms']!=1): raise ValueError('Reaction preconditions')
                for key,value in deltas[action].items(): expected[key]+=value
                if state!=expected: raise ValueError('Exact reaction prices and waste')
                if action in count: count[action]+=1
                if action=='associate' and state['polymer_atoms']==case['length']: completed+=1
            old=state
        if case['events'][-1]['action']!='exhausted' or old!=dict(monomers=96,polymer_atoms=0,bonds=0,fuel=0,waste=256,photons=0,heat=768): raise ValueError('Finite exhaustion; no top-up')
        if case['paid_associations']!=256 or count['associate']!=256 or count['cut']!=256 or count['regenerate']!=256 or case['completed_cycles']!=completed or completed!=256//(case['length']-1): raise ValueError('Independent closed-form capacity')
    return dict(schema='kinetic01-budget-audit-v1',lengths=5,events=denominator,paid_associations_per_length=256,
        gross_energy_per_case=768,final_heat_per_case=768,natural_worlds=0,seed_maps_screened=0,
        accounting_feasible=True,productive_organization_demonstrated=False,inheritance_demonstrated=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--input',required=True); a=p.parse_args()
    try: print(json.dumps(inspect(json.loads(Path(a.input).read_bytes())),indent=2))
    except (ValueError,KeyError,TypeError) as error: print('Rejected:',error); raise SystemExit(2)
