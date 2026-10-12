import unittest
from unittest.mock import patch
from copy import deepcopy
from experiments.digital_function53 import scan,founder,diagnose


class FunctionFixtures(unittest.TestCase):
    def event(self,op=6,energy=12,death=False,attempt=None):
        program=[[op,0,0]];s=founder(program);s['energy']=energy
        e=dict(tick=1,actor=0,decoded=deepcopy(program[0]),outcome='executed')
        after=deepcopy(s);after['energy']-=1
        if op==13:after['pos']=3
        if death:e['death']=list(range(19))
        else:e['after']=after
        if attempt is not None:e['attempt']=attempt
        return program,e
    def test_empty_is_not_failed(self):
        p,e=self.event();c=scan([e],p)['counts'];self.assertEqual(c['empty_actions'],1);self.assertNotIn('failed_attempts',c)
    def test_failed_has_personal_opportunity(self):
        p,e=self.event(attempt=dict(position=0,success=0));c=scan([e],p)['counts'];self.assertEqual(c['failed_attempts'],1);self.assertEqual(c['available_actions'],1)
    def test_food_is_separate(self):
        p,e=self.event(attempt=dict(position=0,success=1));self.assertEqual(scan([e],p)['counts']['food'],1)
    def test_move_on_terminal_step_counts(self):
        p,e=self.event(13,death=True);r=scan([e],p);self.assertEqual(r['actors'][0]['visited_positions'],[0,3]);self.assertEqual(r['counts']['moves'],1)
    def test_birth_move_is_not_remote_resource_access(self):
        p,e=self.event(13);r=scan([e],p);self.assertEqual(r['counts']['actors_with_birth_move'],1);self.assertEqual(r['counts']['actors_visiting_resource_sites'],0)
    def test_decoded_mismatch_refused(self):
        p,e=self.event();e['decoded'][0]=13
        with self.assertRaises(AssertionError):scan([e],p)
    def test_boolean_opcode_refused(self):
        p,e=self.event();e['decoded'][0]=True
        with self.assertRaises(AssertionError):scan([e],p)
    def test_noop_self_write_disclosed(self):
        p,e=self.event(9);e['self_write']=dict(old=9,value=9);self.assertEqual(scan([e],p)['actors'][0]['self_writes'],1)
    def test_paid_mutation_without_birth_is_not_transmission(self):
        p,e=self.event(10);e['writes']=[dict(write_id=0,mutated=True,index=0,value=13)];c=scan([e],p)['counts'];self.assertEqual(c['mutations_not_reaching_birth'],1);self.assertNotIn('mutations_reaching_birth',c)
    def test_refusals_may_overlap(self):
        p,e=self.event(12);e['outcome']='division_refused';c=scan([e],p)['counts'];self.assertEqual(c['division_energy_refusals'],1);self.assertEqual(c['division_incomplete_refusals'],1)
    def test_established_referee_food_schema(self):
        p,e=self.event(attempt=dict(position=0,success=1))
        row=dict(seed=52000,mode='faithful',genesis_program=p,final=dict(events=[e]))
        checked=dict(births=0,deaths=0,successful_food=1,remote_food=0,paid_copy_words=0,mutations=0)
        with patch('experiments.digital_function53.interpret',return_value=dict(checked=checked)):
            self.assertEqual(diagnose(row)['diagnosis']['counts']['food'],1)
