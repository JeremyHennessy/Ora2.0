"""Ordering/refusal fixtures; no producer histories or World."""
import unittest
from unittest.mock import patch
from experiments import digital_firstborn63_runner as r
from experiments import digital_informative_exposure23 as substrate


class Ordering(unittest.TestCase):
    def setUp(self):
        trap=patch.object(substrate,'World',side_effect=AssertionError('World forbidden'))
        trap.start();self.addCleanup(trap.stop)
        self.calls=[];self.receipts=[];self.gate_calls=[]

    def run_pair(self,location,seed,source):
        if source is not None:
            self.assertEqual(len(self.receipts),1)
            self.assertTrue(self.receipts[0]['admitted'])
        self.calls.append((location,seed,source))
        return dict(pair=dict(seed=seed,source=source),histories=['prepared'])

    def gate(self,rows):
        self.assertEqual(len(rows),16)
        self.assertEqual([x['pair']['seed'] for x in rows],list(r.SEEDS))
        self.assertTrue(all(x['pair']['source'] is None for x in rows))
        self.gate_calls.append(rows)
        return True

    def test_all_references_both_locations_before_all_sources(self):
        with patch.object(r,'ordinary_admission',side_effect=self.gate),patch.object(r,'cohort',side_effect=lambda p:dict(pairs=len(p))):
            result=r.panel(self.run_pair,self.receipts.append)
        self.assertEqual(len(self.calls),288)
        self.assertEqual(len(self.gate_calls),2)
        self.assertTrue(all(c[2] is None for c in self.calls[:32]))
        expected={(loc,seed,source) for loc in r.LOCATIONS for seed in r.SEEDS for source in (None,)+r.ROSTER}
        self.assertEqual(set(self.calls),expected)
        self.assertEqual(result['unique_histories'],288)
        self.assertEqual(result['engineering_replays'],288)

    def test_failed_ordinary_still_evaluates_both_sets_and_opens_no_source(self):
        for gates in ((False,True),(True,False),(False,False)):
            self.calls=[];self.receipts=[]
            with patch.object(r,'ordinary_admission',side_effect=gates) as admission,patch.object(r,'cohort',side_effect=AssertionError('cohort forbidden')):
                result=r.panel(self.run_pair,self.receipts.append)
            self.assertEqual(admission.call_count,2)
            self.assertEqual(len(self.calls),32)
            self.assertIsNone(result['comparison'])
            self.assertEqual(result['unique_histories'],32)
            self.assertFalse(result['admission']['admitted'])

    def test_reference_replay_mismatch_stops_before_sources(self):
        def callback(location,seed,source):
            row=self.run_pair(location,seed,source)
            if location=='restored':row['corrupt']=True
            return row
        with patch.object(r,'ordinary_admission',side_effect=self.gate):
            with self.assertRaises(AssertionError):r.panel(callback,self.receipts.append)
        self.assertEqual(len(self.calls),32);self.assertEqual(self.receipts,[])

    def test_native_failure_stops_without_sources(self):
        def callback(location,seed,source):
            self.run_pair(location,seed,source);raise RuntimeError('native failed')
        with self.assertRaises(RuntimeError):r.panel(callback,self.receipts.append)
        self.assertEqual(len(self.calls),1);self.assertEqual(self.receipts,[])

    def test_admission_receipt_failure_prevents_sources(self):
        def save(receipt):raise OSError('budget refusal')
        with patch.object(r,'ordinary_admission',side_effect=self.gate):
            with self.assertRaises(OSError):r.panel(self.run_pair,save)
        self.assertEqual(len(self.calls),32)

    def test_source_replay_mismatch_prevents_cohort(self):
        def callback(location,seed,source):
            row=self.run_pair(location,seed,source)
            if source is not None and location=='restored':row['corrupt']=True
            return row
        with patch.object(r,'ordinary_admission',side_effect=self.gate),patch.object(r,'cohort',side_effect=AssertionError('cohort forbidden')):
            with self.assertRaises(AssertionError):r.panel(callback,self.receipts.append)
        self.assertEqual(len(self.calls),34)


if __name__=='__main__':unittest.main()
