"""AL02-COPY: sandboxed virtual instruction reproduction with byte provenance.

Synthetic, investigator-seeded self-copying *positive control* only.
See frozen docs/AL02-COPY-PROTOCOL.md. No host-call bytecodes exist.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
import platform
import random
from typing import Iterable

EAT_A = 0
EAT_B = 1
COPY = 2
LOOP = 3
DIVIDE = 4
NOP = 5
ALPHABET = tuple(range(6))
SEED_TAPE = (EAT_A, COPY, LOOP, DIVIDE)
VARIANTS = ("mutating", "faithful", "copy_disabled", "no_food")
ENERGY_PER_FOOD = 20
INITIAL_ORGANISM_ENERGY = 4
CHILD_ENERGY = 4
MATERIAL_UNITS = 256
POPULATION_LIMIT = 64
MAX_STEPS = 600


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def genotype_hash(ops: Iterable[int]) -> str:
    return sha256(canonical(list(ops)))


@dataclass(frozen=True)
class Gene:
    op: int
    material_unit: int


@dataclass
class Organism:
    organism_id: int
    tape: tuple[Gene, ...]
    energy: int
    generation: int
    parent_id: int | None
    born_tick: int
    pc: int = 0
    read_head: int = 0
    nursery: list[Gene] = field(default_factory=list)
    nursery_write_ids: list[int] = field(default_factory=list)

    def ops(self) -> tuple[int, ...]:
        return tuple(g.op for g in self.tape)

    def tape_hash(self) -> str:
        return genotype_hash(self.ops())


class World:
    """A fully bounded pure-Python virtual machine, never a host-code agent."""

    def __init__(
        self, seed: int, *, variant: str = "mutating",
        founder_ops: tuple[int, ...] = SEED_TAPE,
        food_a: int = 12, food_b: int = 18,
        material_units: int = MATERIAL_UNITS,
        population_limit: int = POPULATION_LIMIT,
        initial_energy: int = INITIAL_ORGANISM_ENERGY,
        mutation_rate: float = 0.08,
    ) -> None:
        if variant not in VARIANTS:
            raise ValueError("Unknown experimental variant")
        if seed < 0 or len(founder_ops) == 0 or len(founder_ops) > material_units:
            raise ValueError("Invalid seed, tape or available material")
        if any(op not in ALPHABET for op in founder_ops):
            raise ValueError("Invalid data-only opcode")
        if min(food_a, food_b, initial_energy, material_units) < 0:
            raise ValueError("Negative resource")
        if population_limit < 1 or not 0 <= mutation_rate <= 1:
            raise ValueError("Invalid population limit or mutation rate")
        self.seed = seed
        self.variant = variant
        self.rng = random.Random(seed)
        self.copy_enabled = variant != "copy_disabled"
        self.mutation_rate = mutation_rate if variant in ("mutating", "copy_disabled", "no_food") else 0.0
        self.food_a = food_a if variant != "no_food" else 0
        self.food_b = food_b if variant != "no_food" else 0
        self.material_units = material_units
        self.population_limit = population_limit
        self.heat = 0
        self.tick_count = 0
        self.last_actor = -1
        self.next_organism_id = 1
        self.free_units = set(range(len(founder_ops), material_units))
        self.genesis_energy = initial_energy + ENERGY_PER_FOOD * (self.food_a + self.food_b)
        self.genesis_material = material_units
        founder_tape = tuple(Gene(op, i) for i, op in enumerate(founder_ops))
        self.organisms: dict[int, Organism] = {
            0: Organism(0, founder_tape, initial_energy, 0, None, 0)
        }
        self.events: list[dict] = []
        self.births: list[dict] = []
        self.deaths = 0
        self.max_population_seen = 1
        self.mutations_written = 0
        self.failed_divisions = 0
        self.failed_copy = 0
        self.energy_residual_max = 0
        self.material_residual_max = 0
        self.emit(
            "GENESIS",
            organism_id=0,
            tape_ops=list(founder_ops),
            tape_units=list(range(len(founder_ops))),
            food_a=self.food_a, food_b=self.food_b,
            energy=initial_energy, free_material=len(self.free_units),
        )
        self.assert_invariants()

    def emit(self, kind: str, **payload: object) -> int:
        seq = len(self.events)
        self.events.append({"event_id": seq, "tick": self.tick_count, "kind": kind, **payload})
        return seq

    def assert_invariants(self) -> tuple[int, int]:
        tapes = [
            g.material_unit
            for org in self.organisms.values()
            for g in (*org.tape, *org.nursery)
        ]
        combined = tapes + list(self.free_units)
        if len(combined) != self.material_units or len(set(combined)) != self.material_units:
            raise AssertionError("Material units duplicated/lost")
        if set(combined) != set(range(self.material_units)):
            raise AssertionError("Material unit identifier missing/outside pool")
        if any(o.energy < 0 for o in self.organisms.values()):
            raise AssertionError("Negative organism energy")
        if min(self.food_a, self.food_b, self.heat) < 0:
            raise AssertionError("Negative energy compartment")
        material_residual = len(combined) - self.genesis_material
        actual_energy = (
            sum(o.energy for o in self.organisms.values())
            + ENERGY_PER_FOOD * (self.food_a + self.food_b)
            + self.heat
        )
        energy_residual = actual_energy - self.genesis_energy
        self.energy_residual_max = max(self.energy_residual_max, abs(energy_residual))
        self.material_residual_max = max(self.material_residual_max, abs(material_residual))
        if material_residual or energy_residual:
            raise AssertionError(f"Resource violation: material {material_residual}, energy {energy_residual}")
        if len(self.organisms) > self.population_limit:
            raise AssertionError("Population exceeded physical cap")
        return material_residual, energy_residual

    def die(self, org: Organism, reason: str) -> None:
        if org.organism_id not in self.organisms:
            raise AssertionError("Organism died twice")
        self.free_units.update(g.material_unit for g in (*org.tape, *org.nursery))
        energy_released = org.energy
        self.heat += energy_released
        org.energy = 0
        self.organisms.pop(org.organism_id)
        self.deaths += 1
        self.emit("DEATH", organism_id=org.organism_id, reason=reason,
                  energy_released=energy_released, abandoned_nursery=len(org.nursery))

    def next_actor(self) -> Organism | None:
        if not self.organisms:
            return None
        ids = sorted(self.organisms)
        choice = next((i for i in ids if i > self.last_actor), ids[0])
        self.last_actor = choice
        return self.organisms[choice]

    def execute_one(self) -> None:
        org = self.next_actor()
        if org is None:
            return
        self.tick_count += 1
        if org.pc < 0 or org.pc >= len(org.tape):
            self.emit("FAULT", organism_id=org.organism_id,
                      reason="pc_outside_tape", pc=org.pc)
            self.die(org, "pc_outside_tape")
            self.assert_invariants()
            return
        pc_before = org.pc
        opcode = org.tape[pc_before].op
        energy_before = org.energy
        if org.energy < 1:
            self.die(org, "no_energy")
            self.assert_invariants()
            return
        org.energy -= 1
        self.heat += 1
        outcome = "executed"
        if opcode in (EAT_A, EAT_B):
            if opcode == EAT_A and self.food_a > 0:
                self.food_a -= 1
                org.energy += ENERGY_PER_FOOD
                outcome = "ate_a"
            elif opcode == EAT_B and self.food_b > 0:
                self.food_b -= 1
                org.energy += ENERGY_PER_FOOD
                outcome = "ate_b"
            else:
                outcome = "food_unavailable"
            org.pc += 1
        elif opcode == COPY:
            if not self.copy_enabled:
                outcome = "copy_disabled"
                self.failed_copy += 1
            elif org.read_head >= len(org.tape):
                outcome = "nursery_already_complete"
            elif org.energy < 1 or not self.free_units:
                outcome = "copy_material_or_energy_missing"
                self.failed_copy += 1
            else:
                org.energy -= 1
                self.heat += 1
                source = org.tape[org.read_head]
                original_op = source.op
                emit_op = original_op
                if self.rng.random() < self.mutation_rate:
                    choices = tuple(op for op in ALPHABET if op != original_op)
                    emit_op = choices[self.rng.randrange(len(choices))]
                token_id = min(self.free_units)
                self.free_units.remove(token_id)
                slot = len(org.nursery)
                # The only way material enters a nursery is this executed byte write.
                org.nursery.append(Gene(emit_op, token_id))
                event_id = self.emit(
                    "COPY_WRITE",
                    parent_id=org.organism_id,
                    parent_genome_hash=org.tape_hash(),
                    source_index=org.read_head,
                    source_material_unit=source.material_unit,
                    source_op=original_op,
                    material_unit=token_id,
                    written_op=emit_op,
                    mutated=(emit_op != original_op),
                    nursery_index=slot,
                    paid_energy=2,
                )
                org.nursery_write_ids.append(event_id)
                org.read_head += 1
                self.mutations_written += int(emit_op != original_op)
                outcome = "copied_one_byte"
            org.pc += 1
        elif opcode == LOOP:
            org.pc = 1 if org.read_head < len(org.tape) else pc_before + 1
            outcome = "loop_copy" if org.pc == 1 else "loop_finished"
        elif opcode == DIVIDE:
            tape_length = len(org.tape)
            if (len(org.nursery) == tape_length
                and len(org.nursery_write_ids) == tape_length
                and org.energy >= (2 + CHILD_ENERGY)
                and len(self.organisms) < self.population_limit):
                org.energy -= (2 + CHILD_ENERGY)
                self.heat += 2
                daughter_id = self.next_organism_id
                self.next_organism_id += 1
                # Moving already-written material, NEVER reading/copying the parent tape here.
                daughter_tape = tuple(org.nursery)
                daughter = Organism(
                    daughter_id, daughter_tape, CHILD_ENERGY,
                    org.generation + 1, org.organism_id, self.tick_count
                )
                self.organisms[daughter_id] = daughter
                receipt = {
                    "parent_id": org.organism_id,
                    "child_id": daughter_id,
                    "parent_genome_hash": org.tape_hash(),
                    "parent_genome_ops": list(org.ops()),
                    "child_genome_hash": daughter.tape_hash(),
                    "child_genome_ops": list(daughter.ops()),
                    "child_material_units": [g.material_unit for g in daughter_tape],
                    "copy_event_ids": list(org.nursery_write_ids),
                    "generation": daughter.generation,
                    "transferred_energy": CHILD_ENERGY,
                    "genesis_seeded": False,
                }
                birth_event_id = self.emit("BIRTH", **receipt)
                receipt["event_id"] = birth_event_id
                self.births.append(receipt)
                org.nursery.clear()
                org.nursery_write_ids.clear()
                org.read_head = 0
                outcome = "executed_division"
            else:
                self.failed_divisions += 1
                outcome = "division_blocked"
            org.pc = 0
        elif opcode == NOP:
            org.pc += 1
            outcome = "nop"
        else:
            raise AssertionError("Interpreter did not enforce opcode alphabet")
        self.emit(
            "EXEC",
            organism_id=org.organism_id,
            opcode=opcode, pc_before=pc_before, pc_after=org.pc,
            energy_before=energy_before, energy_after=org.energy,
            read_head_after=org.read_head,
            nursery_bytes_after=len(org.nursery),
            outcome=outcome, food_a=self.food_a, food_b=self.food_b,
            population_after_instruction=len(self.organisms),
            heat=self.heat,
        )
        if org.energy <= 0 and org.organism_id in self.organisms:
            self.die(org, "energy_exhausted")
        self.max_population_seen = max(self.max_population_seen, len(self.organisms))
        self.assert_invariants()

    def run(self, maximum_ticks: int = MAX_STEPS) -> dict:
        if maximum_ticks < 0:
            raise ValueError("Negative world horizon")
        while self.tick_count < maximum_ticks and self.organisms:
            self.execute_one()
        copied = sum(1 for e in self.events if e["kind"] == "COPY_WRITE")
        food_consumed_a = (
            (12 if self.variant != "no_food" else 0) - self.food_a
            if False else None
        )
        return {
            "seed": self.seed,
            "variant": self.variant,
            "ticks": self.tick_count,
            "world_extinct": not bool(self.organisms),
            "live_count": len(self.organisms),
            "max_population": self.max_population_seen,
            "birth_count": len(self.births),
            "death_count": self.deaths,
            "copy_events": copied,
            "mutated_bytes_written": self.mutations_written,
            "failed_copy_attempts": self.failed_copy,
            "failed_divisions": self.failed_divisions,
            "remaining_food_a": self.food_a,
            "remaining_food_b": self.food_b,
            "remaining_material": len(self.free_units),
            "heat": self.heat,
            "max_material_residual": self.material_residual_max,
            "max_energy_residual": self.energy_residual_max,
            "genesis_energy": self.genesis_energy,
            "genesis_material": self.genesis_material,
            "remaining_tapes": [list(o.ops()) for o in self.organisms.values()],
        }


def single_world(seed: int, variant: str = "mutating", **kwargs: object) -> tuple[dict, list[dict], list[dict]]:
    world = World(seed, variant=variant, **kwargs)
    summary = world.run()
    return summary, world.births, world.events


def study(output: Path, seeds: list[int], revision: str = "unspecified") -> dict:
    """Run *all* registered worlds and preserve raw events (including failures)."""
    if not seeds or len(set(seeds)) != len(seeds) or any(s < 0 for s in seeds):
        raise ValueError("Expected nonempty unique nonnegative seeds")
    from experiments.lineage_audit import audit_births
    output.mkdir(parents=True, exist_ok=True)
    by_world: list[dict] = []
    all_births: list[dict] = []
    digests = {f: hashlib.sha256() for f in ("worlds.jsonl", "births.jsonl", "events.jsonl")}
    target_mutant_receipt: dict | None = None
    with (output / "worlds.jsonl").open("w", encoding="utf-8") as f_world, (
            output / "births.jsonl").open("w", encoding="utf-8") as f_birth, (
            output / "events.jsonl").open("w", encoding="utf-8") as f_event:
        for seed in seeds:
            for variant in VARIANTS:
                summary, births, events = single_world(seed, variant)
                audit = audit_births(births, events)
                summary["audit"] = audit
                if audit["invalid_births"] != 0 or audit["valid_births"] != len(births):
                    raise AssertionError("Invalid birth provenance")
                for file, entries, handle in (
                    ("worlds.jsonl", [summary], f_world),
                    ("births.jsonl", [{"seed": seed, "variant": variant, **b} for b in births], f_birth),
                    ("events.jsonl", [{"seed": seed, "variant": variant, **e} for e in events], f_event),
                ):
                    for record in entries:
                        raw = canonical(record) + "\n"
                        handle.write(raw)
                        digests[file].update(raw.encode("utf-8"))
                by_world.append(summary)
                all_births.extend({"seed": seed, "variant": variant, **b} for b in births)
                if target_mutant_receipt is None and variant == "mutating":
                    for b in births:
                        if b["child_genome_ops"] == [EAT_B, COPY, LOOP, DIVIDE]:
                            target_mutant_receipt = {"seed": seed, "receipt": b}
                            break
    variant_totals = {}
    for variant in VARIANTS:
        subset = [w for w in by_world if w["variant"] == variant]
        variant_totals[variant] = {
            "worlds": len(subset),
            "births": sum(w["birth_count"] for w in subset),
            "worlds_with_births": sum(w["birth_count"] > 0 for w in subset),
            "world_extinctions": sum(w["world_extinct"] for w in subset),
            "total_bytes_mutated": sum(w["mutated_bytes_written"] for w in subset),
            "total_copy_events": sum(w["copy_events"] for w in subset),
            "invalid_births": sum(w["audit"]["invalid_births"] for w in subset),
            "maximum_energy_residual": max(w["max_energy_residual"] for w in subset),
            "maximum_material_residual": max(w["max_material_residual"] for w in subset),
        }
    # An assay of a pre-known resource-choice instruction; not emergent invention.
    assay = {"candidate_observed": target_mutant_receipt is not None}
    if target_mutant_receipt:
        assayed = {}
        for label, tape in (
            ("ancestor_eat_a", SEED_TAPE),
            ("mutant_eat_b", (EAT_B, COPY, LOOP, DIVIDE)),
        ):
            w = World(771177, variant="faithful", founder_ops=tape,
                      food_a=0, food_b=3, mutation_rate=0.0)
            result = w.run(40)
            aud = audit_births(w.births, w.events)
            assayed[label] = {
                "birth_count": result["birth_count"],
                "has_birth": result["birth_count"] > 0,
                "audit": aud,
            }
        assay.update({
            "original_birth_source": {
                "seed": target_mutant_receipt["seed"],
                "parent_id": target_mutant_receipt["receipt"]["parent_id"],
                "child_id": target_mutant_receipt["receipt"]["child_id"],
                "birth_event_id": target_mutant_receipt["receipt"]["event_id"],
            },
            "blue_only_resource_assay": assayed,
            "limits": "Designed nutrient-specific opcode; selected first target mutant after screening. Not de novo cognition.",
        })
    # Second-generation identity with exact transmitted mutant program:
    birth_ids = {(b["seed"], b["child_id"]): b for b in all_births if b["variant"] == "mutating"}
    mutated_births = [
        b for b in all_births if b["variant"] == "mutating"
        and b["child_genome_ops"] != b["parent_genome_ops"]
    ]
    faithful_mutant_grandchildren = [
        b for b in all_births if b["variant"] == "mutating"
        and (b["seed"], b["parent_id"]) in birth_ids
        and birth_ids[(b["seed"], b["parent_id"])]["child_genome_ops"]
            != birth_ids[(b["seed"], b["parent_id"])]["parent_genome_ops"]
        and b["child_genome_ops"]
            == birth_ids[(b["seed"], b["parent_id"])]["child_genome_ops"]
    ]
    output_summary = {
        "experiment": "AL02-COPY",
        "status": "engineered_virtual_replicator_not_artificial_life",
        "source_revision": revision,
        "python": platform.python_version(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "protocol": "docs/AL02-COPY-PROTOCOL.md",
        "seed_list": seeds,
        "variant_order": list(VARIANTS),
        "world_count": len(by_world),
        "variation": "substitution-only in 4-token genome, no genome growth or spontaneous genesis",
        "variants": variant_totals,
        "lineage_mutated_births": len(mutated_births),
        "faithfully_inherited_mutant_grandchildren": len(faithful_mutant_grandchildren),
        "resource_choice_assay": assay,
        "worlds_sha256": digests["worlds.jsonl"].hexdigest(),
        "births_sha256": digests["births.jsonl"].hexdigest(),
        "events_sha256": digests["events.jsonl"].hexdigest(),
        "total_births": len(all_births),
        "total_recorded_events": sum(
            1 for _ in (output / "events.jsonl").open(encoding="utf-8")
        ),
        "meaning": (
            "Positive outcomes can demonstrate executed copying and heritable "
            "opcode changes inside a deliberately designed interpreter, NOT "
            "spontaneous life, autonomous metabolism or open-ended evolution."
        ),
    }
    if variant_totals["copy_disabled"]["births"] or variant_totals["no_food"]["births"]:
        raise AssertionError("The no-copy or no-food control unexpectedly reproduced")
    if variant_totals["faithful"]["total_bytes_mutated"]:
        raise AssertionError("No-mutation control leaked a mutated byte")
    (output / "summary.json").write_text(
        json.dumps(output_summary, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return output_summary


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seeds", default="5000:5064", help="half-open start:end")
    p.add_argument("--output-dir", type=Path, default=Path("runs/al02-copy"))
    p.add_argument("--source-revision", default="unspecified")
    args = p.parse_args(argv)
    try:
        lo, hi = (int(v) for v in args.seeds.split(":", 1))
        if lo < 0 or hi <= lo:
            raise ValueError()
    except ValueError:
        p.error("Expected nonnegative half-open --seeds start:end")
    out = study(args.output_dir, list(range(lo, hi)), revision=args.source_revision)
    print(json.dumps({
        "world_count": out["world_count"],
        "variants": out["variants"],
        "mutated_births": out["lineage_mutated_births"],
        "mutant_grandchildren": out["faithfully_inherited_mutant_grandchildren"],
        "resource_choice_assay": out["resource_choice_assay"],
        "total_events": out["total_recorded_events"],
        "interpretation": "executed heredity positive-control, not digital organismhood",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
