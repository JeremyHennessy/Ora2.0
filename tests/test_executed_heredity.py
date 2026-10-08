"""AL02-COPY: independently test causal birth evidence and material accounting."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
import tempfile
import unittest

from experiments.executed_heredity import (
    ALPHABET, COPY, DIVIDE, EAT_A, EAT_B, LOOP, NOP, SEED_TAPE,
    MATERIAL_UNITS, VARIANTS, World, genotype_hash, study,
)
from experiments.lineage_audit import audit_births


class VirtualPhysicsTests(unittest.TestCase):
    def test_blank_tape_and_unauthorized_opcode_rejected(self):
        for tape in ((), (0, 99), (0, -1)):
            with self.assertRaises(ValueError):
                World(1, founder_ops=tape)
        self.assertEqual(set(ALPHABET), set(range(6)))

    def test_conservation_during_neutral_run(self):
        w = World(0, variant="faithful", food_a=5, food_b=7)
        for _ in range(120):
            if not w.organisms:
                break
            w.execute_one()
            self.assertEqual(w.assert_invariants(), (0, 0))
        self.assertEqual(w.energy_residual_max, 0)
        self.assertEqual(w.material_residual_max, 0)
        self.assertLessEqual(w.max_population_seen, 64)

    def test_genesis_does_not_insert_mutant(self):
        w = World(10, variant="faithful", food_a=4, food_b=4)
        self.assertEqual(w.organisms[0].ops(), SEED_TAPE)
        self.assertEqual(w.births, [])
        self.assertEqual([e["kind"] for e in w.events], ["GENESIS"])

    def test_nothing_born_when_no_copy_execution(self):
        w = World(2, variant="copy_disabled")
        s = w.run(120)
        self.assertEqual(s["birth_count"], 0)
        self.assertGreater(s["failed_copy_attempts"], 0)
        self.assertFalse(any(e["kind"] == "COPY_WRITE" for e in w.events))
        self.assertEqual(audit_births(w.births, w.events)["invalid_births"], 0)

    def test_nothing_born_without_food(self):
        w = World(3, variant="no_food")
        s = w.run(80)
        self.assertEqual(s["birth_count"], 0)
        self.assertEqual((w.food_a, w.food_b), (0, 0))
        self.assertTrue(s["world_extinct"])
        self.assertEqual(s["max_energy_residual"], 0)

    def test_both_resources_have_mechanical_not_score_effects(self):
        a = World(4, variant="faithful", founder_ops=SEED_TAPE, food_a=0, food_b=3)
        b = World(4, variant="faithful",
                  founder_ops=(EAT_B, COPY, LOOP, DIVIDE),
                  food_a=0, food_b=3)
        self.assertEqual(a.run(40)["birth_count"], 0)
        self.assertGreater(b.run(40)["birth_count"], 0)
        self.assertEqual(audit_births(b.births, b.events)["invalid_births"], 0)
        self.assertEqual(b.max_population_seen > 1, True)

    def test_inert_program_cannot_reproduce(self):
        w = World(0, variant="faithful", founder_ops=(NOP,), food_a=5, food_b=5)
        s = w.run(30)
        self.assertTrue(s["world_extinct"])
        self.assertEqual(s["birth_count"], 0)
        self.assertEqual(s["max_material_residual"], 0)

    def test_energy_and_material_return_on_death(self):
        w = World(0, variant="no_food")
        w.run(90)
        self.assertEqual(w.free_units, set(range(MATERIAL_UNITS)))
        self.assertEqual(w.heat, w.genesis_energy)
        self.assertEqual(w.assert_invariants(), (0, 0))

    def test_fake_unregistered_organism_is_rejected_even_when_material_balances(self):
        from experiments.executed_heredity import Gene, Organism
        w = World(0, variant="faithful")
        material_unit = min(w.free_units)
        w.free_units.remove(material_unit)
        w.organisms[41] = Organism(
            organism_id=41, tape=(Gene(NOP, material_unit),),
            energy=0, generation=1, parent_id=0, born_tick=0
        )
        # Mass and energy alone cannot catch an unauthorized engine-side duplication.
        with self.assertRaisesRegex(AssertionError, "Unregistered live organism"):
            w.assert_invariants()

    def test_consumption_is_accounted_separately_by_food_species(self):
        w = World(4, variant="faithful", food_a=3, food_b=8)
        r = w.run(50)
        self.assertEqual(r["consumed_food_a"], 3 - r["remaining_food_a"])
        self.assertEqual(r["consumed_food_b"], 8 - r["remaining_food_b"])
        self.assertGreater(r["consumed_food_a"], 0)
        self.assertEqual(r["consumed_food_b"], 0)
        self.assertEqual(w.assert_invariants(), (0, 0))


class LineageAuditTests(unittest.TestCase):
    def setUp(self):
        self.world = World(11, variant="faithful", food_a=4, food_b=0)
        summary = self.world.run(60)
        if summary["birth_count"] < 1:
            raise AssertionError("Positive-control test world failed to produce daughter")

    def test_causally_executed_positive_control(self):
        audit = audit_births(self.world.births, self.world.events)
        self.assertEqual(audit["valid_births"], len(self.world.births))
        self.assertEqual(audit["invalid_births"], 0)
        self.assertGreater(audit["executed_write_events"], 0)
        first = self.world.births[0]
        self.assertEqual(first["parent_id"], 0)
        self.assertEqual(first["child_genome_ops"], list(SEED_TAPE))
        self.assertEqual(len(first["copy_event_ids"]), len(SEED_TAPE))
        self.assertEqual(first["generation"], 1)
        self.assertEqual(len(set(first["child_material_units"])), len(SEED_TAPE))

    def test_fake_engine_birth_rejected(self):
        births = deepcopy(self.world.births)
        forged = deepcopy(births[0])
        forged["event_id"] = 9999999
        forged["child_id"] = 999999
        forged["copy_event_ids"] = []
        births.append(forged)
        audit = audit_births(births, self.world.events)
        self.assertGreater(audit["invalid_births"], 0)

    def test_parent_swap_rejected_even_if_daughter_looks_identical(self):
        births = deepcopy(self.world.births)
        births[0]["parent_id"] = 12345
        audit = audit_births(births, self.world.events)
        self.assertGreater(audit["invalid_births"], 0)

    def test_byte_tamper_rejected(self):
        births = deepcopy(self.world.births)
        birth = births[0]
        birth["child_genome_ops"][0] = EAT_B
        audit = audit_births(births, self.world.events)
        self.assertGreater(audit["invalid_births"], 0)

    def test_mutation_receipts_are_inherited_as_actual_bytes(self):
        w = World(10, variant="mutating", food_a=4, food_b=8, mutation_rate=1.0)
        s = w.run(40)
        self.assertGreater(s["mutated_bytes_written"], 0)
        self.assertGreater(s["birth_count"], 0)
        self.assertGreater(
            sum(any(x != y for x, y in zip(b["child_genome_ops"], b["parent_genome_ops"]))
                for b in w.births), 0
        )
        self.assertEqual(audit_births(w.births, w.events)["invalid_births"], 0)

    def test_faithful_copy_rejects_mutation_as_environmental_resemblance(self):
        self.assertEqual(self.world.mutations_written, 0)
        self.assertTrue(all(b["child_genome_ops"] == b["parent_genome_ops"]
                            for b in self.world.births))
        self.assertTrue(all(b["parent_genome_hash"] == genotype_hash(b["parent_genome_ops"])
                            for b in self.world.births))

    def test_event_and_birth_receipts_cannot_disagree(self):
        records = deepcopy(self.world.births)
        records.pop()
        self.assertGreater(audit_births(records, self.world.events)["invalid_births"], 0)

    def test_byte_writer_provenance_complete_per_birth(self):
        mapping = {e["event_id"]: e for e in self.world.events}
        for b in self.world.births:
            for i, write_id in enumerate(b["copy_event_ids"]):
                write = mapping[write_id]
                self.assertLess(write_id, b["event_id"])
                self.assertEqual(write["source_index"], i)
                self.assertEqual(write["nursery_index"], i)
                self.assertEqual(write["written_op"], b["child_genome_ops"][i])
                self.assertEqual(write["material_unit"], b["child_material_units"][i])
                self.assertEqual(write["parent_id"], b["parent_id"])


class StudyTests(unittest.TestCase):
    def test_deterministic_complete_world_replay(self):
        a = World(34, variant="mutating")
        b = World(34, variant="mutating")
        self.assertEqual(a.run(180), b.run(180))
        self.assertEqual(a.births, b.births)
        self.assertEqual(a.events, b.events)

    def test_all_four_controls_and_replay_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td)
            a = study(dest, [0, 1], revision="test-revision")
            files1 = {p.name: p.read_bytes() for p in dest.iterdir()}
            b = study(dest, [0, 1], revision="test-revision")
            files2 = {p.name: p.read_bytes() for p in dest.iterdir()}
            self.assertEqual(a, b)
            self.assertEqual(files1, files2)
            self.assertEqual(a["world_count"], 8)
            self.assertEqual(len((dest / "worlds.jsonl").read_text().splitlines()), 8)
            self.assertEqual(len((dest / "births.jsonl").read_text().splitlines()),
                             a["total_births"])
            self.assertEqual(len((dest / "events.jsonl").read_text().splitlines()),
                             a["total_recorded_events"])
            self.assertEqual(a["variants"]["copy_disabled"]["births"], 0)
            self.assertEqual(a["variants"]["no_food"]["births"], 0)
            self.assertEqual(a["variants"]["faithful"]["total_bytes_mutated"], 0)
            self.assertTrue(all(v["invalid_births"] == 0 for v in a["variants"].values()))
            self.assertEqual(json.loads((dest / "summary.json").read_text())["source_revision"],
                             "test-revision")

    def test_prohibited_host_code_not_expressible_by_virtual_alphabet(self):
        self.assertEqual(len(ALPHABET), 6)
        self.assertFalse(hasattr(World, "execute_shell"))
        self.assertFalse(hasattr(World, "browse_web"))
        self.assertFalse(hasattr(World, "write_source_code"))


if __name__ == "__main__":
    unittest.main()
