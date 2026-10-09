"""Unreserved authored LIGATE-01 gates; no discovery seed is executed here."""
import unittest
from experiments import ligate as p, ligate_audit as a

class LigateTest(unittest.TestCase):
    def world(self): return p.new(75999,'candidate')
    def test_genesis_accounting(self):
        w=self.world(); p.check(w); self.assertEqual(w,a.initial(75999,'candidate'))
        self.assertEqual(w['photons'],256); self.assertFalse(w['productive'])
    def test_paid_ligation_cleavage(self):
        w=self.world()
        p.tick(w,1,[0,0,1,2,0,0])
        self.assertEqual(p.tick(w,2,[1,0,1,2,0,0]),['ligate',32,0,1,None])
        self.assertEqual(w['heat'],2); self.assertEqual(w['photons'],253)
        self.assertEqual(p.tick(w,3,[2,30,0,0,0,0]),['cleave',32,33,34,1])
        self.assertEqual(w['heat'],3); p.check(w)
    def test_cross_production_and_independent_interpretation(self):
        w=self.world(); v=a.initial(75999,'candidate')
        # Authored basal dimer; generic target determines a priced substrate,
        # never a selected or supplied discovery founder.
        p.tick(w,1,[0,0,1,2,0,0]); a.interpret(v,1,[0,0,1,2,0,0])
        p.tick(w,2,[1,0,1,2,0,0]); a.interpret(v,2,[1,0,1,2,0,0])
        live=[o for o in w['objects'] if o['alive']]; typ=p.target([0,1])
        mono=next(i for i,o in enumerate(live) if len(o['atoms'])==1 and o['atoms'][0]//16==typ)
        for t,d in ((3,[0,mono,0,30,8,0]),(4,[1,mono,(mono+1)%30,0,0,0])):
            self.assertEqual(p.tick(w,t,d),a.interpret(v,t,d)); self.assertEqual(w,v)
        self.assertEqual(w['stats']['catalytic'],1); self.assertEqual(w['stats']['cross'],1)
        self.assertEqual(w['productive'],[32]); self.assertEqual(w['photons'],250)
    def test_no_borrowing_or_free_refund(self):
        w=self.world(); w['heat']=255; w['photons']=1
        self.assertIsNone(p.tick(w,1,[0,0,1,2,0,0])); self.assertEqual(w['photons'],1)
        w['photons']+=1
        with self.assertRaises(ValueError): p.check(w)
    def test_fixture_replay_all_arms(self):
        for arm in p.ARMS:
            w=p.new(75999,arm); v=a.initial(75999,arm)
            for t in range(1,2049):
                d=[p.draw(w) for _ in range(6)]; v['rng']=w['rng']
                self.assertEqual(p.tick(w,t,d),a.interpret(v,t,d)); self.assertEqual(w,v)
    def test_reserved_seed_rejection(self):
        with self.assertRaises(ValueError): p.new(73000,'candidate')

if __name__=='__main__': unittest.main()
