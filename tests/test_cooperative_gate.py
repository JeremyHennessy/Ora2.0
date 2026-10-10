import unittest
from experiments import cooperative_gate as g,cooperative_audit as a
class Cooperative(unittest.TestCase):
    def test_priced_binding_capital_and_damage(self):
        for B in range(7):
            s=(1,1,1,1,2)
            self.assertEqual(g.heat(s,B),a.thermal(s,B))
            self.assertEqual(g.loss(s,B),a.destruction(s,B))
            self.assertEqual(g.heat(g.loss(s,B),B)-g.heat(s,B),4-B)
            self.assertEqual(max(0,6-g.potential(s,B)),max(0,B-4))
        self.assertIsNone(g.loss((1,1,1,0,34),6))
    def test_complete_parities_and_reverse_law(self):
        for B in (0,3,6):
            for p in (0,1):
                states,summary=g.graph(B,p);other,census=a.census(B,p)
                self.assertEqual(states,other);self.assertEqual(summary,census)
                for s in states:
                    for k,d in g.ACTIONS:
                        self.assertEqual(g.move(s,(k,d),B),a.apply(s,k,d,B))
                        for arm in g.ARMS:self.assertEqual(g.rate(s,(k,d),B,arm),a.probability(s,k,d,B,arm))
    def test_resource_yoked_goal_and_flag(self):
        for B in range(7):
            states,_=g.graph(B,1);s=(1,1,1,1,2)
            self.assertEqual(g.phases(B,states)(s),a.phase_max(s,B,set(states)))
        self.assertEqual(g.flag((1,1,1,2,2),('capture',1),0),1)
        self.assertEqual(a.newflag((1,1,1,2,2),'bond',-1,1),0)
if __name__=='__main__':unittest.main()
