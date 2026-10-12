import unittest
from experiments import digital_candidate_admission26 as source
from experiments.digital_neutral_catalogue25 import candidate

class Admission26Tests(unittest.TestCase):
    def test_complete_structural_inclusion(self):
        actual=[i for i in range(744) if candidate(i)['mutation']['flat_address']%3==0 and candidate(i)['mutation']['new']==1]
        self.assertEqual(actual,list(source.CANDIDATES))
        self.assertEqual(len(source.programmes()),19)

    def test_restore_registry_has_unique_genomes(self):
        codes,routes=source.install_registry()
        self.assertEqual(len(routes),19)
        self.assertEqual(len({tuple(sum(p,[])) for p in source.substrate.PROGRAMS.values()}),len(source.substrate.PROGRAMS))
        for role,code in codes.items():self.assertEqual(source.substrate.PROGRAMS[routes[role]],code)
        self.assertEqual(source.install_registry(),(codes,routes))

    def test_reject_unregistered_batch_before_execution(self):
        for seed,group in ((True,'candidates'),(26890,'references'),(26900,'winner')):
            with self.assertRaises(ValueError):source.batch(seed,group)
