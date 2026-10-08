"""AL03-NICHE — finite, mass/energy-conserving byproduct ecology.

A new synthetic experiment about resource specialization. Reproduction is
explicitly engine-mediated; this is NOT AL02's executed-copy heredity and
NOT an autonomous living organism. See frozen AL03-NICHE-PROTOCOL.md.
"""
from __future__ import annotations
from collections import defaultdict
from dataclasses import asdict, dataclass
import argparse
import hashlib
import json
from pathlib import Path
import platform
import random

VARIANTS = (
    "heritable", "byproduct_sink", "nonheritable_role",
    "mutation_disabled", "no_inflow",
)
P, C = "P", "C"


def canonical(x: object) -> str:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class Protocol:
    world_horizon: int = 480
    initial_a: int = 18
    initial_energy: int = 8
    material_slots: int = 40
    supplied_a_every: int = 3
    a_potential: int = 20
    b_potential: int = 8
    producer_energy: int = 12
    consumer_energy: int = 8
    action_heat: int = 1
    divide_threshold: int = 26
    daughter_energy: int = 8
    divide_heat: int = 2
    mutation_probability: float = 0.08

    def __post_init__(self):
        if self.world_horizon < 1 or self.initial_a < 0 or self.initial_energy < 0:
            raise ValueError("Invalid experiment time or resources")
        if self.material_slots < 1 or self.supplied_a_every < 1:
            raise ValueError("Invalid material / environmental cycle")
        if (self.a_potential != self.producer_energy + self.b_potential
            or self.b_potential != self.consumer_energy):
            raise ValueError("Reaction potential not conserved by feeding")
        if min(self.action_heat, self.divide_heat, self.daughter_energy,
               self.divide_threshold) < 0:
            raise ValueError("Negative energy / division requirement")
        if self.divide_threshold < self.daughter_energy + self.divide_heat:
            raise ValueError("Division cannot pay its own energy cost")
        if not 0 <= self.mutation_probability <= 1:
            raise ValueError("Mutation probability outside [0,1]")


@dataclass
class Entity:
    id: int
    role: str
    energy: int
    slot: int
    parent: int | None
    generation: int
    born_tick: int
    lineage_role_switch: bool = False
    fed_b: int = 0
    fed_a: int = 0
    died_tick: int | None = None


def establish_downstream_lineage(births: list[dict], entities: dict[int, Entity]) -> bool:
    """True only for verified B-fed C parent -> B-fed C child with P->C ancestry."""
    for b in births:
        if (b["parent_role"] == C and b["child_role"] == C
            and b["parent_fed_b_before_birth"] is True
            and b["child_lineage_has_p_to_c_switch"] is True
            and b["child_id"] in entities and entities[b["child_id"]].fed_b > 0):
            return True
    return False


