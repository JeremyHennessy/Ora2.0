import copy
import unittest
from experiments import formation_closure as producer
from experiments import formation_closure_audit as interpreter


class FormationClosureTests(unittest.TestCase):
    def test_raw_start_chain_and_cycle(self):
        self.assertEqual(producer.closure((0, 1, 2), 0), 7)
        self.assertEqual(producer.closure((2, 4, 1), 0), 0)
        self.assertEqual(producer.closure((2, 4, 1), 1), 7)
        self.assertEqual(producer.closure((0, 2, 4), 0), 1)
        with self.assertRaises(ValueError):
            producer.closure((False, 1, 2), 0)

    def test_full_census_independently_matches(self):
        result = interpreter.audit(producer.census())
        self.assertEqual(result["cases"], 4096)
        self.assertFalse(result["energy_admission"])

    def test_forged_success_and_missing_cases_refused(self):
        data = producer.census()
        variants = []
        forged = copy.deepcopy(data)
        forged["energy_admission"] = True
        variants.append(forged)
        missing = copy.deepcopy(data)
        missing["cases"].pop()
        variants.append(missing)
        duplicate = copy.deepcopy(data)
        duplicate["cases"][1] = duplicate["cases"][0]
        variants.append(duplicate)
        altered = copy.deepcopy(data)
        altered["cases"][0]["closure"] = 0
        variants.append(altered)
        for variant in variants:
            with self.subTest(variant=variants.index(variant)):
                with self.assertRaises(ValueError):
                    interpreter.audit(variant)


if __name__ == "__main__":
    unittest.main()
