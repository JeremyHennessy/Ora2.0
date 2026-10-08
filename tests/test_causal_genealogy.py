"""AL07-TRACE adversarial tests on development worlds only (NOT original heldout)."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from experiments.executed_heredity import World, VARIANTS, canonical
from experiments.causal_genealogy_audit import (
    ORIGINAL_SHA256, audit_world, analyze_dataset, genotype_hash
)


def fixture(seed=3, variant="faithful", ticks=140, **kwargs):
    world = World(seed, variant=variant, **kwargs)
    meta = world.run(ticks)
    events = [{"seed": seed, "variant": variant, **e} for e in world.events]
    births = [{"seed": seed, "variant": variant, **b} for b in world.births]
    return events, births, meta


def audited(events=None, births=None, meta=None):
    if events is None:
        events, births, meta = fixture()
    return audit_world(events, births, meta)


class CausalLineageTests(unittest.TestCase):
    def setUp(self):
        self.events, self.births, self.meta = fixture(seed=3, food_a=8, food_b=3)
        self.assertGreater(len(self.births), 0)

    def test_original_untampered_stream_passes(self):
        r = audited(self.events, self.births, self.meta)
        self.assertTrue(r["valid"], r["errors"][:5])
        self.assertEqual(r["birth_count"], len(self.births))
        self.assertEqual(r["independent_energy_residual_max"], 0)
        self.assertGreaterEqual(r["max_generation"], 1)

    def test_mutating_development_world_also_passes(self):
        events, births, meta = fixture(seed=2, variant="mutating", ticks=200)
        result = audited(events, births, meta)
        self.assertTrue(result["valid"], result["errors"][:5])

    def test_copy_disabled_and_no_food_are_valid_nulls(self):
        for variant in ("copy_disabled", "no_food"):
            events, births, meta = fixture(seed=5, variant=variant)
            result = audited(events, births, meta)
            self.assertTrue(result["valid"], (variant, result["errors"][:5]))
            self.assertEqual(result["birth_count"], 0)

    def test_forged_birth_receipt_rejected(self):
        births = deepcopy(self.births)
        forged = dict(births[0], child_id=999, event_id=100000)
        births.append(forged)
        result = audited(self.events, births, self.meta)
        self.assertFalse(result["valid"])
        self.assertIn("birth_stream_and_certificate_ids_mismatch",
                      {e["reason"] for e in result["errors"]})

    def test_swapped_parent_even_identical_genotype_rejected(self):
        births = deepcopy(self.births)
        births[0]["parent_id"] = 55
        result = audited(self.events, births, self.meta)
        self.assertFalse(result["valid"])

    def test_missing_write_events_rejected(self):
        events = [e for e in self.events if e["kind"] != "COPY_WRITE"]
        result = audited(events, self.births, self.meta)
        self.assertFalse(result["valid"])

    def test_write_material_cloned_while_active_rejected(self):
        events = deepcopy(self.events)
        writes = [e for e in events if e["kind"] == "COPY_WRITE"]
        self.assertGreaterEqual(len(writes), 2)
        writes[1]["material_unit"] = writes[0]["material_unit"]
        result = audited(events, self.births, self.meta)
        self.assertFalse(result["valid"])
        self.assertIn("simultaneously_owned_material_unit",
                      {e["reason"] for e in result["errors"]})

    def test_duplicate_event_id_and_time_reversal_rejected(self):
        events = deepcopy(self.events)
        events[5]["event_id"] = events[4]["event_id"]
        self.assertFalse(audited(events, self.births, self.meta)["valid"])
        events = deepcopy(self.events)
        events[5]["tick"] = -1
        self.assertFalse(audited(events, self.births, self.meta)["valid"])

    def test_mismatch_parent_program_and_offspring_bytes_rejected(self):
        events = deepcopy(self.events)
        b = next(e for e in events if e["kind"] == "BIRTH")
        b["child_genome_ops"] = [5, 2, 3, 4]
        b["child_genome_hash"] = genotype_hash(b["child_genome_ops"])
        self.assertFalse(audited(events, self.births, self.meta)["valid"])

    def test_missing_corresponding_execute_rejected(self):
        events = deepcopy(self.events)
        idx = next(i for i, e in enumerate(events) if e["kind"] == "COPY_WRITE")
        self.assertEqual(events[idx+1]["kind"], "EXEC")
        events[idx+1]["opcode"] = 5
        result = audited(events, self.births, self.meta)
        self.assertFalse(result["valid"])
        self.assertIn("copy_or_birth_without_immediate_executed_instruction",
                      {e["reason"] for e in result["errors"]})

    def test_illegal_energy_injection_rejected(self):
        events = deepcopy(self.events)
        exec_ = next(e for e in events if e["kind"] == "EXEC")
        exec_["energy_after"] += 1
        result = audited(events, self.births, self.meta)
        self.assertFalse(result["valid"])

    def test_forged_after_death_parent_rejected(self):
        events = deepcopy(self.events)
        dead = next(e for e in events if e["kind"] == "DEATH")
        original = next(e for e in events if e["kind"] == "COPY_WRITE")
        forged = deepcopy(original)
        forged.update(event_id=len(events), tick=events[-1]["tick"]+1,
                      parent_id=dead["organism_id"])
        events.append(forged)
        self.assertFalse(audited(events, self.births, self.meta)["valid"])

    def test_copies_must_use_legal_current_source_tape(self):
        events = deepcopy(self.events)
        write = next(e for e in events if e["kind"] == "COPY_WRITE")
        write["source_op"] = 5
        self.assertFalse(audited(events, self.births, self.meta)["valid"])

    def test_counterfeited_summary_with_no_births_rejected(self):
        meta = dict(self.meta, birth_count=0)
        self.assertFalse(audited(self.events, self.births, meta)["valid"])


class RecordedDataTests(unittest.TestCase):
    def test_dev_fixture_dataset_has_no_unauthorized_leak(self):
        with tempfile.TemporaryDirectory() as td:
            input_dir = Path(td) / "inputs"
            output_dir = Path(td) / "audit"
            input_dir.mkdir()
            records = {"worlds.jsonl": [], "births.jsonl": [], "events.jsonl": []}
            for variant in VARIANTS:
                events, births, meta = fixture(4, variant, 120)
                records["worlds.jsonl"].append(meta)
                records["births.jsonl"].extend(births)
                records["events.jsonl"].extend(events)
            for name, values in records.items():
                (input_dir / name).write_text("".join(canonical(v)+"\n" for v in values), encoding="utf-8")
            result = analyze_dataset(input_dir, output_dir, require_original_hashes=False)
            self.assertEqual(result["worlds"], 4)
            self.assertEqual(result["invalid_worlds"], 0)
            self.assertEqual(result["births"], len(records["births.jsonl"]))
            self.assertEqual(len((output_dir/"genealogy-worlds.jsonl").read_text().splitlines()), 4)
            self.assertEqual(json.loads((output_dir/"genealogy-summary.json").read_text())["invalid_worlds"], 0)
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                analyze_dataset(input_dir, output_dir, require_original_hashes=True)

    def test_expected_original_artifact_hashes_frozen(self):
        self.assertEqual(set(ORIGINAL_SHA256),
                         {"worlds.jsonl", "births.jsonl", "events.jsonl"})
        self.assertTrue(all(len(v) == 64 for v in ORIGINAL_SHA256.values()))


if __name__ == "__main__":
    unittest.main()
