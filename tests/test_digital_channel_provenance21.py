import unittest
from experiments.digital_channel_provenance21 import trace_events
from experiments.digital_channel_provenance21_audit import reconstruct

def event(tick,op,a=0,b=0,hit=None):
    e=dict(tick=tick,actor=0,decoded=[op,a,b])
    if hit is not None:e['attempt']=dict(packet=0,success=hit)
    return e

class ChannelProvenance21(unittest.TestCase):
    def checked(self,events):
        t=trace_events(events);self.assertEqual(t,reconstruct(events));return t['trace']
    def test_empty_act_clears_source_but_actual_zero_is_personal(self):
        t=self.checked([event(1,1),event(2,6,hit=0),event(3,1),event(4,6),event(5,1)])
        self.assertEqual([t[i]['feedback_read_cause'] for i in (0,2,4)],['initial_supplied','actual_own_attempt','empty_act_reset'])
        self.assertEqual(t[2]['feedback_read_origins'],[2]);self.assertEqual(t[4]['feedback_read_origins'],[])
    def test_branch_pc_can_carry_history_without_a_memory_write(self):
        t=self.checked([event(1,6,hit=1),event(2,1),event(3,8),event(4,4),event(5,6)])
        self.assertFalse(any(t[-1]['memory']));self.assertEqual(t[-1]['action_possible_origins'],[1])
        self.assertEqual(t[3]['registers'][0],[1]);self.assertEqual(t[3]['pc_possible_origins'],[1])
    def test_fixed_clock_memory_is_not_experience_and_repeated_latch_is_one_origin(self):
        t=self.checked([event(1,4,b=1),event(2,3,a=1),event(3,2,b=1),event(4,6,hit=1),event(5,1),event(6,1)])
        self.assertEqual(t[3]['action_possible_origins'],[]);self.assertFalse(any(t[2]['memory']))
        self.assertEqual(t[4]['feedback_read_origins'],t[5]['feedback_read_origins']);self.assertEqual(t[5]['feedback_read_origins'],[4])
