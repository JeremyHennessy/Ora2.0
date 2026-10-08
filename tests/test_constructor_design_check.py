import copy
import json
import unittest

from experiments import constructor_design_check as check


class ConstructorDesignTests(unittest.TestCase):
    def setUp(self):
        self.law = json.loads(check.LAW.read_text(encoding="utf-8"))

    def test_finite_feasibility_and_work_trap(self):
        result = check.analyze(self.law)
        self.assertEqual(result["one_event_input_states"], 5616)
        by_name = {c["name"]: c for c in result["authored_envelopes"]}
        self.assertFalse(by_name["work_trap"]["conversion_reachable"])
        self.assertTrue(by_name["work_trap"]["constructor_birth_reachable"])
        self.assertEqual(by_name["productive_buffer"]["shortest_conversion_events"], 3)
        self.assertFalse(by_name["no_producer"]["constructor_birth_reachable"])
        self.assertTrue(by_name["interface_only"]["conversion_reachable"])
        self.assertFalse(by_name["interface_only"]["constructor_birth_reachable"])
        self.assertEqual(result["stochastic_worlds"], 0)

    def test_conserved_but_free_or_ungated_build_rejected(self):
        for change in ("free", "ungated", "wrong_producer"):
            law = copy.deepcopy(self.law)
            row = next(r for r in law["reactions"] if r["name"] == "make_C")
            if change == "free":
                row["delta"][7:9] = [0, 0]
                row["minimum_W"] = 0
            else:
                row["catalyst"] = None if change == "ungated" else "D"
            self.assertEqual(check.totals(row["delta"]), (0, 0))
            with self.subTest(change=change), self.assertRaises(ValueError):
                check.validate(law)

    def test_energy_leak_and_hidden_external_reaction_rejected(self):
        for change in ("energy", "extra", "duplicate", "price"):
            law = copy.deepcopy(self.law)
            if change == "energy":
                law["reactions"][4]["delta"][7] += 1
            elif change == "extra":
                law["reactions"].append({"name": "external_C", "catalyst": None, "product": "C", "minimum_W": 0, "delta": check.vector(C=1)})
            elif change == "duplicate":
                law["reactions"][-1] = copy.deepcopy(law["reactions"][0])
            else:
                law["contact_read_work"] = 0
            with self.subTest(change=change), self.assertRaises(ValueError):
                check.validate(law)

    def test_contacts_cannot_cash_energy_without_work(self):
        rows = {r["name"]: r for r in self.law["reactions"]}
        one_work = (0, 1, 0, 0, 1, 0, 0, 1, 0)
        self.assertIsNone(check.advance(one_work, rows["convert"]))
        depleted = check.advance(one_work, rows["read_only"])
        self.assertEqual(depleted[7:9], (0, 1))
        two_work = (0, 1, 0, 0, 1, 0, 0, 2, 0)
        self.assertIsNone(check.advance(two_work, rows["failed_contact"]))
        converted = check.advance(two_work, rows["convert"])
        self.assertEqual(converted[7:9], (3, 7))
        self.assertEqual(check.totals(two_work), check.totals(converted))

    def test_material_damage_matches_but_dependency_differs(self):
        state = (8, 1, 1, 1, 0, 1, 0, 4, 0)
        c_cut, d_cut = (check.paid_impairment(state, x) for x in ("C", "D"))
        make_i = next(r for r in self.law["reactions"] if r["name"] == "make_I")
        self.assertIsNone(check.advance(c_cut, make_i))
        self.assertIsNotNone(check.advance(d_cut, make_i))
        self.assertEqual(check.totals(c_cut), check.totals(d_cut))
        self.assertEqual(c_cut[6:9], d_cut[6:9])
        self.assertIsNone(check.paid_impairment((8,1,1,1,0,1,0,0,0), "C"))

    def test_slot_reuse_does_not_claim_ancestry(self):
        rows = {r["name"]: r for r in self.law["reactions"]}
        state = (16, 1, 1, 0, 0, 0, 0, 10, 0)
        for name in ("make_C", "decay_A", "make_A", "decay_C", "make_C", "make_I", "convert"):
            previous = state
            state = check.advance(state, rows[name])
            self.assertIsNotNone(state)
            self.assertEqual(check.totals(state), check.totals(previous))
        self.assertEqual(state, (0,0,1,1,1,0,9,3,15))
        # Static occupancy can witness the budget, but it cannot establish
        # never-reused birth IDs or living catalyst ancestry in a simulator.


if __name__ == "__main__":
    unittest.main()
