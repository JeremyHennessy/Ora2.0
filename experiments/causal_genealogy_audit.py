"""AL07-TRACE: read-only, independent event-stream genealogy and material auditor.

The input is previously recorded JSONL data. No organism simulation, code evaluation,
model execution, or external access is performed. See docs/AL07-TRACE-PROTOCOL.md.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
import argparse
import hashlib
import json
from pathlib import Path

ORIGINAL_SHA256 = {
    "worlds.jsonl": "684f135f8f59261877414901a1d3f5e5b114a93ce83710e348cc82030de35d7f",
    "births.jsonl": "88cc94dda7bc00173e4ddfd0fdd8a3af0082b7f78926b4ad6e0e26838318fd44",
    "events.jsonl": "8d0872972a15c53155658df493d2ce10e1b00d34bb75e2b1f543fdab5820d7a5",
}
VARIANTS = ("mutating", "faithful", "copy_disabled", "no_food")
VALID_OPS = frozenset(range(6))
COST_PER_FOOD = 20


def normalized(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def genotype_hash(ops: list[int]) -> str:
    return hashlib.sha256(normalized(ops).encode("utf-8")).hexdigest()


@dataclass
class Entity:
    entity_id: int
    ops: list[int]
    units: list[int]
    generation: int
    parent_id: int | None
    born_tick: int
    energy: int
    pc: int = 0
    read_head: int = 0
    nursery: list[dict] = field(default_factory=list)
    death_tick: int | None = None


def audit_world(events: list[dict], births: list[dict], world: dict) -> dict:
    """Process causal history without trusting the simulator's original audit flag."""
    errors: list[dict] = []
    alive: dict[int, Entity] = {}
    all_entities: dict[int, Entity] = {}
    occupied: dict[int, tuple[int, str]] = {}
    ever_allocated: set[int] = set()
    parent_children: dict[int, list[int]] = defaultdict(list)
    seen_birth_events: dict[int, dict] = {}
    expected_event_id = 0
    last_tick = -1
    pending = None
    genesis = None
    resource_state = {"a": None, "b": None, "heat": 0}
    total_energy = None
    total_material = world.get("genesis_material", 256)
    reuse_count = 0
    copy_count = 0
    death_count = 0
    fault_count = 0
    maximum_energy_residual = 0
    entities_released = 0
    tick_actors: dict[int, int] = {}

    def fail(event_id: int | None, reason: str, **extra: object) -> None:
        errors.append({"event_id": event_id, "reason": reason, **extra})

    def check_energy(eid: int) -> None:
        nonlocal maximum_energy_residual
        if total_energy is None:
            return
        observed = (
            sum(node.energy for node in alive.values())
            + (resource_state["a"] + resource_state["b"]) * COST_PER_FOOD
            + resource_state["heat"]
        )
        resid = observed - total_energy
        maximum_energy_residual = max(maximum_energy_residual, abs(resid))
        if resid:
            fail(eid, "inconsistent_independent_energy_ledger", residual=resid)

    for event in events:
        eid, tick, kind = event.get("event_id"), event.get("tick"), event.get("kind")
        if not isinstance(eid, int) or eid != expected_event_id:
            fail(eid, "noncontiguous_event_ids", expected=expected_event_id)
        expected_event_id += 1
        if not isinstance(tick, int) or tick < last_tick:
            fail(eid, "nonmonotonic_simulated_time")
            tick = last_tick
        last_tick = tick
        if (event.get("seed"), event.get("variant")) != (
            world.get("seed"), world.get("variant")
        ):
            fail(eid, "event_wrong_world")
        matched_pending = None
        if pending is not None:
            matched_pending = pending
            if not (
                kind == "EXEC"
                and event.get("organism_id") == pending["parent_id"]
                and tick == pending["tick"]
                and event.get("opcode") == pending["opcode"]
                and event.get("outcome") == pending["outcome"]
            ):
                fail(eid, "copy_or_birth_without_immediate_executed_instruction",
                     source_event=pending["event_id"])
                matched_pending = None
            pending = None

        if kind == "GENESIS":
            if genesis is not None or eid != 0 or tick != 0:
                fail(eid, "duplicate_or_misplaced_genesis")
                continue
            genesis = event
            tape = event.get("tape_ops")
            units = event.get("tape_units")
            if not isinstance(tape, list) or not isinstance(units, list) or not tape or len(tape) != len(units):
                fail(eid, "invalid_genesis_tape")
                continue
            if any(not isinstance(op, int) or op not in VALID_OPS for op in tape):
                fail(eid, "invalid_genesis_opcode")
            if any(not isinstance(x, int) or x < 0 or x >= total_material for x in units) or len(set(units)) != len(units):
                fail(eid, "duplicate_or_invalid_genesis_material")
            org = Entity(0, list(tape), list(units), 0, None, tick, event.get("energy", 0))
            alive[0] = org
            all_entities[0] = org
            for unit in units:
                occupied[unit] = (0, "tape")
                ever_allocated.add(unit)
            if event.get("free_material") != total_material - len(units):
                fail(eid, "genesis_free_material_count_mismatch")
            resource_state["a"] = event.get("food_a")
            resource_state["b"] = event.get("food_b")
            if not all(isinstance(resource_state[k], int) and resource_state[k] >= 0 for k in ("a", "b")):
                fail(eid, "invalid_genesis_resource_counts")
                continue
            total_energy = (org.energy +
                            COST_PER_FOOD * (resource_state["a"] + resource_state["b"]))
            if total_energy != world.get("genesis_energy"):
                fail(eid, "genesis_energy_manifest_mismatch")
        elif kind == "COPY_WRITE":
            copy_count += 1
            parent = alive.get(event.get("parent_id"))
            if parent is None:
                fail(eid, "write_parent_not_alive")
                continue
            slot = event.get("source_index")
            unit = event.get("material_unit")
            if not isinstance(slot, int) or slot != parent.read_head or slot >= len(parent.ops):
                fail(eid, "write_source_head_not_executed_in_order")
                continue
            if (event.get("source_op") != parent.ops[slot]
                or event.get("source_material_unit") != parent.units[slot]
                or event.get("parent_genome_hash") != genotype_hash(parent.ops)):
                fail(eid, "write_does_not_match_active_parent_tape")
            if (event.get("nursery_index") != len(parent.nursery)
                or event.get("paid_energy") != 2):
                fail(eid, "write_not_next_paid_nursery_slot")
            if not isinstance(unit, int) or not 0 <= unit < total_material:
                fail(eid, "write_invalid_material_unit")
                continue
            if unit in occupied:
                fail(eid, "simultaneously_owned_material_unit", unit=unit,
                     existing_owner=occupied[unit])
            elif unit in ever_allocated:
                reuse_count += 1
            ever_allocated.add(unit)
            occupied[unit] = (parent.entity_id, "nursery")
            op = event.get("written_op")
            if op not in VALID_OPS or event.get("mutated") != (op != parent.ops[slot]):
                fail(eid, "invalid_written_opcode_or_mutation_flag")
            parent.nursery.append({"event_id": eid, "unit": unit, "op": op, "source_index": slot})
            pending = {"event_id": eid, "tick": tick, "parent_id": parent.entity_id,
                       "opcode": 2, "outcome": "copied_one_byte"}
        elif kind == "BIRTH":
            pid, cid = event.get("parent_id"), event.get("child_id")
            parent = alive.get(pid)
            if parent is None:
                fail(eid, "birth_parent_not_alive")
                continue
            if not isinstance(cid, int) or cid <= pid or cid in all_entities:
                fail(eid, "invalid_or_duplicate_child_id")
                continue
            if event.get("generation") != parent.generation + 1:
                fail(eid, "wrong_birth_generation")
            if event.get("genesis_seeded") is not False or event.get("transferred_energy") != 4:
                fail(eid, "invalid_child_energy_or_genesis_flag")
            expected_ids = [row["event_id"] for row in parent.nursery]
            expected_units = [row["unit"] for row in parent.nursery]
            expected_ops = [row["op"] for row in parent.nursery]
            if (len(parent.nursery) != len(parent.ops) or
                event.get("copy_event_ids") != expected_ids or
                event.get("child_material_units") != expected_units or
                event.get("child_genome_ops") != expected_ops):
                fail(eid, "birth_does_not_transfer_complete_executed_nursery")
            if (event.get("parent_genome_ops") != parent.ops or
                event.get("parent_genome_hash") != genotype_hash(parent.ops) or
                event.get("child_genome_hash") != genotype_hash(expected_ops)):
                fail(eid, "incorrect_birth_parent_or_child_genome_hash")
            for unit in expected_units:
                if occupied.get(unit) != (pid, "nursery"):
                    fail(eid, "birth_material_not_from_parent_nursery", unit=unit)
                occupied[unit] = (cid, "tape")
            child = Entity(cid, expected_ops, expected_units,
                           parent.generation + 1, pid, tick, 4)
            alive[cid] = child
            all_entities[cid] = child
            parent.nursery.clear()
            parent_children[pid].append(cid)
            seen_birth_events[eid] = event
            pending = {"event_id": eid, "tick": tick, "parent_id": pid,
                       "opcode": 4, "outcome": "executed_division"}
        elif kind == "EXEC":
            actor_id = event.get("organism_id")
            actor = alive.get(actor_id)
            if actor is None:
                fail(eid, "execution_by_dead_or_unknown_entity")
                continue
            if tick in tick_actors and tick_actors[tick] != actor_id:
                fail(eid, "multiple_entities_executed_same_tick")
            tick_actors[tick] = actor_id
            pc = event.get("pc_before")
            if not isinstance(pc, int) or pc != actor.pc or not 0 <= pc < len(actor.ops):
                fail(eid, "invalid_executed_program_counter")
                continue
            op = actor.ops[pc]
            if event.get("opcode") != op:
                fail(eid, "executed_opcode_not_active_program")
            if event.get("energy_before") != actor.energy:
                fail(eid, "executed_energy_before_mismatch")
            outcome = event.get("outcome")
            expected_cost = 1
            if outcome == "copied_one_byte":
                if op != 2 or matched_pending is None or matched_pending["opcode"] != 2:
                    fail(eid, "copy_opcode_without_prior_write")
                expected_cost = 2
                actor.read_head += 1
            elif outcome == "executed_division":
                if op != 4 or matched_pending is None or matched_pending["opcode"] != 4:
                    fail(eid, "division_opcode_without_prior_birth")
                expected_cost = 7
                actor.read_head = 0
            else:
                if matched_pending is not None:
                    fail(eid, "receipt_not_confirmed_by_executor")
            gain = 0
            if outcome == "ate_a" and op == 0 and resource_state["a"] > 0:
                resource_state["a"] -= 1
                gain = COST_PER_FOOD
            elif outcome == "ate_b" and op == 1 and resource_state["b"] > 0:
                resource_state["b"] -= 1
                gain = COST_PER_FOOD
            elif outcome in ("ate_a", "ate_b"):
                fail(eid, "food_consumed_without_corresponding_resource")
            expected_energy = actor.energy - expected_cost + gain
            if event.get("energy_after") != expected_energy:
                fail(eid, "executed_energy_after_mismatch")
            actor.energy = expected_energy
            resource_state["heat"] += expected_cost - (4 if outcome == "executed_division" else 0)
            # DIVIDE's 7-unit cost is: 1 instruction +2 heat +4 child endowment.
            expected_pc = (1 if actor.read_head < len(actor.ops) else pc + 1) if op == 3 else (
                0 if op == 4 else pc + 1
            )
            if event.get("pc_after") != expected_pc:
                fail(eid, "executed_next_pc_mismatch")
            actor.pc = expected_pc
            if (event.get("read_head_after") != actor.read_head or
                event.get("nursery_bytes_after") != len(actor.nursery)):
                fail(eid, "executor_does_not_confirm_nursery_progress")
            if (event.get("food_a") != resource_state["a"] or
                event.get("food_b") != resource_state["b"] or
                event.get("heat") != resource_state["heat"]):
                fail(eid, "executor_resource_receipt_mismatch")
            if event.get("population_after_instruction") != len(alive):
                fail(eid, "executed_population_count_mismatch")
            check_energy(eid)
        elif kind == "FAULT":
            fault_count += 1
            actor = alive.get(event.get("organism_id"))
            if actor is None or event.get("pc") != actor.pc:
                fail(eid, "fault_not_at_live_entity_program_counter")
        elif kind == "DEATH":
            death_count += 1
            actor = alive.get(event.get("organism_id"))
            if actor is None:
                fail(eid, "death_of_unknown_or_already_dead_entity")
                continue
            if event.get("abandoned_nursery") != len(actor.nursery):
                fail(eid, "death_nursery_count_mismatch")
            if event.get("energy_released") != actor.energy:
                fail(eid, "death_resource_reclaim_mismatch")
            for unit in actor.units + [n["unit"] for n in actor.nursery]:
                if occupied.get(unit, (None, None))[0] != actor.entity_id:
                    fail(eid, "death_releasing_another_entity_material", unit=unit)
                occupied.pop(unit, None)
            resource_state["heat"] += actor.energy
            actor.death_tick = tick
            alive.pop(actor.entity_id)
            entities_released += 1
            check_energy(eid)
        else:
            fail(eid, "unexpected_event_type", kind=kind)

    if pending:
        fail(pending["event_id"], "unterminated_instruction_receipt")
    if genesis is None:
        fail(None, "missing_genesis")
    raw_birth_receipts = {b.get("event_id"): b for b in births}
    if len(raw_birth_receipts) != len(births):
        fail(None, "duplicate_birth_certificate_id")
    if set(raw_birth_receipts) != set(seen_birth_events):
        fail(None, "birth_stream_and_certificate_ids_mismatch")
    for eid, event in seen_birth_events.items():
        expected = {k: v for k, v in event.items() if k not in ("kind", "tick", "seed", "variant")}
        supplied = {k: v for k, v in raw_birth_receipts.get(eid, {}).items()
                    if k not in ("seed", "variant")}
        if expected != supplied:
            fail(eid, "birth_certificate_does_not_match_event")
    if world.get("birth_count") != len(seen_birth_events):
        fail(None, "world_birth_count_mismatch")
    if world.get("copy_events") != copy_count:
        fail(None, "world_copy_event_count_mismatch")
    if world.get("death_count") != death_count:
        fail(None, "world_death_count_mismatch")
    if world.get("world_extinct") != (not alive) or world.get("live_count") != len(alive):
        fail(None, "world_extinction_or_live_count_mismatch")
    if world.get("remaining_material") != total_material - len(occupied):
        fail(None, "world_remaining_material_mismatch")
    if world.get("heat") != resource_state["heat"]:
        fail(None, "world_heat_mismatch")
    if (world.get("remaining_food_a") != resource_state["a"] or
        world.get("remaining_food_b") != resource_state["b"]):
        fail(None, "world_food_totals_mismatch")
    if world.get("max_energy_residual") != 0 or world.get("max_material_residual") != 0:
        fail(None, "original_world_indicated_resource_failure")

    offspring_ids = {i for i in all_entities if i != 0}
    fertile_offspring = offspring_ids & set(parent_children)
    branching_parents = [i for i, ch in parent_children.items() if len(ch) >= 2]
    branching_fertile_siblings = [
        i for i, children in parent_children.items()
        if len([c for c in children if c in fertile_offspring]) >= 2
    ]
    mutant_children = [
        node for i, node in all_entities.items()
        if i and node.parent_id in all_entities and
        node.ops != all_entities[node.parent_id].ops
    ]
    faithful_mutant_grandchildren = [
        node for i, node in all_entities.items()
        if i and node.parent_id in all_entities
        and all_entities[node.parent_id].parent_id is not None
        and all_entities[node.parent_id].ops !=
            all_entities[all_entities[node.parent_id].parent_id].ops
        and node.ops == all_entities[node.parent_id].ops
    ]
    return {
        "seed": world.get("seed"), "variant": world.get("variant"),
        "valid": not errors, "errors": errors,
        "event_count": len(events), "birth_count": len(seen_birth_events),
        "copy_events": copy_count, "death_count": death_count, "fault_count": fault_count,
        "finitely_reused_material_units": reuse_count,
        "max_generation": max((e.generation for e in all_entities.values()), default=0),
        "fertile_offspring": len(fertile_offspring),
        "branching_parents": len(branching_parents),
        "parents_with_two_fertile_children": len(branching_fertile_siblings),
        "mutated_child_tapes": len(mutant_children),
        "grandchildren_retain_mutated_parent_tape": len(faithful_mutant_grandchildren),
        "final_live_entities": len(alive),
        "independent_energy_residual_max": maximum_energy_residual,
        "interpretation": "authored, executed heredity with shared ecology; not evidence of spatial independent offspring or life",
    }


