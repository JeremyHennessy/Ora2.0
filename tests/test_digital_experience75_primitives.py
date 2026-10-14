"""Software admission only; no valid World or scientific target queried."""
import copy,unittest
from unittest.mock import patch
from experiments import digital_experience75_source as source,digital_experience75_controls as controls,digital_experience75_world as world

def state():return dict(r=[0,0],m=list(range(8)),pc=0,feedback=0)
class Primitives(unittest.TestCase):
    def test_indirect_load_uses_bounded_register_address(self):
        s=state();s['r']=[0,15]
        result=controls.step([[19,0,1]],s)
        self.assertEqual(result['r'],[7,15]);self.assertEqual(s['r'],[0,15])
    def test_indirect_store_does_not_write_outside_eight_cells(self):
        s=state();s['r']=[15,12]
        result=controls.step([[20,0,1]],s)
        self.assertEqual(result['m'],list(range(7))+[12]);self.assertEqual(s['m'],list(range(8)))
    def test_sensor_uses_prepared_current_input(self):
        for cue in (0,1):self.assertEqual(controls.step([[0,1,0]],state(),current_cue=cue)['r'][1],cue)
        for cue in (True,2,-1):
            with self.assertRaises(ValueError):controls.step([[0,1,0]],state(),current_cue=cue)
    def test_retention_cut_erases_saved_feedback_without_erasing_native_latch(self):
        code=[[1,0,0],[3,0,0],[6,0,0]];s=state();s['m']=[0]*8;s['feedback']=1
        c=controls.Control(code,s,'retained_disabled',3)
        for _ in range(3):
            before=copy.deepcopy(s);native=controls.step(code,s,act_feedback=1);s,annotation=c.apply(before,native)
        self.assertEqual(s['m'][0],0);self.assertEqual(s['r'][0],0);self.assertEqual(s['feedback'],1)
        self.assertTrue(annotation['rewrites'])
    def test_unrelated_feedback_is_logged_and_never_relabels_native_feedback(self):
        code=[[1,0,0]];s=state();s['feedback']=1
        c=controls.Control(code,s,'own_disrupted',3);native=controls.step(code,s)
        result,annotation=c.apply(s,native)
        self.assertEqual(native['r'][0],1);self.assertEqual(result['feedback'],1)
        self.assertEqual(annotation['substitution']['original'],1)
        self.assertIn(annotation['substitution']['value'],(0,1))
    def test_sensor_reaches_zero_feedback_shadow(self):
        code=[[0,1,0],[6,1,0]];s=state();c=controls.Control(code,s,'retained_disabled',3)
        for _ in range(2):
            before=copy.deepcopy(s);native=controls.step(code,s,act_feedback=0,current_cue=1);s,_=c.apply(before,native,current_cue=1)
        self.assertEqual(s['r'][1],1)
    def test_bad_words_and_states_never_address_host_data(self):
        for code in ([[21,0,0]],[[19,0,True]],[[20,-1,0]]):
            with self.assertRaises(ValueError):controls.step(code,state())
        s=state();s['r'][0]=16
        with self.assertRaises(ValueError):controls.step([[20,0,1]],s)
    def test_complete_neutral_source_is_reproducible_without_targets(self):
        a=source.manifest();self.assertEqual(a,source.manifest())
        self.assertEqual([x['sample_id'] for x in a['candidates']],list(range(16)))
        self.assertFalse(a['performance_selection']);self.assertEqual(a['targets_queried'],0)
        for row in a['candidates']:
            self.assertEqual(len(row['draws']),27);self.assertEqual(row['program'][:5],source.PREFIX)
            self.assertEqual(len(row['program']),14);self.assertIsNone(row['parent'])
            self.assertEqual(source.digest(row['program']),row['program_sha256'])
    def test_nonregistered_and_reserved_seeds_refused_before_context_generation(self):
        with patch.object(world,'h',side_effect=RuntimeError('context query reached')):
            for seed in (True,-1,1,75100,75107,75300,75307,75008):
                with self.assertRaises(AssertionError):world.World(seed)
    def test_all_references_have_equal_paid_formation_without_chosen_mapping(self):
        refs=source.references();self.assertEqual(tuple(refs),source.REFERENCES)
        for code in refs.values():
            self.assertEqual(len(code),14);self.assertEqual(code[:5],source.PREFIX)
            self.assertEqual(3*len(code)+16,58)
            self.assertTrue(all(row[0] in source.OPS for row in code))
    def test_paid_cold_fixture_conserves_energy_in_both_prepared_orientations(self):
        for outcomes in ((0,1),(1,0)):
            energy=12;heat=58;constructor=70;packets=64;index=0;s=state();s['m']=[0]*8
            for triple in source.PREFIX:
                energy-=1;heat+=1;fb=0
                if triple[0]==6:
                    fb=outcomes[index];index+=1
                    if fb:
                        gain=min(20,64-energy);energy+=gain;heat+=20-gain;packets-=1
                    else:
                        debit=min(4,energy);energy-=debit;heat+=debit
                s['pc']=0;s=controls.step([triple],s,act_feedback=fb)
                self.assertEqual(energy+heat+constructor+20*packets,1420)
            self.assertEqual((energy,heat,constructor,packets),(23,67,70,63))

if __name__=='__main__':unittest.main()
