import copy
import json
import unittest
from experiments.packet_buffer import Ledger, preflight
from experiments.packet_buffer_audit import audit


class PacketBufferTests(unittest.TestCase):
    def test_reference_and_actual_exhaustion(self):
        data = json.loads(json.dumps(preflight()))
        self.assertEqual(audit(data)['ordinary_whole'],19)
        self.assertNotIn('converter',data['positive']['final']['roles'])

    def test_refuses_free_capital_and_duplicate_source(self):
        x=Ledger([16],capital=6); x.command('form','c',kind='C')
        before=x.snapshot()
        with self.assertRaises(ValueError): x.command('intake',packet=0)
        self.assertEqual(x.snapshot(),before)
        y=Ledger([16]); y.command('intake',packet=0)
        before=y.snapshot()
        with self.assertRaises(ValueError): y.command('intake',packet=0)
        self.assertEqual(y.snapshot(),before)

    def test_cannot_convert_held_fuel_or_erase_formation_bill(self):
        x=Ledger([16]); x.command('form','b',kind='B'); x.command('form','c',kind='C')
        x.command('intake',packet=0); x.command('store','b',0)
        before=x.snapshot()
        with self.assertRaises(ValueError): x.command('convert','c',0)
        self.assertEqual(x.snapshot(),before)
        data=json.loads(json.dumps(preflight())); forged=copy.deepcopy(data)
        forged['positive']['paid']=0
        with self.assertRaises(AssertionError): audit(forged)

    def test_rejects_forged_ancestry_and_work(self):
        data=json.loads(json.dumps(preflight()))
        for field in ('load','heat'):
            bad=copy.deepcopy(data); bad['all_source_sizes'][15]['events'][-1]['state'][field]+=1
            with self.assertRaises(AssertionError): audit(bad)
        bad=copy.deepcopy(data)
        bad['buffer_witness']['events'][3]['state']['packets']['0']['ancestors']=[99]
        with self.assertRaises(AssertionError): audit(bad)
