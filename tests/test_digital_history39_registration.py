"""Static scopes and prepared evaluator bills only; no valid World execution."""
import copy
import unittest
from pathlib import Path
from unittest.mock import patch
from experiments import digital_history39_world as world
from experiments.digital_history39_endpoint import census, contract, identities, SEEDS
from experiments.digital_history33_endpoint import MODES, REFERENCES
from experiments.digital_history34_independent import compare as independent
from tests.test_digital_history33_endpoint import fixture


def bank():
    a, r = fixture()
    return ({(i, s): copy.deepcopy(a) for i in identities() for s in SEEDS},
            {s: copy.deepcopy(r) for s in SEEDS})


class RegistrationTests(unittest.TestCase):
    def test_whole_source_sparse_identity_scope(self):
        c=contract(); m=world.manifest()
        self.assertEqual(c['candidates'],[x['path_id'] for x in m['candidates']])
        self.assertEqual(len(set(c['candidates'])),112)
        self.assertEqual(c['total_histories'],2952)
        self.assertEqual(len(world.chunks()),16)
        self.assertEqual(sum(map(len,world.chunks())),123)
        self.assertFalse(c['performance_selection'])
        self.assertEqual(c['world_histories_executed'],0)

    def test_old_and_reserved_scopes_refused_before_construction(self):
        with patch.object(world,'install',side_effect=AssertionError('must not construct')):
            for seed in (True,38100,33100,38300,38208):
                with self.assertRaises(ValueError): world.batch(seed,'intact',0)
            for mode,chunk in [('bad',0),('intact',True),('intact',16)]:
                with self.assertRaises(ValueError): world.batch(38200,mode,chunk)

    def test_exact_world_semantics_preserved(self):
        p=Path(world.__file__).parent
        old=(p/'digital_admission38_world.py').read_text()
        new=Path(world.__file__).read_text()
        self.assertEqual(old[old.index('def install():'):old.index('def batch(')],
                         new[new.index('def install():'):new.index('def batch(')])
        old=(p/'digital_admission38_interpret.py').read_text()
        new=(p/'digital_history39_interpret.py').read_text()
        self.assertEqual(new,old.replace('DIGITAL-ADMISSION-38-PAID-v1','DIGITAL-HISTORY-39-FRESH-v1')
            .replace('(38100,38101)','(38200,38201,38202,38203,38204,38205,38206,38207)'))

    def test_prepared_complete_census_independent_predicate_agrees(self):
        a,r=bank(); x=census(a,r); self.assertEqual(x,census(a,r,independent))
        self.assertEqual(x['qualified_cells'],896); self.assertEqual(x['all_eight_qualified'],112)
        self.assertFalse(x['learning']); self.assertFalse(x['stage_credit'])

    def test_missing_failed_or_extra_identity_never_disappears(self):
        a,r=bank(); del a[identities()[0],SEEDS[0]]
        with self.assertRaises(ValueError): census(a,r)
        a,r=bank(); a[31360,SEEDS[0]]=fixture()[0]
        with self.assertRaises(ValueError): census(a,r)
        a,r=bank(); del r[SEEDS[0]]
        with self.assertRaises(ValueError): census(a,r)

    def test_death_null_opportunity_and_paid_bill_failures_retained(self):
        a,r=bank(); i=identities()[0]; s=SEEDS[0]
        a[i,s]['retained_disabled'].update(completed=False,food=2,fresh=0,
            completion_tick=None,paid_work=None,terminal_tick=90)
        a[i,SEEDS[1]]['intact']['own_origins']=15
        a[i,SEEDS[2]]['intact']['paid_work']=154
        with self.assertRaises(ValueError): census(a,r)
        a[i,SEEDS[2]]['intact']['paid_work']=155
        x=census(a,r); self.assertEqual(x,census(a,r,independent))
        self.assertEqual(x['qualified_cells'],894); self.assertEqual(x['all_eight_qualified'],111)
        self.assertEqual(x['denominator_cells'],896)

    def test_one_advantage_does_not_establish_all_contexts(self):
        a,r=bank(); i=identities()[0]
        a[i,SEEDS[7]]['intact']['completion_tick']=200
        a[i,SEEDS[7]]['intact']['terminal_tick']=200
        a[i,SEEDS[7]]['intact']['paid_work']=255
        x=census(a,r); self.assertEqual(x,census(a,r,independent))
        self.assertEqual(x['all_eight_qualified'],111)
        self.assertEqual(x['qualified_cells'],895)


if __name__=='__main__': unittest.main()
