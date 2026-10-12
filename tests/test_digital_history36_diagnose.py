"""Prepared local instruction traces, not scientific World histories."""
import copy
import unittest
from experiments import digital_history36_diagnose as f
from experiments import digital_history36_independent as independent
from experiments.digital_pc_controls31 import Control,step

def prepared(code,mode='intact',ticks=None,real=True,success=0):
    ticks=len(code) if ticks is None else ticks
    state=dict(r=[0,0],m=[0]*8,pc=0,feedback=0);control=Control(code,state,mode,33100);es=[];origin=None;packet=0
    for tick in range(1,ticks+1):
        before=copy.deepcopy(state);decoded=code[state['pc']][:];op,a,b=decoded
        native=step(code,state,success if op==6 and real else 0);state,ann=control.apply(before,native)
        ann['personal_read']=dict(own_source_tick=origin,original=native['r'][a%2],value=state['r'][a%2]) if op==1 else None
        e=dict(tick=tick,actor=0,decoded=decoded,control=ann,after=dict(registers=state['r'][:],memory=state['m'][:],pc=state['pc'],feedback=state['feedback']))
        if op==6:
            e['feedback']=state['feedback'];origin=tick if real else None
            if real:
                e['attempt']=dict(packet=packet,port=before['r'][a%2]%2,success=state['feedback'])
                if state['feedback']:packet+=1
        es.append(e)
    return dict(genesis_program=code,control_mode=mode,final=dict(events=es))

class DiagnosisTests(unittest.TestCase):
    def both(self,row):
        result=f.diagnose(row);self.assertEqual(result,independent.diagnose(row));return result['reads']

    def test_immediate_action_is_local_use_not_learning(self):
        row=prepared([[6,0,0],[1,0,0],[6,0,0]])
        r=self.both(row)[0];self.assertEqual((r['origin_tick'],r['first_effect'],r['effect_tick']),(1,'ACT_port',3));self.assertTrue(r['real_opportunity'])
        self.assertFalse(f.diagnose(row)['learning'])

    def test_overwrite_and_self_xor_cancel(self):
        for middle in ([4,0,7],[5,0,0]):
            r=self.both(prepared([[1,0,0],middle,[6,0,0]]))[0];self.assertEqual(r['first_effect'],'none')

    def test_memory_and_other_register_carry(self):
        r=self.both(prepared([[1,1,0],[3,7,1],[4,1,0],[2,0,7],[6,0,0]]))[0]
        self.assertEqual((r['first_effect'],r['effect_tick']),('ACT_port',5))

    def test_branch_same_successor_is_not_effect(self):
        self.assertEqual(self.both(prepared([[1,0,0],[8,0,2],[6,0,0]]))[0]['first_effect'],'ACT_port')
        r=self.both(prepared([[1,0,0],[8,0,3],[18,0,0],[18,0,0]]))[0];self.assertEqual((r['first_effect'],r['effect_tick']),('JZ_successor',2))

    def test_zero_predicate_insensitive_when_high_bits_present(self):
        r=self.both(prepared([[4,1,2],[1,0,0],[5,0,1],[8,0,5],[18,0,0],[18,0,0]]))[0];self.assertEqual(r['first_effect'],'none')

    def test_later_read_overwrites_and_sources_are_distinct(self):
        rs=self.both(prepared([[1,0,0],[1,0,0],[6,0,0]]));self.assertEqual([x['first_effect'] for x in rs],['none','ACT_port'])

    def test_empty_action_effect_is_not_resource_opportunity(self):
        r=self.both(prepared([[1,0,0],[6,0,0]],real=False))[0];self.assertEqual(r['first_effect'],'ACT_port');self.assertFalse(r['real_opportunity']);self.assertEqual(r['source'],'initial_or_empty')

    def test_retention_reset_clears_delayed_memory(self):
        code=[[1,0,0],[3,0,0],[4,0,0],[6,0,0],[2,0,0],[6,0,0]]
        self.assertEqual(self.both(prepared(code))[0]['effect_tick'],6)
        self.assertEqual(self.both(prepared(code,'retained_disabled'))[0]['first_effect'],'none')

    def test_unrelated_delivery_never_becomes_own(self):
        r=self.both(prepared([[6,0,0],[1,0,0],[6,0,0]],'own_disrupted'))[0];self.assertEqual(r['source'],'unrelated');self.assertFalse(r['post_change_own'])

    def test_cutoff_and_death_keep_reads_explicit(self):
        code=[[6,0,0],[1,0,0],[7,0,0]];row=prepared(code,ticks=96,success=1)
        rs=self.both(row);self.assertFalse(rs[-1]['read_before_completion']);self.assertIsNone(rs[-1]['effect_tick'])
        row['final']['events'][-1]['death']='prepared';self.both(row)

    def test_malformed_transition_refused(self):
        row=prepared([[1,0,0],[6,0,0]]);row['final']['events'][0]['after']['registers'][0]=1
        for impl in (f,independent):
            with self.assertRaises(ValueError):impl.diagnose(row)

if __name__=='__main__':unittest.main()