class Ecology:
    def __init__(self, seed: int, variant: str, p: Protocol = Protocol()):
        if not isinstance(seed, int) or seed < 0 or variant not in VARIANTS:
            raise ValueError("Invalid seed or variant")
        self.seed, self.variant, self.p = seed, variant, p
        self.rng = random.Random(seed)
        self.tick = 0
        self.last_actor = -1
        self.a, self.b, self.w = p.initial_a, 0, 0
        self.supplied_a = 0
        self.heat = 0
        self.initial_energy = p.initial_a * p.a_potential + p.initial_energy
        self.free_slots: set[int] = set(range(1, p.material_slots))
        self.occupied_slots: dict[int, int] = {0: 0}
        self.ever_used_slots = {0}
        self.slot_reuse = 0
        founder = Entity(0, P, p.initial_energy, 0, None, 0, 0)
        self.alive = {0: founder}
        self.entities = {0: founder}
        self.next_id = 1
        self.events: list[dict] = []
        self.traces: list[dict] = []
        self.births: list[dict] = []
        self.deaths = 0
        self.max_population = 1
        self.role_switches = 0
        self.b_generations = 0
        self.generated_b = 0
        self.consumed_b = 0
        self.max_mass_residual = 0
        self.max_energy_residual = 0
        self.emit("GENESIS", founder_id=0, food_a=self.a,
                  food_b=self.b, founder_energy=founder.energy, body_slot=0)
        self.assert_conservation()

    def emit(self, kind: str, **items: object):
        e = dict(event_id=len(self.events), seed=self.seed, variant=self.variant,
                 tick=self.tick, kind=kind, **items)
        self.events.append(e)
        return e["event_id"]

    def assert_conservation(self) -> tuple[int, int]:
        bodies = [x.slot for x in self.alive.values()]
        all_slots = bodies + list(self.free_slots)
        if (len(all_slots) != self.p.material_slots
            or len(set(all_slots)) != self.p.material_slots
            or set(all_slots) != set(range(self.p.material_slots))
            or {slot: e.id for slot, e in
                ((entity.slot, entity) for entity in self.alive.values())
               } != self.occupied_slots):
            raise AssertionError("Duplicate/lost living material slots")
        if any(entity.energy < 0 for entity in self.alive.values()):
            raise AssertionError("Entity has negative energy")
        if min(self.a, self.b, self.w, self.heat, self.supplied_a) < 0:
            raise AssertionError("Negative material or environmental energy")
        mass_delta = self.a + self.b + self.w - self.p.initial_a - self.supplied_a
        effective_energy = (
            self.a * self.p.a_potential + self.b * self.p.b_potential
            + sum(entity.energy for entity in self.alive.values()) + self.heat
        )
        energy_delta = effective_energy - (
            self.initial_energy + self.supplied_a * self.p.a_potential
        )
        self.max_mass_residual = max(self.max_mass_residual, abs(mass_delta))
        self.max_energy_residual = max(self.max_energy_residual, abs(energy_delta))
        if mass_delta or energy_delta:
            raise AssertionError(f"Resource accounting error: mass {mass_delta}, energy {energy_delta}")
        return mass_delta, energy_delta

    def choose_actor(self) -> Entity | None:
        if not self.alive:
            return None
        ids = sorted(self.alive)
        chosen = next((i for i in ids if i > self.last_actor), ids[0])
        self.last_actor = chosen
        return self.alive[chosen]

    def die(self, entity: Entity):
        if entity.id not in self.alive:
            raise AssertionError("Double death")
        self.heat += entity.energy
        self.free_slots.add(entity.slot)
        self.occupied_slots.pop(entity.slot)
        entity.died_tick = self.tick
        self.alive.pop(entity.id)
        self.deaths += 1
        self.emit("DEATH", organism=entity.id, role=entity.role,
                  parent_id=entity.parent, material_slot=entity.slot,
                  terminal_energy=entity.energy)
        entity.energy = 0

    def draw_child_role(self, parent: Entity) -> str:
        if self.variant == "mutation_disabled":
            return parent.role
        if self.variant == "nonheritable_role":
            return C if self.rng.random() < self.p.mutation_probability else P
        if self.rng.random() < self.p.mutation_probability:
            return C if parent.role == P else P
        return parent.role

    def reproduce(self, parent: Entity) -> None:
        if (parent.energy < self.p.divide_threshold
            or not self.free_slots or len(self.alive) >= self.p.material_slots):
            return
        parent.energy -= self.p.daughter_energy + self.p.divide_heat
        self.heat += self.p.divide_heat
        cid = self.next_id
        self.next_id += 1
        slot = min(self.free_slots)
        self.free_slots.remove(slot)
        if slot in self.ever_used_slots:
            self.slot_reuse += 1
        self.ever_used_slots.add(slot)
        role = self.draw_child_role(parent)
        role_changed = role != parent.role
        self.role_switches += int(role_changed)
        switched = parent.lineage_role_switch or (parent.role == P and role == C)
        child = Entity(cid, role, self.p.daughter_energy, slot, parent.id,
                       parent.generation + 1, self.tick,
                       lineage_role_switch=switched)
        self.alive[cid] = child
        self.entities[cid] = child
        self.occupied_slots[slot] = cid
        birth = {
            "parent_id": parent.id, "child_id": cid,
            "parent_role": parent.role, "child_role": role,
            "parent_generation": parent.generation,
            "child_generation": child.generation,
            "parent_fed_b_before_birth": bool(parent.fed_b),
            "child_lineage_has_p_to_c_switch": switched,
            "child_material_slot": slot, "transferred_energy": self.p.daughter_energy,
            "mutation_or_role_change": role_changed,
        }
        self.births.append(birth)
        self.emit("BIRTH", **birth)

    def step(self) -> None:
        actor = self.choose_actor()
        if actor is None:
            return
        self.tick += 1
        if self.variant != "no_inflow" and self.tick % self.p.supplied_a_every == 0:
            self.a += 1
            self.supplied_a += 1
            self.emit("ENVIRONMENT_SUPPLY", resource="A", amount=1)
        if actor.energy <= 0:
            self.die(actor)
            self.assert_conservation()
            return
        actor.energy -= self.p.action_heat
        self.heat += self.p.action_heat
        outcome = "resource_unavailable"
        if actor.role == P and self.a > 0:
            self.a -= 1
            actor.energy += self.p.producer_energy
            actor.fed_a += 1
            if self.variant == "byproduct_sink":
                self.w += 1
                self.heat += self.p.b_potential
                outcome = "producer_to_waste"
            else:
                self.b += 1
                self.generated_b += 1
                outcome = "producer_to_byproduct"
        elif actor.role == C and self.b > 0:
            self.b -= 1
            self.w += 1
            actor.energy += self.p.consumer_energy
            actor.fed_b += 1
            self.consumed_b += 1
            outcome = "consumer_uses_byproduct"
        self.emit("ACT", organism=actor.id, role=actor.role, outcome=outcome,
                  energy_after_act=actor.energy, resource_a=self.a, resource_b=self.b)
        self.reproduce(actor)
        if actor.energy <= 0 and actor.id in self.alive:
            self.die(actor)
        self.max_population = max(self.max_population, len(self.alive))
        mass, energy = self.assert_conservation()
        self.traces.append({
            "seed": self.seed, "variant": self.variant, "tick": self.tick,
            "population": len(self.alive),
            "producers": sum(x.role == P for x in self.alive.values()),
            "consumers": sum(x.role == C for x in self.alive.values()),
            "a": self.a, "b": self.b, "w": self.w,
            "supplied_a": self.supplied_a, "heat": self.heat,
            "births": len(self.births), "deaths": self.deaths,
            "mass_residual": mass, "energy_residual": energy,
        })

    def run(self) -> tuple[dict, list[dict], list[dict]]:
        while self.tick < self.p.world_horizon and self.alive:
            self.step()
        established = establish_downstream_lineage(self.births, self.entities)
        summary = {
            "seed": self.seed, "variant": self.variant,
            "steps": self.tick, "extinct": not bool(self.alive),
            "live_at_end": len(self.alive), "max_population": self.max_population,
            "births": len(self.births), "deaths": self.deaths,
            "role_switches": self.role_switches,
            "generated_b": self.generated_b, "consumed_b": self.consumed_b,
            "consumer_births": sum(b["child_role"] == C for b in self.births),
            "b_fed_consumers": sum(e.role == C and e.fed_b > 0 for e in self.entities.values()),
            "max_generation": max(e.generation for e in self.entities.values()),
            "established_downstream_lineage": established,
            "potential_role_specialization_only": True,
            "material_slot_reallocations": self.slot_reuse,
            "supplied_a": self.supplied_a,
            "a_remaining": self.a, "b_remaining": self.b, "w_remaining": self.w,
            "heat": self.heat,
            "max_mass_residual": self.max_mass_residual,
            "max_energy_residual": self.max_energy_residual,
            "initial_potential": self.initial_energy,
        }
        return summary, list(self.events), list(self.traces)


