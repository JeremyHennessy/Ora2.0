import copy,unittest
from experiments.digital_pc31_world import batch,programmes,World
from experiments.digital_pc31_paid import endpoint
from experiments.digital_pc31_world_reconstruct import update

def prepared_endpoint(complete=False):
    events=[dict(tick=i,actor=0,decoded=[6,0,0],attempt=dict(packet=i-1,success=1),after=dict(energy=64)) for i in range(1,33)] if complete else [dict(tick=1,actor=0,decoded=[8,0,0],death=[])]
    return dict(genesis_program=[[8,0,0]],final=dict(events=events),control_mode='intact')

class PaidPcTests(unittest.TestCase):
    def test_registered_source_scope_and_no_feedback_clock(self):
        codes=programmes();self.assertEqual(len(codes),5);self.assertEqual(codes['conditional_clock'][:5],codes['affine3'][:5]);self.assertEqual(codes['conditional_clock'][6],[8,1,5])
        self.assertTrue(all(x[0] in (1,2,3,4,5,6,7,8,18) for c in codes.values() for x in c));self.assertFalse(any(x[0]==1 for x in codes['conditional_clock']))
    def test_unregistered_batches_refused_before_world(self):
        for seed,mode in ((True,'intact'),(31102,'intact'),(31100,'other')):
            with self.assertRaises(ValueError):batch(seed,mode)
        with self.assertRaises(AssertionError):World(31100,'mutating','missing')
    def test_failed_short_history_keeps_null_paid_completion(self):
        x=endpoint(prepared_endpoint());self.assertFalse(x['completed']);self.assertIsNone(x['paid_work_to_completion']);self.assertEqual(x['death_tick'],1)
    def test_jz_scope_pays_formation_and_all_instruction_work(self):
        x=endpoint(prepared_endpoint(True));self.assertTrue(x['completed']);self.assertEqual(x['paid_work_to_completion'],19+32);self.assertEqual(x['startup_endowment'],12);self.assertEqual(x['cap_loss_to_completion'],556)
    def test_duplicate_acquisition_refused(self):
        row=prepared_endpoint(True);row['final']['events'][1]['attempt']['packet']=0
        with self.assertRaises(AssertionError):endpoint(row)
    def test_code_write_and_inbox_genotypes_not_silently_scored(self):
        for op in (9,15):
            row=prepared_endpoint();row['genesis_program']=[[op,0,0]]
            with self.assertRaises(AssertionError):endpoint(row)
    def test_independent_actual_origin_and_latch_reset_metadata(self):
        program=[[1,0,0],[6,0,0]];aux=dict(program=program,shadow=dict(r=[0,0],m=[0]*8,pc=0,feedback=0),origin=4,reads=0,epoch=0)
        entity=dict(registers=[1,0],memory=[0]*8,pc=1,feedback=1)
        a=update(aux,entity,dict(decoded=[1,0,0],tick=5),'intact',31100);self.assertEqual(a['personal_read'],dict(read_index=1,own_source_tick=4,original=1,value=1))
        entity.update(pc=0,feedback=0);a=update(aux,entity,dict(decoded=[6,0,0],tick=6),'retained_disabled',31100);self.assertIsNone(a['latest_own_source_tick']);self.assertEqual(entity['feedback'],0);self.assertEqual(entity['registers'][0],0)
