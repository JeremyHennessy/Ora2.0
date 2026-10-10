import copy
import unittest
from experiments.channel_gate import produce
from experiments.channel_audit import audit

class ChannelGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=produce('frozen-test')
    def test_independent_rational_grid_and_all_certificates(self):
        result=audit(self.data,'frozen-test');self.assertFalse(result['mechanism_admitted']);self.assertEqual(result['controlled_certificates'],48)
    def test_capital_preserving_counterexample(self):
        for r in self.data['certificates']:
            self.assertGreater(r['gross_work'],r['claimed_ceiling']);self.assertGreaterEqual(r['final_heat'],8)
    def test_energy_rate_and_provenance_forgeries(self):
        for kind in ('energy','rate','provenance'):
            data=copy.deepcopy(self.data)
            if kind=='energy':data['certificates'][0]['states'][-1][1]+=1
            elif kind=='rate':data['local_grids'][0]['edge_sha256']='0'*64
            else:data['certificates'][0]['events'][-1]['output_origin']='fresh-fuel'
            with self.assertRaises(ValueError):audit(data,'frozen-test')
