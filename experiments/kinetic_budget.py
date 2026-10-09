"""Authored closed-budget feasibility only; zero natural worlds or seed screening."""
import argparse
import json
from pathlib import Path


def trajectory(length):
    if type(length) is not int or not 2<=length<=6: raise ValueError('Registered lengths 2..6')
    state=dict(monomers=96,polymer_atoms=0,bonds=0,fuel=256,waste=0,photons=512,heat=0)
    events=[]; joins=cycles=0
    def emit(action): events.append(dict(action=action,state=dict(state)))
    emit('initial')
    while True:
        if state['fuel']<2:
            if state['photons']<2 or not state['waste']:
                if state['bonds']:
                    while state['bonds']:
                        state['bonds']-=1; state['heat']+=1
                        state['monomers']+=1; state['polymer_atoms']-=1; emit('cut')
                    state['monomers']+=1; state['polymer_atoms']=0; emit('release')
                emit('exhausted'); break
            state['waste']-=1; state['fuel']+=1; state['photons']-=2; state['heat']+=1
            emit('regenerate'); continue
        if not state['polymer_atoms']:
            state['monomers']-=1; state['polymer_atoms']=1; emit('select')
        state['monomers']-=1; state['polymer_atoms']+=1; state['bonds']+=1
        state['fuel']-=2; state['waste']+=2; state['heat']+=1; joins+=1; emit('associate')
        if state['polymer_atoms']==length:
            while state['bonds']:
                state['bonds']-=1; state['heat']+=1; state['monomers']+=1; state['polymer_atoms']-=1; emit('cut')
            state['monomers']+=1; state['polymer_atoms']=0; emit('release'); cycles+=1
    return dict(length=length,completed_cycles=cycles,paid_associations=joins,events=events)


def panel():
    return dict(schema='kinetic01-budget-v1',natural_worlds=0,seed_maps_screened=0,
                cases=[trajectory(length) for length in range(2,7)])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output',required=True)
    a=p.parse_args()
    with Path(a.output).open('x',encoding='utf-8') as out: json.dump(panel(),out); out.write('\n')