def load_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def analyze_dataset(inputs: Path, output: Path, *,
                    require_original_hashes: bool = True) -> dict:
    hashes = {name: hashlib.sha256((inputs / name).read_bytes()).hexdigest()
              for name in ORIGINAL_SHA256}
    if require_original_hashes and hashes != ORIGINAL_SHA256:
        raise ValueError(f"AL02 raw archive identity mismatch: {hashes}")
    worlds, birth_rows, event_rows = (
        load_rows(inputs / name)
        for name in ("worlds.jsonl", "births.jsonl", "events.jsonl")
    )
    groups_events: dict[tuple[int, str], list[dict]] = defaultdict(list)
    groups_births: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for row in event_rows:
        groups_events[(row["seed"], row["variant"])].append(row)
    for row in birth_rows:
        groups_births[(row["seed"], row["variant"])].append(row)
    world_map = {(row["seed"], row["variant"]): row for row in worlds}
    if len(world_map) != len(worlds):
        raise ValueError("Duplicate world metadata")
    if (set(world_map) != set(groups_events)
        or not set(groups_births).issubset(set(world_map))):
        raise ValueError("Worlds, event streams, and certificates reference different keys")
    if require_original_hashes:
        expected = {(seed, v) for seed in range(5000, 5064) for v in VARIANTS}
        if set(world_map) != expected:
            raise ValueError("Original AL02 256-world sample not preserved")
    audited = [audit_world(groups_events[key], groups_births.get(key, []), world_map[key])
               for key in sorted(world_map)]
    problem_worlds = [row for row in audited if not row["valid"]]
    by_variant = {}
    for variant in VARIANTS:
        subset = [row for row in audited if row["variant"] == variant]
        by_variant[variant] = {
            "worlds": len(subset),
            "births": sum(row["birth_count"] for row in subset),
            "max_generation": max((row["max_generation"] for row in subset), default=0),
            "fertile_offspring": sum(row["fertile_offspring"] for row in subset),
            "branching_parents": sum(row["branching_parents"] for row in subset),
            "parents_with_two_fertile_children": sum(
                row["parents_with_two_fertile_children"] for row in subset),
            "mutated_child_tapes": sum(row["mutated_child_tapes"] for row in subset),
            "grandchildren_retain_mutated_parent_tape": sum(
                row["grandchildren_retain_mutated_parent_tape"] for row in subset),
            "post_death_material_reallocations": sum(
                row["finitely_reused_material_units"] for row in subset),
            "invalid_worlds": sum(not row["valid"] for row in subset),
        }
    result = {
        "experiment": "AL07-TRACE", "status": "read_only_causal_provenance_audit",
        "source_data_sha256": hashes,
        "worlds": len(worlds), "births": len(birth_rows), "events": len(event_rows),
        "verified_birth_certificates": sum(x["birth_count"] for x in audited if x["valid"]),
        "invalid_worlds": len(problem_worlds),
        "invalid_diagnostics": [dict(seed=x["seed"], variant=x["variant"], errors=x["errors"])
                                for x in problem_worlds],
        "variants": by_variant,
        "claims_not_tested": [
            "No emergent organism boundary or endogenous repair",
            "No genome encoding beyond designed bytecode alphabet",
            "Sibling reproductive ancestry != counterfactual sibling independence",
            "No newly invented ecological capability, sentience, or open-ended evolution",
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    raw = "".join(normalized(row) + "\n" for row in audited)
    (output / "genealogy-worlds.jsonl").write_text(raw, encoding="utf-8")
    result["genealogy_worlds_sha256"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    (output / "genealogy-summary.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("runs/al02-copy"))
    parser.add_argument("--output-dir", type=Path, default=Path("runs/al07-trace"))
    parser.add_argument("--allow-dev-fixture", action="store_true",
                        help="Only for generated development fixtures, skip original archive hash check")
    args = parser.parse_args()
    result = analyze_dataset(args.input_dir, args.output_dir,
                             require_original_hashes=not args.allow_dev_fixture)
    print(json.dumps({
        "worlds": result["worlds"], "births": result["births"],
        "verified_births": result["verified_birth_certificates"],
        "invalid_worlds": result["invalid_worlds"],
        "variants": result["variants"],
        "meaning": "only causal write/material genealogy in an authored virtual machine",
    }, sort_keys=True))
    return 0 if result["invalid_worlds"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
