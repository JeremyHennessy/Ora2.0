import copy,unittest
from experiments.digital_pc_controls31 import Control,PROGRAMS,fixture,panel,step
from experiments.digital_pc_controls31_audit import audit

class PcControlTests(unittest.TestCase):
    def test_independent_complete_prepared_panel(self):
        result=audit(panel());self.assertEqual(result['prepared_instruction_transitions'],576);self.assertGreater(result['pc_rewrites'],0);self.assertGreater(result['memory_rewrites'],0)
    def test_both_native_branch_paths(self):
        for bit,expected in ((0,4),(1,2)):
            state=dict(r=[0,0],m=[0]*8,pc=0,feedback=bit)
            state=step(PROGRAMS['branch'],state);state=step(PROGRAMS['branch'],state)
            self.assertEqual(state['pc'],expected)
    def test_pc_rewrite_keeps_truthful_latest_latch(self):
        rows=fixture('branch','retained_disabled',1)['events'];changed=[e for e in rows if any(x['channel']=='pc' for x in e['control']['rewrites'])]
        self.assertTrue(changed)
        for e in changed:self.assertEqual(e['after']['feedback'],e['native_after']['feedback'])
    def test_memory_retained_until_next_action_then_erased(self):
        events=fixture('memory','retained_disabled',1)['events'];self.assertEqual(events[1]['after']['m'][2],1);self.assertEqual(events[3]['after']['m'][2],0)
    def test_no_feedback_conditional_clock_unchanged_across_controls(self):
        for fb in (0,1):
            histories=[[e['after'] for e in fixture('no_feedback',m,fb)['events']] for m in ('intact','retained_disabled','own_disrupted')]
            self.assertEqual(histories[0],histories[1]);self.assertEqual(histories[0],histories[2])
    def test_unsupported_channels_and_malformed_state_refused(self):
        state=dict(r=[0,0],m=[0]*8,pc=0,feedback=0)
        for code in ([[9,0,0]],[[15,0,0]],[[True,0,0]]):
            with self.assertRaises(ValueError):Control(code,state,'intact',31000)
        bad=copy.deepcopy(state);bad['pc']=True
        with self.assertRaises(ValueError):Control(PROGRAMS['branch'],bad,'intact',31000)
    def test_omitted_or_corrupt_pc_reconstruction_refused(self):
        data=panel();data['fixtures'].pop()
        with self.assertRaises(AssertionError):audit(data)
        data=panel();data['fixtures'][0]['events'][1]['after']['pc']=0
        with self.assertRaises(AssertionError):audit(data)
