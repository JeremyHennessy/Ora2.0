"""Prepared boundary witnesses: constructor trapped, no population histories."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch
from experiments import digital_sharedlineage68_population as producer
from experiments import digital_sharedlineage68_transition as shared
from experiments import digital_sharedlineage68_fork_interpret as referee
from test_digital_sharedlineage68_transition_components import prepared,PROVENANCE


class IndependentBoundary(unittest.TestCase):
    def setUp(self):
        trap=patch.object(producer.World,'__init__',side_effect=AssertionError('No World'))
        self.spy=trap.start();self.addCleanup(trap.stop)
        self.addCleanup(lambda:self.assertEqual(self.spy.call_count,0))

    def test_shared_helper_unavailable_and_valid_parity(self):
        for role in ('sham','ancestor_value_control'):
            state,slot=prepared()
            expected=shared.transition(state,slot,'c'*64,role,PROVENANCE)
            with patch.object(shared,'transition',side_effect=AssertionError('Shared helper forbidden')):
                self.assertEqual(referee.transition(state,slot,'c'*64,role,PROVENANCE),expected)
        tree=ast.parse(Path(referee.__file__).read_text(encoding='utf-8'))
        imports=[n for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        self.assertFalse(any(a.name in ('transition','validate_transition') for n in imports for a in n.names))

    def test_common_helper_corruption_is_rejected(self):
        original=shared.transition
        for corruption in ('energy','unit','value','scheduler','resource'):
            state,slot=prepared()
            def corrupted(*args):
                after,record=original(*args)
                child=shared.actor_record(after['entities'],slot['target'])
                if corruption=='energy':child['energy']+=1
                if corruption=='unit':child['code'][0][1]+=1
                if corruption=='value':child['code'][0][0]=(child['code'][0][0]+1)%32
                if corruption=='scheduler':after['last']=1
                if corruption=='resource':after['free']=[]
                record.update(after_hash=shared.h(after),after_code=shared.clone(child['code']))
                return after,record
            with patch.object(shared,'transition',side_effect=corrupted):
                bad_after,bad_record=shared.transition(state,slot,'c'*64,'ancestor_value_control',PROVENANCE)
                # Demonstrate the original common-helper self-check accepts it.
                self.assertTrue(shared.validate_transition(state,bad_after,bad_record,slot,'c'*64,'ancestor_value_control',PROVENANCE))
                after,record=referee.transition(state,slot,'c'*64,'ancestor_value_control',PROVENANCE)
                with self.assertRaises(AssertionError):
                    assert bad_record==record and bad_after==after

    def test_independent_cold_start_and_identity_refusals(self):
        for key,value in [('energy',13),('memory',[1]*8),('pc',1),('registers',[1,0]),('inbox',0),('nursery',[{}])]:
            state,slot=prepared();state['entities'][1][key]=value
            slot['post_step_hash']=shared.h({k:v for k,v in state.items() if k!='events'})
            with self.assertRaises(AssertionError):referee.transition(state,slot,'c'*64,'sham',PROVENANCE)
        for mapping in [{'01':{}},{True:{}},{1:{},'1':{}}]:
            state,slot=prepared();state['entities']=mapping
            with self.assertRaises(AssertionError):referee.transition(state,slot,'c'*64,'sham',PROVENANCE)

    def test_independent_temporal_and_provenance_refusals(self):
        for key,value in [('source_value',32),('mutation_draw',True),('mutation_draw',0),('tick',40),('unit',True),('mutated',0)]:
            state,slot=prepared();slot['certificates'][0][key]=value
            with self.assertRaises(AssertionError):referee.transition(state,slot,'c'*64,'sham',PROVENANCE)
        state,slot=prepared()
        with self.assertRaises(AssertionError):referee.transition(state,slot,'c'*64,'sham',dict(PROVENANCE,source_sha256='A'*64))

    def test_post_expiration_boundary_and_all_other_fields(self):
        state,slot=prepared();state.update(food={'1':[2,3]},next_id=2,occupied=[100,101])
        slot['post_step_hash']=shared.h({k:v for k,v in state.items() if k!='events'})
        after,record=referee.transition(state,slot,'c'*64,'ancestor_value_control',PROVENANCE)
        unchanged=shared.clone(after)
        shared.actor_record(unchanged['entities'],1)['code']=shared.clone(slot['born_code'])
        self.assertEqual(unchanged,shared.clone(state))
        for key,value in [('tick',41),('heat',201),('free',[]),('expiry_records',[])]:
            bad=shared.clone(state);bad[key]=value
            with self.assertRaises(AssertionError):referee.transition(bad,slot,'c'*64,'sham',PROVENANCE)


if __name__=='__main__':unittest.main()
