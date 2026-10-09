import copy
import unittest
from experiments import paid_dissociation as worker
from experiments import paid_dissociation_audit as audit

class DissociationTests(unittest.TestCase):
    def test_frozen_scope_and_paired_complete_semantic_ledger(self):
        self.assertEqual(list(worker.configs()),audit.configurations()); self.assertEqual(len(audit.configurations()),1344)
        for mode in worker.MODES:
            for word in ('00','000','0000'):
                c=dict(word=word,budget=32,food_bit='1',mode=mode); r=worker.simulate(c)
                self.assertEqual(worker.metrics(r),audit.verify_record(r,c))
                self.assertLessEqual(len(r['events']),64)
                audit.validate(r['initial']); audit.validate(r['terminal'])

    def test_cut_ghost_matches_work_bond_charge_price_without_refund(self):
        snapshots=[]
        for mode in ('candidate','cut_ghost'):
            c=dict(word='00',budget=32,food_bit='1',mode=mode); s=worker.initial(c)
            for t,op,atom,phase in worker.schedule(c):
                q=worker.select(s,c,op,atom,phase); before=copy.deepcopy(s); result=worker.step(s,c,t,q)
                if op==6:
                    snapshots.append((before,s,result)); break
        self.assertEqual(snapshots[0][2]['spent'],snapshots[1][2]['spent'])
        self.assertEqual(snapshots[0][2]['heat'],snapshots[1][2]['heat'])
        self.assertEqual(len(snapshots[0][1]['products'][snapshots[0][2]['actor']]['work']),1)
        for before,s,r in snapshots:
            self.assertEqual(r['heat'],s['heat']-before['heat']); self.assertEqual(r['heat'],6)
            audit.validate(s)
        self.assertIn('M4',snapshots[0][1]['free']); self.assertNotIn('M4',snapshots[1][1]['free'])
        self.assertIn('M4',snapshots[1][1]['spare']); self.assertEqual(snapshots[0][1]['recycles']['M4'],['D130'])

    def test_insufficient_work_leaves_four_atom_cut_unchanged(self):
        c=dict(word='0000',budget=32,food_bit='1',mode='candidate'); s=worker.initial(c)
        for t,op,atom,phase in worker.schedule(c):
            q=worker.select(s,c,op,atom,phase); before=copy.deepcopy(s); result=worker.step(s,c,t,q)
            if op==6:
                self.assertEqual(result['outcome'],'starved'); self.assertEqual(s,before)
                self.assertEqual(len(s['products'][q['actor']]['work']),4); break

    def test_work_recycling_ancestry_boolean_and_cut_debit_forgeries_reject(self):
        c=dict(word='00',budget=32,food_bit='1',mode='candidate'); r=worker.simulate(c)
        for kind in ('heat','recycle','parent','work','boolean'):
            bad=copy.deepcopy(r)
            if kind=='heat': bad['terminal']['heat']+=1
            elif kind=='recycle': bad['terminal']['recycles']['M4']=[]
            elif kind=='parent': bad['terminal']['history']['D130']['parents']=[]
            elif kind=='work': bad['terminal']['history']['D130']['work_debits']=[]
            else: bad['terminal']['history']['D130']['returned']=1
            with self.subTest(kind=kind),self.assertRaises(ValueError): audit.verify_record(bad,c)

if __name__=='__main__': unittest.main()
