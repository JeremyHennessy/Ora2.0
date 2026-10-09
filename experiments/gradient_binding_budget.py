"""Authored GRADIENT-01 feasibility only: no natural seeds or origin evidence."""
import argparse
import json
from pathlib import Path
from experiments.gradient_binding import Surface, canon
from experiments.gradient_binding_audit import Interpreter


class Fixture:
    def __init__(self,arm='candidate'):
        self.model=Surface(91000,arm,list(range(48)))
        self.check=Interpreter(91000,arm,list(range(48)))
        self.t=8192;self.trace=[]

    def perform(self,request):
        event=self.model.perform(request,self.t)
        independent=self.check.apply(request,self.t)
        if event!=independent or canon(self.model.snapshot())!=canon(self.check.snapshot()):raise ValueError('Independent authored-state disagreement')
        self.check.conserve();self.check.measure(self.t,event)
        self.trace.append([self.t,request,event]);self.t+=1
        return event

    def fill(self,node,amount):
        while len(self.model.q[node])<amount:
            if node==0:
                event=self.perform(['capture',0,self.model.photons[0][:2]])
                if event[0]!='capture':raise ValueError('Finite local photons exhausted')
            else:
                self.fill(node-1,2)
                links=[i for i in self.model.active if self.model.bonds[i]['pair']==[node-1,node]]
                if not links:raise ValueError('No physical transport path')
                event=self.perform(['transport',links[0],node-1,node,self.model.q[node-1][:2]])
                if event[0]!='transport':raise ValueError('Inert channel cannot charge recipient')

    def bind(self,a,b):
        self.fill(a,2);event=self.perform(['bind',[a,b],a,self.model.q[a][:2]])
        if event[0]!='bind':raise ValueError('Unaffordable/impossible link')
        return event[1]

    def result(self):
        return dict(authored_geometry_and_action_sequence=True,natural_origin_evidence=False,
            trace=self.trace,endpoints=self.check.endpoints,state=self.model.snapshot())


def feasibility():
    shallow=Fixture();shallow.bind(0,1);origin=shallow.bind(1,2);shallow.bind(2,3)
    shallow.perform(['unbind',origin]);shallow.bind(1,2);shallow.bind(2,10)
    assert len(shallow.check.endpoints)==1
    used=2048-sum(map(len,shallow.model.photons.values()))
    assert used==52 and shallow.model.heat==48 and len(shallow.model.active)==4
    deep=Fixture()
    for i in range(5):deep.bind(i,i+1)
    deep.bind(5,13);link=next(i for i in deep.model.active if deep.model.bonds[i]['pair']==[4,5]);deep.perform(['unbind',link])
    try:deep.bind(4,5)
    except ValueError as error:deep_failure=str(error)
    else:raise AssertionError('Depth-five source stock unexpectedly sufficient')
    assert deep_failure=='Finite local photons exhausted' and not deep.model.photons[0]
    ghost=Fixture('ghost');ghost.bind(0,1)
    try:ghost.bind(1,2)
    except ValueError as error:ghost_failure=str(error)
    else:raise AssertionError('Ghost conveyed useful energy')
    assert ghost_failure=='Inert channel cannot charge recipient' and ghost.model.q[1]==[]
    return dict(schema='gradient01-authored-budget-v1',shallow_required_photons=52,
        deep_minimum_photons=316,deep_local_stock=256,deep_failure=deep_failure,
        inaccessible_photons=sum(map(len,deep.model.photons.values())),ghost_failure=ghost_failure,
        shallow=shallow.result(),deep=deep.result(),ghost=ghost.result(),
        natural_worlds_executed=0,life_demonstrated=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report',required=True);args=parser.parse_args()
    result=feasibility();Path(args.report).write_text(canon(result)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('shallow','deep','ghost')}))
