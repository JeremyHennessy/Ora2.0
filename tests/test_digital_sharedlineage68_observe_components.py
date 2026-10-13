"""Prepared observation predicates and literal replay AST only. No paid histories."""
import ast,inspect,unittest
from unittest.mock import patch
from experiments import digital_sharedlineage68_population as producer
from experiments import digital_sharedlineage68_observe as observation
from experiments import digital_sharedlineage68_interpret as full
from experiments import digital_sharedlineage68_fork_interpret as replay
from experiments.digital_sharedlineage68_transition import body,clone,h
P=dict(source_sha256='a'*64,configuration_sha256='b'*64)

def actor(identity,generation,program,births=0,food=0,censored=False):
    return dict(id=identity,generation=generation,born_program=program,births=births,food=food,censored=censored,
        birth_tick=identity,death_tick=None if censored else identity+100,turns=8,signatures=[])

class PreparedObservationComponents(unittest.TestCase):
    def setUp(self):
        self.trap=patch.object(producer.World,'__init__',side_effect=AssertionError('No World in observation fixtures'))
        self.spy=self.trap.start();self.addCleanup(self.trap.stop)
        self.addCleanup(lambda:self.assertEqual(self.spy.call_count,0))

    def test_representation_exact_all_parents(self):
        projected=dict(actors={1:actor(1,1,[4],3),2:actor(2,1,[5],1),3:actor(3,1,[6],0,censored=True)},
            births=[dict(parent=1,generation=2,newborn_program=[4]),dict(parent=1,generation=2,newborn_program=[4]),
                    dict(parent=1,generation=2,newborn_program=[5]),dict(parent=2,generation=2,newborn_program=[6])])
        result=observation.representation(projected,1)
        self.assertEqual((result['P'],result['W'],result['C']),([1,3],[3,4],[1,2]))
        self.assertEqual(result['identity'],dict(total=[1,6],weighting=[5,12],transmission=[-1,4]))
        self.assertEqual(result['censored_parent_ids'],[3]);self.assertTrue(result['positive'])

    def test_zero_offspring_undefined(self):
        result=observation.representation(dict(actors={1:actor(1,1,[4],censored=True),2:actor(2,1,[5])},births=[]),1)
        self.assertEqual(result['P'],[1,2]);self.assertFalse(result['defined']);self.assertIsNone(result['W'])
        self.assertFalse(result['positive'])

    def test_temporal_transmission_not_division_hash(self):
        program=list(range(27));actors={1:actor(1,1,program,1,1),2:actor(2,2,program,1,1),
            3:actor(3,3,program,1,1),4:actor(4,4,program)}
        edges=[dict(parent=i,child=i+1,newborn_program=program,temporally_copied_source_program=program,
                    parent_program_at_division=program) for i in (1,2,3)]
        projected=dict(actors=actors,births=edges)
        self.assertEqual(observation.transmission(projected,1)['exact_paid_chains'],[[1,2,3]])
        edges[0]['temporally_copied_source_program']=[31]+program[1:]
        self.assertFalse(observation.transmission(projected,1)['positive'])
        edges[0]['temporally_copied_source_program']=program;actors[3]['births']=0
        self.assertFalse(observation.transmission(projected,1)['positive'])

    def test_strategy_requires_shared_action_difference(self):
        a=actor(1,1,[1],2,3);b=actor(1,1,[0],1,2)
        a['signatures']=[['ACT',0,1],['MOVE',1]];b['signatures']=[['ACT',0,1]]
        result=observation.contrast(a,b,True);self.assertTrue(result['conditional_useful_program'])
        self.assertFalse(result['new_resource_strategy'])
        b['signatures'][0]=['ACT',0,0]
        self.assertTrue(observation.contrast(a,b,True)['new_resource_strategy'])
        a['censored']=True;self.assertFalse(observation.contrast(a,b,True)['conditional_useful_program'])
        a['censored']=False;self.assertFalse(observation.contrast(a,b,False)['new_resource_strategy'])

    def test_actual_material_refusal_predicates(self):
        bodies={};cursor=0
        for identity in range(8):
            code=[[0,cursor+i] for i in range(27)];cursor+=27
            units=list(range(cursor,cursor+16));cursor+=16
            entity=body(identity,None,0,code,units,0);entity['energy']=8
            entity['nursery']=[dict(unit=cursor+i) for i in range(21)];cursor+=21
            bodies[str(identity)]=entity
        self.assertEqual(cursor,512)
        before=dict(entities=bodies,free=[],tick=44)
        event=dict(actor=0,tick=44,decoded=[10,0,0],outcome='copy_refused',state_hash='a'*64)
        obs=observation.Observation();obs._competition(before,event,bodies['0'])
        self.assertEqual(len(obs.competition),1)
        self.assertEqual(obs.competition[0]['free_units'],0)
        ownership=obs.ownership[obs.competition[0]['ownership_hash']]
        self.assertEqual(sum(len(v) for owner in ownership.values() for v in owner.values()),512)
        bodies['0']['energy']=3;obs._competition(before,event,bodies['0'])
        self.assertEqual(len(obs.competition),1)
        # A stock-cap rejection or several living actors adds no material witness.
        event['outcome']='executed';obs._competition(before,event,bodies['0'])
        self.assertEqual(len(obs.competition),1)

    def test_observation_hooks_preserve_literal_vm_ast(self):
        baseline=ast.parse(inspect.getsource(full.audit)).body[0]
        candidate=ast.parse(inspect.getsource(replay.audit_history)).body[0]
        candidate.name=baseline.name;candidate.args=baseline.args
        class RemoveHooks(ast.NodeTransformer):
            def visit_If(self,node):
                if ast.unparse(node.test).startswith(('observations is not None','binding is not None')):return None
                return self.generic_visit(node)
        candidate=RemoveHooks().visit(candidate)
        self.assertEqual(ast.dump(candidate),ast.dump(baseline))

    def test_full_replay_before_projection(self):
        with (patch.object(full,'audit',side_effect=AssertionError('Full refusal')) as audit,
              patch.object(replay,'audit_history') as secondary):
            with self.assertRaisesRegex(AssertionError,'Full refusal'):observation.audit_row({},P)
            self.assertEqual(audit.call_count,1);secondary.assert_not_called()

    def test_terminal_move_and_complete_state_hash(self):
        code=[[0,i] for i in range(27)];code[0][0]=13
        born=body(0,None,0,code,list(range(27,43)),0);before=dict(entities={0:born},tick=1,free=list(range(43,512)))
        terminal=clone(born);terminal.update(pos=3,energy=0,pc=1)
        after=dict(entities={},turns={0:1},tick=1)
        event=dict(actor=0,tick=1,decoded=[13,0,0],before=h(born),state_hash=h(after),outcome='executed',death=list(range(43)))
        obs=observation.Observation();obs.before(before,event['decoded']);obs.after(after,event,terminal)
        proof=obs.finish(after,dict(turns={0:1},ticks=1,successful_food=0,births=0,deaths=1))
        actual=proof['actors']['0'];self.assertEqual(actual['signatures'],[['MOVE',3]])
        self.assertEqual(actual['end_state_hash'],h(terminal));self.assertFalse(actual['censored'])
        actual['death_tick']=None;actual['censored']=True;actual['birth_tick']=0
        other=dict(actual,id=1,born_program=[1],birth_tick=1,turns=8)
        actual['id']=2;actual['turns']=8;proof['actors']={'1':other,'2':actual};proof['endpoint_tick']=10
        self.assertEqual(observation.overlapping_programs(proof),[[1,2]])

if __name__=='__main__':unittest.main()