def paired_interval(diffs: list[int], resamples=4000, seed=20261008) -> list[float]:
    if not diffs:
        raise ValueError("No paired worlds")
    rng = random.Random(seed)
    n = len(diffs)
    vals = sorted(sum(diffs[rng.randrange(n)] for _ in range(n)) / n
                  for _ in range(resamples))
    return [vals[int(.025 * (len(vals)-1))], vals[int(.975 * (len(vals)-1))]]


def analyze(worlds: list[dict], seed_list: list[int]) -> dict:
    if not seed_list or len(set(seed_list)) != len(seed_list):
        raise ValueError("Duplicate or missing sampled world seeds")
    mapped = {(w["seed"], w["variant"]): w for w in worlds}
    expected = {(s, v) for s in seed_list for v in VARIANTS}
    if len(mapped) != len(worlds) or set(mapped) != expected:
        raise AssertionError("Missing/duplicate treatment world")
    if any(w["max_mass_residual"] or w["max_energy_residual"] for w in worlds):
        raise AssertionError("Non-conserved experiment record")
    variants = {}
    for v in VARIANTS:
        group = [mapped[s, v] for s in seed_list]
        variants[v] = {
            "worlds": len(group),
            "successful_lineage_worlds": sum(w["established_downstream_lineage"] for w in group),
            "total_births": sum(w["births"] for w in group),
            "b_fed_consumers": sum(w["b_fed_consumers"] for w in group),
            "b_molecules_generated": sum(w["generated_b"] for w in group),
            "b_molecules_consumed": sum(w["consumed_b"] for w in group),
            "world_extinctions": sum(w["extinct"] for w in group),
            "maximum_generation": max(w["max_generation"] for w in group),
            "maximum_energy_residual": max(w["max_energy_residual"] for w in group),
            "maximum_mass_residual": max(w["max_mass_residual"] for w in group),
        }
    diffs = {}
    for control in ("byproduct_sink", "nonheritable_role"):
        differences = [
            int(mapped[s, "heritable"]["established_downstream_lineage"]) -
            int(mapped[s, control]["established_downstream_lineage"])
            for s in seed_list
        ]
        diffs[control] = {
            "heritable_minus_control": sum(differences) / len(differences),
            "descriptive_bootstrap_95": paired_interval(differences),
            "heritable_only": sum(d == 1 for d in differences),
            "control_only": sum(d == -1 for d in differences),
            "same": sum(d == 0 for d in differences),
        }
    return {
        "experiment": "AL03-NICHE",
        "status": "preregistered_ecological_role_selection_not_living_organisms",
        "sampled_seeds": seed_list,
        "treatment_worlds": len(worlds),
        "variants": variants,
        "paired_differences": diffs,
        "explicit_limit": (
            "P and C capabilities and engine-mediated copying are designer-authored. "
            "The result does not show spontaneous new skills, executed heredity or organismhood."
        ),
    }


