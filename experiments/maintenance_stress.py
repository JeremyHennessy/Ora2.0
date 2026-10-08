"""AL03-MAINT: separate maintenance-cost falsifier for a saturated synthetic ecology.

Extends the existing AL03 finite, non-physical resource rules without editing
any previously verified AL03 code, source protocols, or research artifacts.
See docs/AL03-MAINT-PROTOCOL.md. This is NOT a self-maintaining living organism.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import random

from experiments.niche_selection import Ecology, Protocol, C, P, canonical

ARMS = ("baseline", "upkeep_8", "upkeep_4", "upkeep_1", "upkeep_8_no_inflow")
MAINT_INTERVAL = {
    "baseline": None,
    "upkeep_8": 8,
    "upkeep_4": 4,
    "upkeep_1": 1,
    "upkeep_8_no_inflow": 8,
}


class MaintenanceEcology(Ecology):
    """Original physics plus a predeclared energy debit on whole-world time."""

    def __init__(self, seed: int, arm: str, p: Protocol = Protocol()) -> None:
        if arm not in ARMS:
            raise ValueError(f"Unknown AL03-MAINT intervention: {arm}")
        self.arm = arm
        self.interval = MAINT_INTERVAL[arm]
        self.upkeep_paid = 0
        self.upkeep_deaths = 0
        self.upkeep_occurrences = 0
        # Use one and only one change of original AL03 source treatment as named.
        base_variant = "no_inflow" if arm == "upkeep_8_no_inflow" else "heritable"
        super().__init__(seed, base_variant, p)

    def step(self) -> None:
        if not self.alive:
            return
        super().step()
        if not self.interval or self.tick % self.interval != 0:
            return
        self.upkeep_occurrences += 1
        # An entity gets one cost per whole-world calendar interval, even if idle.
        for entity_id in sorted(tuple(self.alive)):
            entity = self.alive.get(entity_id)
            if entity is None:
                continue
            if entity.energy <= 0:
                raise AssertionError("Unresolved zero-energy entity before upkeep")
            before = entity.energy
            entity.energy -= 1
            self.heat += 1
            self.upkeep_paid += 1
            self.emit(
                "UPKEEP",
                organism=entity_id, material_slot=entity.slot,
                energy_before=before, paid_energy=1, energy_after=entity.energy,
                maintenance_interval=self.interval,
            )
            if entity.energy == 0:
                self.upkeep_deaths += 1
                self.die(entity)
        mass, energy = self.assert_conservation()
        # The parent engine records the pre-upkeep step; replace diagnostic
        # fields with the authoritative post-upkeep state, not a second tick.
        if len(self.traces) != self.tick:
            raise AssertionError("Missing or duplicated AL03 step trace")
        trace = self.traces[-1]
        trace.update(
            population=len(self.alive),
            producers=sum(x.role == P for x in self.alive.values()),
            consumers=sum(x.role == C for x in self.alive.values()),
            a=self.a, b=self.b, w=self.w,
            supplied_a=self.supplied_a,
            heat=self.heat, births=len(self.births), deaths=self.deaths,
            mass_residual=mass, energy_residual=energy,
        )
        if any(trace[k] != getattr(self, k) for k in ("a", "b", "w", "heat", "supplied_a")):
            raise AssertionError("Post-upkeep trace disagrees with world state")

    def run_maintenance(self) -> tuple[dict, list[dict], list[dict]]:
        result, events, traces = self.run()
        if len(traces) != self.tick:
            raise AssertionError("Incomplete tick history")
        cap_count = sum(t["population"] == self.p.material_slots for t in traces)
        first_cap = next(
            (t["tick"] for t in traces if t["population"] == self.p.material_slots),
            None,
        )
        actual_upkeep = sum(e["paid_energy"] for e in events if e["kind"] == "UPKEEP")
        if actual_upkeep != self.upkeep_paid:
            raise AssertionError("Upkeep debit differs from recorded energy transfers")
        if sum(e["kind"] == "DEATH" for e in events) != self.deaths:
            raise AssertionError("Death receipts lost")
        if any(t["mass_residual"] or t["energy_residual"] for t in traces):
            raise AssertionError("Previously recorded conservation residual was nonzero")
        if result["max_energy_residual"] or result["max_mass_residual"]:
            raise AssertionError("World resource residual nonzero")
        result.update({
            "arm": self.arm,
            "maintenance_interval": self.interval,
            "maintenance_occurrences": self.upkeep_occurrences,
            "paid_upkeep_units": self.upkeep_paid,
            "upkeep_caused_deaths": self.upkeep_deaths,
            "population_at_cap_steps": cap_count,
            "share_of_observed_steps_at_cap": cap_count / len(traces) if traces else 0.0,
            "share_of_full_480_tick_horizon_at_cap": cap_count / self.p.world_horizon,
            "first_saturation_tick": first_cap,
            "survived_to_horizon": self.tick == self.p.world_horizon and bool(self.alive),
            "assumption": "Upkeep is an authored world law, NOT intrinsic organism metabolism",
        })
        return result, events, traces


def paired_bootstrap(diffs: list[int], *, resamples: int = 4000,
                     seed: int = 20261008) -> list[float]:
    if not diffs or resamples < 1:
        raise ValueError("Requires paired worlds and positive resample count")
    rng = random.Random(seed)
    n = len(diffs)
    values = sorted(
        sum(diffs[rng.randrange(n)] for _ in range(n)) / n
        for _ in range(resamples)
    )
    return [values[int(.025 * (resamples - 1))],
            values[int(.975 * (resamples - 1))]]


def summarize(worlds: list[dict], seeds: list[int], p: Protocol) -> dict:
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("Duplicate or empty world seeds")
    mapped = {(w["seed"], w["arm"]): w for w in worlds}
    keys = {(seed, arm) for seed in seeds for arm in ARMS}
    if len(mapped) != len(worlds) or set(mapped) != keys:
        raise AssertionError("Missing, extra or duplicate world treatment")
    if any(w["max_mass_residual"] or w["max_energy_residual"] for w in worlds):
        raise AssertionError("Resource conservation breach")
    by_arm = {}
    for arm in ARMS:
        subset = [mapped[(seed, arm)] for seed in seeds]
        finals = sorted(w["live_at_end"] for w in subset)
        atcap = sum(w["live_at_end"] == p.material_slots for w in subset)
        observed_steps = sum(w["steps"] for w in subset)
        cap_steps = sum(w["population_at_cap_steps"] for w in subset)
        by_arm[arm] = {
            "worlds": len(subset),
            "survived_to_horizon": sum(w["survived_to_horizon"] for w in subset),
            "extinct_before_horizon": sum(w["extinct"] for w in subset),
            "final_at_population_cap": atcap,
            "mean_final_population": sum(finals) / len(finals),
            "median_final_population": (
                (finals[(len(finals) - 1)//2] + finals[len(finals)//2]) / 2
            ),
            "cap_steps_over_observed_steps": cap_steps / observed_steps,
            "cap_steps_over_full_horizon": cap_steps / (len(subset) * p.world_horizon),
            "worlds_ever_at_cap": sum(w["first_saturation_tick"] is not None
                                     for w in subset),
            "total_births": sum(w["births"] for w in subset),
            "total_deaths": sum(w["deaths"] for w in subset),
            "maintenance_energy_paid": sum(w["paid_upkeep_units"] for w in subset),
            "maintenance_deaths": sum(w["upkeep_caused_deaths"] for w in subset),
            "total_supplied_a": sum(w["supplied_a"] for w in subset),
            "consumer_lineage_worlds": sum(
                w["established_downstream_lineage"] for w in subset
            ),
            "maximum_mass_residual": max(w["max_mass_residual"] for w in subset),
            "maximum_energy_residual": max(w["max_energy_residual"] for w in subset),
        }
    comparison = {}
    for arm in ARMS:
        if arm == "baseline":
            continue
        differences = [
            int(mapped[seed, "baseline"]["survived_to_horizon"]) -
            int(mapped[seed, arm]["survived_to_horizon"])
            for seed in seeds
        ]
        comparison[arm] = {
            "baseline_minus_arm": sum(differences) / len(differences),
            "paired_bootstrap_95_descriptive": paired_bootstrap(differences),
            "baseline_only": sum(x == 1 for x in differences),
            "arm_only": sum(x == -1 for x in differences),
            "same": sum(x == 0 for x in differences),
        }
    return {
        "experiment": "AL03-MAINT",
        "status": "maintenance_cost_sensitivity_in_toy_ecology_not_digital_life",
        "seed_list": seeds,
        "arm_order": list(ARMS),
        "total_worlds": len(worlds),
        "conditions": by_arm,
        "paired_persistence_differences": comparison,
        "limitations": [
            "Maintenance is externally authored and cannot establish metabolic autonomy",
            "World time and population cap are still assigned by the host simulator",
            "Energy scarcity and upkeep accounting predict some outcomes by construction",
            "The same genotype and environment rule set was not evolved independently",
            "Worlds are not born from primordial random organization",
        ],
    }


def execute_study(output: Path, seeds: list[int], revision: str = "unspecified",
                  p: Protocol = Protocol()) -> dict:
    if not seeds or len(set(seeds)) != len(seeds) or min(seeds) < 0:
        raise ValueError("World seeds must be unique, nonempty and nonnegative")
    output.mkdir(parents=True, exist_ok=True)
    files = ("worlds.jsonl", "events.jsonl", "traces.jsonl")
    hashes = {name: hashlib.sha256() for name in files}
    worlds: list[dict] = []
    with (output / "worlds.jsonl").open("w", encoding="utf-8") as wf, (
         output / "events.jsonl").open("w", encoding="utf-8") as ef, (
         output / "traces.jsonl").open("w", encoding="utf-8") as tf:
        for seed in seeds:
            for arm in ARMS:
                w = MaintenanceEcology(seed, arm, p)
                result, events, traces = w.run_maintenance()
                worlds.append(result)
                for file, handle, rows in (
                    ("worlds.jsonl", wf, [result]),
                    ("events.jsonl", ef, events),
                    ("traces.jsonl", tf, traces),
                ):
                    for row in rows:
                        line = canonical({"arm": arm, **row}) + "\n"
                        handle.write(line)
                        hashes[file].update(line.encode("utf-8"))
    out = summarize(worlds, seeds, p)
    out.update({
        "protocol": "docs/AL03-MAINT-PROTOCOL.md",
        "source_revision": revision,
        "python_version": platform.python_version(),
        "simulation_parameters": asdict(p),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "worlds_sha256": hashes["worlds.jsonl"].hexdigest(),
        "events_sha256": hashes["events.jsonl"].hexdigest(),
        "traces_sha256": hashes["traces.jsonl"].hexdigest(),
        "world_rows": len(worlds),
        "event_rows": None,
        "trace_rows": None,
    })
    # Count actual rows without requiring a large in-memory list.
    for file, key in (("events.jsonl", "event_rows"), ("traces.jsonl", "trace_rows")):
        with (output / file).open(encoding="utf-8") as handle:
            out[key] = sum(1 for _ in handle)
    (output / "summary.json").write_text(
        json.dumps(out, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", default="8500:8548")
    parser.add_argument("--output-dir", type=Path, default=Path("runs/al03-maint"))
    parser.add_argument("--source-revision", default="unspecified")
    args = parser.parse_args(argv)
    try:
        a, b = (int(x) for x in args.seeds.split(":", 1))
        if a < 0 or b <= a:
            raise ValueError()
    except ValueError:
        parser.error("--seeds requires nonnegative half-open start:end")
    result = execute_study(args.output_dir, list(range(a, b)),
                           revision=args.source_revision)
    print(json.dumps({
        "total_worlds": result["total_worlds"],
        "conditions": result["conditions"],
        "paired_persistence_differences": result["paired_persistence_differences"],
        "mass_trace_residuals": [
            result["conditions"][arm]["maximum_mass_residual"] for arm in ARMS
        ],
        "energy_trace_residuals": [
            result["conditions"][arm]["maximum_energy_residual"] for arm in ARMS
        ],
        "interpretation": "research stress test of a designed ecology; NOT life",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
