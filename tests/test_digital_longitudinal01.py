"""Prospective short software equivalence/refusal checks; no scientific sample."""
import ast
import copy
from pathlib import Path
import unittest
from unittest.mock import patch
from experiments import digital_pressure71_population as unchanged
from experiments import digital_longitudinal01_population as candidate
from experiments import digital_longitudinal01_referee as literal

class Longitudinal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(unchanged.World,'run',side_effect=AssertionError('closed run must not be borrowed')):
            cls.rows={seed:candidate.history(seed,horizon=h) for seed,h in [(3,128),(4,256)]}
    def test_short_whole_state_equivalence(self):
        for seed,row in self.rows.items():
            w=unchanged.World(seed,'faithful','ancestor','renewed','parent_copy',dose=8)
            final=w.run(row['horizon'])
            self.assertEqual(final,row['final'])
            proof=literal.audit(row)
            self.assertEqual((proof['ticks'],proof['births'],proof['deaths']),
                             (final['tick'],final['births'],final['deaths']))
    def test_closed_interface_still_refuses_long_probe(self):
        with self.assertRaises(AssertionError):unchanged.history(3,horizon=8192,software_only=True)
        for seed,h in [(1,128),(True,128),(3,63),(3,8193),(3,True)]:
            with self.assertRaises(AssertionError):candidate.history(seed,horizon=h)
    def test_prospective_inflow_bound_and_unchanged_bill(self):
        for tick in (4096,4160,8192):
            w=candidate.World(3,'faithful','ancestor','renewed','parent_copy',dose=8)
            old=unchanged.World(3,'faithful','ancestor','renewed','parent_copy',dose=8)
            w.tick=tick;old.tick=4096  # Authored input witnesses, not histories.
            offers=w.input();self.assertEqual(offers,old.input())
            self.assertEqual(len(offers),16)
            self.assertEqual([p['packet'] for p in offers],list(range(64,80)))
            self.assertEqual((w.offered,w.admitted,w.rejected),(16,12,4))
            w.check();old.check()
            new_state=w.snapshot();new_state['tick']=4096
            self.assertEqual(new_state,old.snapshot())
            old.tick=4160
            with self.assertRaises(AssertionError):old.input()
        w.tick=8256
        with self.assertRaises(AssertionError):w.input()
    def test_literal_does_not_use_producer(self):
        with patch.object(unchanged.World,'__init__',side_effect=AssertionError('producer forbidden')):
            self.assertTrue(literal.audit(self.rows[3])['verified'])
        tree=ast.parse(Path(literal.__file__).read_bytes())
        self.assertEqual([a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names],['hashlib','json'])
        self.assertFalse(any(isinstance(n,ast.ImportFrom) for n in ast.walk(tree)))
    def test_restored_subclass_has_prospective_inflow(self):
        for row in self.rows.values():
            replayed=candidate.World.restore(row['checkpoint'])
            old=unchanged.World.restore(row['checkpoint'])
            self.assertIs(type(replayed),candidate.World)
            replayed.tick=4160;old.tick=4096  # Explicit prepared boundary witness.
            self.assertEqual(replayed.input(),old.input())
            a=replayed.snapshot();a['tick']=4096
            self.assertEqual(a,old.snapshot());replayed.check();old.check()
    def test_wrong_prospective_admission_refused(self):
        for key,value in [('software_only',False),('seed',1),('mode','mutating'),('dose',1),
                          ('version',unchanged.VERSION),('learning_demonstrated',True)]:
            row=copy.deepcopy(self.rows[3]);row[key]=value
            with self.assertRaises(AssertionError):literal.audit(row)
    def test_resealed_physical_corruptions_refused(self):
        for kind in ('ledger','register','birth','history'):
            row=copy.deepcopy(self.rows[3]);final=row['final']
            if kind=='ledger':final['heat']+=1
            elif kind=='register':next(iter(final['entities'].values()))['registers'][0]^=1
            elif kind=='birth':next(e for e in final['events'] if 'birth' in e)['birth']['child']['pc']=1
            else:final['events'][0]['actor']=999
            row['hash']=literal.h(final)
            with self.assertRaises((AssertionError,KeyError)):literal.audit(row)

if __name__=='__main__':unittest.main()
