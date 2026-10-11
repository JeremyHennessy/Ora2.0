import copy
import json
import unittest
from experiments import correlated_cycle as producer
from experiments import correlated_cycle_audit as independent

class CycleTests(unittest.TestCase):
    def test_finite_bijection_and_energy(self):
        tables=independent._tables()
        for m,a,b,w in independent._states():
            for arm,table in tables.items():
                out,work,memory,_=producer.cycle((a,b),w,m,arm)
                self.assertEqual((memory,*out,work),table[(m,a,b,w)])

    def test_positive_and_reverse_source_work(self):
        r=producer.record(((0,0),(0,1),(1,1)),'stationary')
        self.assertEqual((r['retained_load'],r['positive_source_work'],r['returned_source_work']),(2,4,2))
        self.assertIsNone(r['whole_life_net'])

    def test_complete_panel_matches_actual_stationary_cycle(self):
        d=independent.audit(producer.panel())
        self.assertTrue(d['stationary_matches_candidate_on_all_tapes'])
        self.assertFalse(d['admitted'])
        self.assertFalse(d['profitable_paid_comparator_verified'])

    def test_refuses_free_prices_and_work_forgery(self):
        r=producer.record(((0,0),)*3,'memory_cycle')
        for field,value in [('retained_load',7),('whole_life_net',6),('costs',dict(r['costs'],raw_coupler_fabrication=0)),('raw_formation',True)]:
            forged=copy.deepcopy(r);forged[field]=value
            with self.assertRaises(ValueError):independent._check_record(forged)

    def test_duplicate_and_noninteger_state_refuses(self):
        with self.assertRaises(ValueError):json.loads('{"work":0,"work":1}',object_pairs_hook=independent.unique)
        for args in [((False,0),0,0,'stationary'),((0,0),False,0,'stationary'),((0,0),7,0,'stationary')]:
            with self.assertRaises(ValueError):producer.cycle(*args)

    def test_initial_memory_is_a_resource_not_free_reset(self):
        out,w,m,_=producer.cycle((1,1),0,1,'memory_cycle')
        self.assertEqual((out,w,m),((1,1),0,1))
        self.assertEqual(producer.cycle((1,1),0,0,'memory_cycle')[:3],((1,0),2,0))

if __name__=='__main__':unittest.main()
