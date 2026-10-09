import copy
import unittest
from experiments import startup_unscreened as worker
from experiments import startup_unscreened_audit as audit

class UnscreenedTests(unittest.TestCase):
    def test_frozen_genesis_matched_resources_and_unscreened_replay(self):
        self.assertEqual(len(audit.configurations()),224)
        for mode in worker.MODES:
            record=worker.simulate(40000,mode)
            audit.verify_record(record,dict(seed=40000,mode=mode))
            audit.validate(record['initial']); audit.validate(record['terminal'])
            self.assertNotIn('channels',record['initial'])
            self.assertNotIn('target_length',record['config'])
        a=worker.initial(40000,'active')[0]; b=worker.initial(40000,'supplied')[0]
        self.assertEqual(a['atoms'],b['atoms']); self.assertEqual(len(b['history']['C']['debits']),13)

    def test_generic_two_atom_full_price_and_empty_bound_renewal_fixture(self):
        s,_=worker.initial(40000,'topup_off')
        # Authored feasibility fixture only, never included in fresh seed-panel counts.
        requests=((0,0,0,0,0,0),(2,0,0,0,0,0),(0,1,1,0,0,0),(3,1,0,0,0,0),
                  (0,1,2,0,0,0),(4,0,0,0,0,0))
        for t,q in enumerate(requests): worker.step(s,'topup_off',t,q); audit.validate(s)
        product=s['history']['P5']; self.assertEqual(len(product['atoms']),2)
        self.assertEqual(len(product['debits']),7)
        self.assertFalse(product['fully_capture_funded'])
        self.assertEqual(product['parents'],['C3'])
        self.assertEqual(s['history']['C1']['atoms'],['M0'])

    def test_ghost_price_and_irreversible_waste_conservation(self):
        states=[]
        for mode in ('active','ghost'):
            s,_=worker.initial(40000,mode)
            for t,q in enumerate(((0,0,0,0,0,0),(2,0,0,0,0,0),(0,1,1,0,0,0),(3,1,0,0,0,0),(0,1,2,0,0,0),(4,0,0,0,0,0))):
                worker.step(s,mode,t,q); audit.validate(s)
            states.append(s)
        self.assertEqual(states[0]['history']['P5']['debits'],states[1]['history']['P5']['debits'])
        self.assertEqual(states[1]['heat']-states[0]['heat'],2)
        self.assertEqual(states[1]['products']['P5']['work'],[])
        self.assertEqual(len(states[0]['waste']),3)

    def test_withdrawal_does_not_create_or_remove_energy(self):
        s,_=worker.initial(40000,'active'); before=copy.deepcopy(s)
        worker.step(s,'active',128,[0,0,0,0,0,0]); self.assertEqual(s,before)
        worker.step(s,'food_withdrawn',128,[0,0,0,0,0,0]); self.assertEqual(s,before)
        worker.step(s,'external',128,[0,0,0,0,0,0]); self.assertEqual(len(s['bank']),62); audit.validate(s)

    def test_coherent_history_funding_noise_and_boolean_forgeries_reject(self):
        record=worker.simulate(40000,'active')
        for mode in ('heat','parent','funding','noise','boolean'):
            r=copy.deepcopy(record)
            if mode=='heat': r['terminal']['heat']+=1
            elif mode=='parent': next(iter(r['terminal']['history'].values()))['parents']=['fake']
            elif mode=='funding': r['terminal']['reserve_work']=[]
            elif mode=='noise': r['events'][0]['draw'][1]^=1
            else: r['config']['seed']=False
            with self.subTest(mode=mode),self.assertRaises(ValueError):
                audit.verify_record(r,dict(seed=40000,mode='active'))
        s,_=worker.initial(40000,'active'); s['free'].append('M0')
        with self.assertRaises(ValueError): audit.validate(s)
        with self.assertRaises(ValueError): audit.decode('{"x":1,"x":2}')

if __name__=='__main__': unittest.main()
