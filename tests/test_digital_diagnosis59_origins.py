"""Prepared normalized views only; no authentic history or World execution."""
import unittest
from unittest.mock import patch
from experiments.digital_diagnosis59_origins import trace as direct
from experiments.digital_diagnosis59_origins_independent import trace as independent

SELECTED=(direct,independent)
SEMANTICS={}


def event(t,op,a=0,b=0,actor=0,**fields):
    return dict(tick=t,actor=actor,decoded=[op,a,b],pc_before=0,**fields)


def experience():return [event(1,6,packet_present=True),event(2,1)]


def family():
    return experience()+[event(3,10,writes=[dict(index=i) for i in range(3)]),event(4,12,birth=1)]


class OriginKernelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trap=patch('experiments.digital_informative_exposure23.World.__init__',side_effect=AssertionError('World forbidden'))
        cls.trap.start()

    @classmethod
    def tearDownClass(cls):
        import json
        cls.trap.stop()
        print('\nSEMANTICS:'+json.dumps(SEMANTICS,sort_keys=True,separators=(',',':')),flush=True)

    def check(self,views):
        results=[f(views,3) for f in SELECTED]
        for r in results:
            self.assertFalse(r['learning']);self.assertFalse(r['stage_credit']);self.assertEqual(r['causal_effect'],'UNKNOWN')
        if len(results)>1:self.assertEqual(results[0],results[1])
        SEMANTICS.setdefault(self._testMethodName,[]).append(results[0])
        return results[0]

    def refused(self,views):
        for f in SELECTED:
            with self.assertRaises((AssertionError,KeyError)):f(views,3)
        SEMANTICS.setdefault(self._testMethodName,[]).append('REFUSED')

    def test_01_empty_act_not_personal(self):
        r=self.check([event(1,6,packet_present=False),event(2,1)]);self.assertEqual(r['records'][1]['read'],[])

    def test_02_real_failed_trial_has_origin(self):
        r=self.check(experience());self.assertEqual(r['records'][1]['read'],[[0,1]])

    def test_03_empty_act_replaces_latch(self):
        r=self.check(experience()+[event(3,6,packet_present=False),event(4,1,a=1)])
        self.assertEqual(r['actors']['0']['registers'],[[[0,1]],[]])

    def test_04_older_register_survives_new_trial(self):
        r=self.check(experience()+[event(3,6,packet_present=True)]);self.assertEqual(r['actors']['0']['registers'][0],[[0,1]])

    def test_05_const_overwrites_register(self):
        r=self.check(experience()+[event(3,4)]);self.assertEqual(r['actors']['0']['registers'][0],[])

    def test_06_xor_is_conservative_even_cancellation(self):
        r=self.check(experience()+[event(3,5)]);self.assertEqual(r['actors']['0']['registers'][0],[[0,1]])

    def test_07_memory_retains_old_feedback(self):
        r=self.check(experience()+[event(3,3),event(4,4),event(5,2,a=1)])
        self.assertEqual(r['actors']['0']['registers'][1],[[0,1]])

    def test_08_memory_replacement(self):
        r=self.check(experience()+[event(3,3),event(4,4),event(5,3),event(6,2)])
        self.assertEqual(r['actors']['0']['memory'][0],[])

    def test_09_conditional_pc_is_conservative(self):
        r=self.check(experience()+[event(3,8)]);self.assertEqual(r['actors']['0']['pc'],[[0,1]])

    def test_10_move_and_sense_position_channel(self):
        r=self.check(experience()+[event(3,13),event(4,0,a=1)])
        self.assertEqual(r['actors']['0']['cue'],[[0,1]]);self.assertEqual(r['actors']['0']['registers'][1],[[0,1]])

    def test_11_code_written_from_feedback(self):
        r=self.check(experience()+[event(3,9,self_write=dict(index=2,old=0,value=1))])
        self.assertEqual(r['actors']['0']['code'][2],[[0,1]])

    def test_12_noop_write_not_causal_effect(self):
        r=self.check(experience()+[event(3,9,self_write=dict(index=2,old=1,value=1))]);self.assertEqual(r['causal_effect'],'UNKNOWN')

    def test_13_code_origin_replacement(self):
        r=self.check(experience()+[event(3,9,self_write=dict(index=2,old=0,value=1)),event(4,4,a=1),event(5,9,a=1,self_write=dict(index=2,old=1,value=0))])
        # Decoded instruction itself is now history-dependent; clearing a value is not proof of removed dependence.
        self.assertEqual(r['actors']['0']['code'][2],[[0,1]])

    def test_14_copy_transmits_foreign_code_origin(self):
        v=experience()+[event(3,9,self_write=dict(index=2,old=0,value=1)),event(4,10,writes=[dict(index=i) for i in range(3)]),event(5,12,birth=1)]
        r=self.check(v);self.assertEqual(r['actors']['1']['code'][2],[[0,1]])

    def test_15_birth_resets_feedback_memory_registers(self):
        r=self.check(family());c=r['actors']['1'];self.assertEqual(c['registers'],[[],[]]);self.assertEqual(c['memory'],[[]]*8);self.assertEqual(c['feedback'],[])

    def test_16_message_foreign_origin(self):
        r=self.check(family()+[event(5,14,message=1)]);self.assertEqual(r['actors']['1']['inbox'],[[0,1]])

    def test_17_receive_clears_inbox(self):
        r=self.check(family()+[event(5,14,message=1),event(6,15,actor=1)]);self.assertIsNone(r['actors']['1']['inbox']);self.assertEqual(r['actors']['1']['registers'][0],[[0,1]])

    def test_18_empty_receive_preserves_register(self):
        r=self.check(experience()+[event(3,15)]);self.assertEqual(r['actors']['0']['registers'][0],[[0,1]])

    def test_19_death_preserves_denominator_and_refuses_later(self):
        r=self.check([event(1,17,death=True)]);self.assertFalse(r['actors']['0']['alive']);self.refused([event(1,17,death=True),event(2,0)])

    def test_20_duplicate_tick_refused(self):self.refused([event(1,0),event(1,0)])

    def test_21_unknown_actor_refused(self):self.refused([event(1,0,actor=1)])

    def test_22_invalid_pc_refused(self):
        e=event(1,0);e['pc_before']=1;self.refused([e])

    def test_23_incomplete_birth_refused(self):self.refused([event(1,12,birth=1)])

    def test_24_duplicate_copy_index_refused(self):self.refused([event(1,10,writes=[dict(index=0),dict(index=0)])])


if __name__=='__main__':
    import sys
    if len(sys.argv)==2:
        SELECTED=(direct,) if sys.argv.pop()=='direct' else (independent,)
    unittest.main()
