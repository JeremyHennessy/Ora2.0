import copy
import unittest
from experiments import constructor_opportunity as sim
from experiments import constructor_opportunity_audit as audit
from experiments import constructor_events_audit as history


class ConstructorOpportunityTests(unittest.TestCase):
    def test_independent_full_stream_and_all_paired_controls(self):
        for seed in range(96, 112):
            for material in (32, 0):
                with self.subTest(seed=seed, material=material):
                    row = sim.world(seed, material)
                    audit.verify_world(row)
                    self.assertEqual(len(row["arms"]["active"]["ticks"]), 64)

    def test_registered_generator_prefix_cannot_be_truncated(self):
        row = sim.world(96,32)
        row["arms"]["active"]["ticks"].pop()
        with self.assertRaises(ValueError):
            audit.verify_world(row)

    def test_forged_noise_opportunity_and_extra_branch_rejected(self):
        for change in ("noise", "availability", "branch"):
            row = sim.world(96,32)
            if change == "noise":
                row["arms"]["ghost"]["ticks"][0]["draws"][0] = (row["arms"]["ghost"]["ticks"][0]["draws"][0] + 1) % 8
            elif change == "availability":
                e = row["arms"]["active"]["receipt"]["events"][0]
                e["opportunities"]["funded_internal_build"] = not e["opportunities"]["funded_internal_build"]
                e["sha256"] = history.digest({k:v for k,v in e.items() if k != "sha256"})
            else:
                row["branches"]["extra"] = copy.deepcopy(row["arms"]["active"])
            with self.subTest(change=change), self.assertRaises(ValueError):
                audit.verify_world(row)

    def test_paid_external_constructor_keeps_its_root_and_work_trap(self):
        initial = {"P": 8, "W": 4, "S": [1], "waste":0, "heat":0, "objects":{}}
        engine = sim.Engine(initial, "active")
        engine.step("external_build",0,"C","externalC")
        engine.step("build",0,"I","I1")
        result = engine.step("contact",0)
        row = {"schema":"constructor01-events-v1", "case":"authored-boundary", "mode":"active",
               "initial":initial, "events":engine.events, "terminal":engine.s}
        counts = history.audit_receipt(row)
        self.assertEqual(result["reason"], "read_work")
        self.assertEqual(counts["internal_C_births"],0)
        self.assertEqual(engine.s["objects"]["I1"]["roots"],["externalC"])
