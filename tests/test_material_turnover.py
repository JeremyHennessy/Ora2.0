import copy
import unittest

from experiments import material_turnover as sim
from experiments import material_turnover_audit as oracle


def authored_initial(work=96):
    initial, _ = sim.genesis(1, work)
    for oid, bit in (("g0", "0"), ("g1", "1")):
        initial["objects"][oid]["bits"] = bit
        initial["atoms"][initial["objects"][oid]["atoms"][0]]["bit"] = bit
    for n in initial["nutrients"].values():
        initial["atoms"][n["atom"]]["bit"] = "0"
    initial["nutrients"]["n0"]["site"] = 0
    return initial


class MaterialTurnoverTests(unittest.TestCase):
    def test_all_static_binary_reaction_ledgers(self):
        result = oracle.static_grammar()
        self.assertEqual(result["chains"], 126)
        self.assertEqual(result["length_permitted_ligations"], 516)
        self.assertEqual(result["bounded_reaction_cases"], 3584)
        self.assertTrue(result["bit_and_energy_residuals_zero"])

    def test_authored_paid_replacement_and_controls(self):
        initial = authored_initial()
        draws = [[0, 0, 0, 0, 0], [0, 4, 0, 0, 0], [0, 2, 0, 0, 0],
                 [0, 2, 0, 0, 0], [0, 0, 2, 2, 0], [0, 3, 0, 0, 0]]
        active_events = None
        for mode in sim.ARMS:
            engine = sim.Engine(initial, mode)
            state = copy.deepcopy(initial)
            budget = oracle.ledger(state)
            for tick, draw in enumerate(draws):
                state, opp, expected = oracle.transition(state, mode, tick, draw)
                engine.step(tick, draw)
                self.assertEqual(engine.s, state)
                self.assertEqual(engine.events[-1]["result"], expected)
                self.assertEqual(engine.events[-1]["opportunities"], opp)
                self.assertEqual(oracle.ledger(state), budget)
            if mode == "active":
                self.assertTrue(engine.events[-1]["result"]["qualifying_turnover"])
                self.assertEqual(engine.s["W"], 91)
                self.assertEqual(engine.s["atoms"]["a0"]["polymer_reclaims"], 1)
                active_events = engine.events
            if mode == "fixed":
                self.assertEqual(engine.events, active_events)
            if mode in ("ghost_reclaim", "ghost_capture", "local_stock", "shared_stock", "direct_access"):
                self.assertFalse(engine.events[-1]["result"]["qualifying_turnover"])
            if mode == "ghost_capture":
                self.assertEqual(len(engine.s["nutrients"]), 32)

    def test_genesis_monomer_recovery_is_not_polymer_turnover(self):
        engine = sim.Engine(authored_initial(), "active")
        for tick, draw in enumerate([[0, 4, 0, 0, 0], [0, 2, 0, 0, 0], [0, 0, 3, 0, 0], [0, 3, 0, 0, 0]]):
            engine.step(tick, draw)
        self.assertEqual(engine.events[-1]["result"]["outcome"], "converted")
        self.assertFalse(engine.events[-1]["result"]["qualifying_turnover"])
        self.assertEqual(engine.s["atoms"]["a0"]["polymer_reclaims"], 0)

    def test_zero_and_partial_work_never_create_energy_or_polymers(self):
        for work in (0, 1):
            initial = authored_initial(work)
            engine = sim.Engine(initial, "direct_access")
            for tick, draw in enumerate([[0, 0, 0, 0, 0], [0, 3, 0, 0, 0], [0, 2, 0, 0, 0]]):
                engine.step(tick, draw)
            self.assertEqual(len(engine.s["nutrients"]), 32)
            self.assertEqual(len(engine.s["objects"]), 32)
            self.assertEqual(engine.s["W"], 0)
            self.assertEqual(engine.s["heat"], work)

    def test_development_fixture_full_stream_and_fixed_match(self):
        # Seed1 is an existing development fixture; never sample pilot112..127 here.
        for work in (96, 0):
            record = sim.simulate(1, work)
            oracle.verify_record(record, 1, work)
            if work == 0:
                for arm in record["arms"]:
                    self.assertEqual(arm["statistics"]["births"], 0)
                    self.assertEqual(arm["statistics"]["conversions"], 0)
                    self.assertEqual(arm["statistics"]["exhausted_events"], 128)

    def test_rehashed_cost_provenance_and_selected_stream_forgeries_rejected(self):
        good = sim.simulate(1, 96)
        for name in ("cost", "ancestry", "stream", "missing", "founder", "summary", "identity"):
            record = copy.deepcopy(good)
            arm = record["arms"][0]
            if name == "cost":
                arm["events"][0]["result"]["charged_W"] += 1
                event = arm["events"][0]
                event["event_sha256"] = oracle.sha({k: v for k, v in event.items() if k != "event_sha256"})
            elif name == "ancestry":
                arm["terminal"]["atoms"]["a0"]["polymer_reclaims"] += 1
            elif name == "stream":
                record["draws"][0][1] = (record["draws"][0][1] + 1) % 8
            elif name == "missing":
                arm["events"].pop()
            elif name == "founder":
                arm["initial"]["objects"]["g0"]["bits"] = "01"
            elif name == "summary":
                arm["statistics"]["qualifying_uses"] += 1
            else:
                record["initial_work"] = True
            with self.subTest(name=name), self.assertRaises(ValueError):
                oracle.verify_record(record, 1, 96)

    def test_atom_duplicate_and_sequence_corruption_rejected(self):
        initial = authored_initial()
        for name in ("duplicate", "bit", "energy"):
            state = copy.deepcopy(initial)
            if name == "duplicate":
                state["objects"]["g1"]["atoms"] = ["a0"]
                state["objects"]["g1"]["bits"] = "0"
            elif name == "bit":
                state["objects"]["g0"]["bits"] = "1"
            else:
                state["W"] = True
            with self.subTest(name=name), self.assertRaises(ValueError):
                oracle.ledger(state)


if __name__ == "__main__":
    unittest.main()
