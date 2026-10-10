import unittest
from fractions import Fraction
from experiments.equilibrium_gate import multiplicity,weight,exact
from experiments.local_world import transition

class ExactPopulation(unittest.TestCase):
    def test_labelled_source_multiplicity(self):
        s=(4,3,0,0,0,1)
        self.assertEqual(multiplicity(s,('work',0,1)),3)
        self.assertEqual(multiplicity(s,('work',0,-1)),3)
        self.assertEqual(multiplicity(s,('activate',0,1)),1)
    def test_aggregate_flux_requires_token_counts(self):
        s=(6,1,0,0,0,0);a=('capture',0,1);t,p=transition(s,a,'candidate');u,q=transition(t,('capture',0,-1),'candidate')
        self.assertEqual(u,s)
        self.assertEqual(weight(s)*p*multiplicity(s,a),weight(t)*q*multiplicity(t,('capture',0,-1)))
        self.assertNotEqual(weight(s)*p,weight(t)*q)
    def test_no_rounded_zero_or_probability(self):
        self.assertEqual(exact(Fraction(1,2**68)),[1,2**68]);self.assertEqual(exact(Fraction(0)),[0,1])
if __name__=='__main__':unittest.main()