def write_study(output: Path, seed_list: list[int], revision="unspecified",
                p: Protocol = Protocol()) -> dict:
    if not seed_list or len(set(seed_list)) != len(seed_list) or min(seed_list) < 0:
        raise ValueError("Invalid world seed set")
    output.mkdir(parents=True, exist_ok=True)
    hasher = {name: hashlib.sha256() for name in
              ("worlds.jsonl", "events.jsonl", "traces.jsonl")}
    worlds: list[dict] = []
    with (output / "worlds.jsonl").open("w", encoding="utf-8") as wf, (
         output / "events.jsonl").open("w", encoding="utf-8") as ef, (
         output / "traces.jsonl").open("w", encoding="utf-8") as tf:
        for seed in seed_list:
            for variant in VARIANTS:
                model = Ecology(seed, variant, p)
                result, events, traces = model.run()
                worlds.append(result)
                for name, handle, records in (
                    ("worlds.jsonl", wf, [result]),
                    ("events.jsonl", ef, events),
                    ("traces.jsonl", tf, traces),
                ):
                    for record in records:
                        text = canonical(record) + "\n"
                        handle.write(text)
                        hasher[name].update(text.encode("utf-8"))
    summary = analyze(worlds, seed_list)
    summary.update({
        "protocol": "docs/AL03-NICHE-PROTOCOL.md",
        "revision": revision, "python": platform.python_version(),
        "parameters": asdict(p),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "worlds_sha256": hasher["worlds.jsonl"].hexdigest(),
        "events_sha256": hasher["events.jsonl"].hexdigest(),
        "traces_sha256": hasher["traces.jsonl"].hexdigest(),
    })
    (output / "summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2)+"\n",encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", default="8000:8048")
    parser.add_argument("--output-dir", type=Path, default=Path("runs/al03-niche"))
    parser.add_argument("--source-revision", default="unspecified")
    args = parser.parse_args(argv)
    try:
        a, b = (int(s) for s in args.seeds.split(":", 1))
        if a < 0 or a >= b:
            raise ValueError()
    except ValueError:
        parser.error("--seeds must be nonnegative half-open start:end")
    out = write_study(args.output_dir, list(range(a, b)), revision=args.source_revision)
    print(json.dumps({
        "worlds": out["treatment_worlds"],
        "variants": out["variants"],
        "paired_differences": out["paired_differences"],
        "status": "resource-mediated role inheritance experiment only, not life",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
