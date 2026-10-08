"""CLOSURE-01-SPATIAL: explicit reaction-diffusion and shell screening.

This is a fixed toy chemistry with 5 material species and NO organism class.
All reactions/permeability laws are designer chosen; a positive does not imply
autopoiesis, a true biological membrane or life.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import platform
import random

SIDE = 9
CELLS = SIDE * SIDE
ORIGINS = ("clustered", "dispersed", "nutrient_only")
ARMS = (
    "intact", "no_R_to_A", "no_A_to_R",
    "no_M_synthesis", "permeability_null", "resource_denied",
)
NEIGH4 = tuple(
    tuple(
        ((i // SIDE + dr) % SIDE) * SIDE + ((i % SIDE + dc) % SIDE)
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
    )
    for i in range(CELLS)
)
NEIGH8 = tuple(
    tuple(
        ((i // SIDE + dr) % SIDE) * SIDE + ((i % SIDE + dc) % SIDE)
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if (dr, dc) != (0, 0)
    )
    for i in range(CELLS)
)


def compact(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Protocol:
    initial_s_per_site: int = 4
    clustered_a: int = 12
    clustered_r: int = 12
    added_s_per_step: int = 8
    basal_p: float = 0.006
    reaction_rate: float = 0.35
    attempts_per_site: int = 2
    decay_a: float = 0.09
    decay_r: float = 0.09
    decay_m: float = 0.08
    substrate_move_p: float = 0.50
    catalyst_move_p: float = 0.24
    shell_impedance: float = 0.80
    warmup_steps: int = 60
    followup_steps: int = 60
    core_damage: float = 0.55
    ring_damage: float = 0.65
    min_pre_a: int = 4
    min_pre_r: int = 4
    min_pre_ring: int = 2
    core_recovery_fraction: float = 0.70
    required_ring_after: int = 2
    required_local_m_synth: int = 2
    recovery_streak: int = 3

    def __post_init__(self) -> None:
        probabilities = (
            self.basal_p, self.decay_a, self.decay_r, self.decay_m,
            self.substrate_move_p, self.catalyst_move_p,
            self.core_damage, self.ring_damage, self.core_recovery_fraction,
        )
        if any(not 0 <= q <= 1 for q in probabilities):
            raise ValueError("Invalid probability or fraction")
        if self.reaction_rate < 0 or self.shell_impedance < 0:
            raise ValueError("Reaction weights / shell impedance must be nonnegative")
        if self.initial_s_per_site < 0 or min(
            self.clustered_a, self.clustered_r, self.added_s_per_step,
            self.attempts_per_site
        ) < 0:
            raise ValueError("Negative molecule/attempt budget")
        if self.clustered_a + self.clustered_r > CELLS * self.initial_s_per_site:
            raise ValueError("Cannot seed more catalysts than existing substrate")
        if min(
            self.warmup_steps, self.followup_steps, self.min_pre_a,
            self.min_pre_r, self.min_pre_ring, self.required_ring_after,
            self.required_local_m_synth, self.recovery_streak
        ) < 1:
            raise ValueError("Invalid strictly-positive time or recovery threshold")
        if self.min_pre_ring > 8 or self.required_ring_after > 8:
            raise ValueError("More than eight boundary pixels required")


@dataclass
class World:
    s: list[int]
    a: list[int]
    r: list[int]
    m: list[int]
    w: list[int]
    inflow: int = 0
    steps: int = 0
    basal_births: int = 0
    synth_a: int = 0
    synth_r: int = 0
    synth_m: int = 0
    decay_events: int = 0
    reaction_events: int = 0

    def duplicate(self) -> "World":
        return World(
            self.s.copy(), self.a.copy(), self.r.copy(),
            self.m.copy(), self.w.copy(),
            self.inflow, self.steps, self.basal_births,
            self.synth_a, self.synth_r, self.synth_m,
            self.decay_events, self.reaction_events,
        )

    def mass(self) -> int:
        return sum(map(sum, (self.s, self.a, self.r, self.m, self.w)))

    def counts(self) -> dict:
        return {key: sum(getattr(self, key)) for key in ("s", "a", "r", "m", "w")}


def checked(world: World, initial_mass: int) -> int:
    for species in (world.s, world.a, world.r, world.m, world.w):
        if len(species) != CELLS or any(not isinstance(v, int) or v < 0 for v in species):
            raise AssertionError("Invalid molecule lattice")
    residual = world.mass() - (initial_mass + world.inflow)
    if residual:
        raise AssertionError(f"Particle conservation broken: residual {residual}")
    return residual


def initialize(origin: str, rng: random.Random, p: Protocol) -> World:
    if origin not in ORIGINS:
        raise ValueError(f"Unknown initialization {origin}")
    s = [p.initial_s_per_site] * CELLS
    a, r, m, w = ([0] * CELLS for _ in range(4))
    if origin == "clustered":
        count = p.clustered_a + p.clustered_r
        for i in range(CELLS):
            taken = min(count, s[i])
            s[i] -= taken
            count -= taken
            if count == 0:
                break
        if count:
            raise AssertionError("Unable to fund clustered initialization")
        center = (SIDE // 2) * SIDE + SIDE // 2
        a[center], r[center] = p.clustered_a, p.clustered_r
    elif origin == "dispersed":
        for species, n in ((a, p.clustered_a), (r, p.clustered_r)):
            for _ in range(n):
                available_site = rng.randrange(CELLS)
                while not s[available_site]:
                    available_site = rng.randrange(CELLS)
                s[available_site] -= 1
                species[available_site] += 1
    world = World(s, a, r, m, w)
    checked(world, p.initial_s_per_site * CELLS)
    return world


def catalyst_hop_probability(
    source_m: int, target_m: int, p: Protocol,
    *, shell_has_effect: bool,
) -> float:
    if not shell_has_effect:
        return p.catalyst_move_p
    return p.catalyst_move_p / (
        1.0 + p.shell_impedance * (source_m + target_m)
    )


def step(
    world: World, rng: random.Random, p: Protocol,
    arm: str = "intact", *, target: int | None = None,
) -> int:
    """Single bounded update with no privileged organism state or healing API.

    Returns M production count in selected pre-damage 3x3 region, used only as
    independent post-hoc measurement. No new molecule appears without S.
    """
    if arm not in ARMS:
        raise ValueError(f"Unknown intervention {arm}")
    start_mass = p.initial_s_per_site * CELLS
    local_m_synth = 0
    if arm != "resource_denied":
        for _ in range(p.added_s_per_step):
            world.s[rng.randrange(CELLS)] += 1
        world.inflow += p.added_s_per_step

    for pos in range(CELLS):
        if world.s[pos] and rng.random() < p.basal_p:
            world.s[pos] -= 1
            world.a[pos] += 1
            world.basal_births += 1

    for pos in range(CELLS):
        for _ in range(p.attempts_per_site):
            if world.s[pos] == 0:
                continue
            aw, rw = p.reaction_rate * world.a[pos], p.reaction_rate * world.r[pos]
            weights = (
                aw if arm != "no_A_to_R" else 0.0,
                rw if arm != "no_R_to_A" else 0.0,
                aw if arm != "no_M_synthesis" else 0.0,
                rw if arm != "no_M_synthesis" else 0.0,
            )
            threshold = rng.random() * (1.0 + sum(weights)) - 1.0
            if threshold < 0:
                continue
            chosen = None
            for idx, weight in enumerate(weights):
                threshold -= weight
                if threshold < 0:
                    chosen = idx
                    break
            if chosen is None:
                raise AssertionError("Invalid reaction weight selection")
            world.s[pos] -= 1
            world.reaction_events += 1
            if chosen == 0:
                world.r[pos] += 1
                world.synth_r += 1
            elif chosen == 1:
                world.a[pos] += 1
                world.synth_a += 1
            else:
                dest = NEIGH4[pos][rng.randrange(4)]
                world.m[dest] += 1
                world.synth_m += 1
                if target is not None and (dest == target or dest in NEIGH8[target]):
                    local_m_synth += 1

    for molecules, prob in (
        (world.a, p.decay_a), (world.r, p.decay_r), (world.m, p.decay_m)
    ):
        for pos in range(CELLS):
            deaths = sum(rng.random() < prob for _ in range(molecules[pos]))
            molecules[pos] -= deaths
            world.w[pos] += deaths
            world.decay_events += deaths

    # Synchronous transport: moved molecules cannot move again in same step.
    for molecules, kind in ((world.s, "s"), (world.a, "a"), (world.r, "r")):
        previous = molecules.copy()
        updated = [0] * CELLS
        for pos, n in enumerate(previous):
            for _ in range(n):
                dest = NEIGH4[pos][rng.randrange(4)]
                probability = (
                    p.substrate_move_p if kind == "s"
                    else catalyst_hop_probability(
                        world.m[pos], world.m[dest], p,
                        shell_has_effect=arm != "permeability_null"
                    )
                )
                if rng.random() < probability:
                    updated[dest] += 1
                else:
                    updated[pos] += 1
        molecules[:] = updated

    world.steps += 1
    checked(world, start_mass)
    return local_m_synth


def region(world: World, target: int) -> dict:
    core = (target,) + NEIGH8[target]
    return {
        "core_a": sum(world.a[i] for i in core),
        "core_r": sum(world.r[i] for i in core),
        "ring_coverage": sum(world.m[i] > 0 for i in NEIGH8[target]),
        "ring_m": sum(world.m[i] for i in NEIGH8[target]),
        "core_m": sum(world.m[i] for i in core),
        "core_active": sum(world.a[i] + world.r[i] for i in core),
    }


def select_target(world: World) -> int:
    # Tie breaks to the first row-major site: do NOT follow the survivor.
    return max(
        range(CELLS),
        key=lambda i: (sum(world.a[j] + world.r[j] for j in
                           (i,) + NEIGH8[i]), -i)
    )


def damage(world: World, target: int, p: Protocol, arm: str) -> dict:
    removed = {"a": 0, "r": 0, "m": 0, "s_denied": 0}
    for pos in (target,) + NEIGH8[target]:
        for key in ("a", "r"):
            species = getattr(world, key)
            count = int(p.core_damage * species[pos])
            species[pos] -= count
            world.w[pos] += count
            removed[key] += count
    for pos in NEIGH8[target]:
        count = int(p.ring_damage * world.m[pos])
        world.m[pos] -= count
        world.w[pos] += count
        removed["m"] += count
    if arm == "resource_denied":
        removed["s_denied"] = sum(world.s)
        for pos in range(CELLS):
            world.w[pos] += world.s[pos]
            world.s[pos] = 0
    checked(world, p.initial_s_per_site * CELLS)
    return removed


def run_world(seed: int, origin: str, p: Protocol = Protocol()) -> tuple[list[dict], list[dict]]:
    if not isinstance(seed, int) or seed < 0:
        raise ValueError("Seed must be nonnegative")
    if origin not in ORIGINS:
        raise ValueError("Unknown initial state")
    rng = random.Random(seed * 7 + ORIGINS.index(origin))
    base = initialize(origin, rng, p)
    for _ in range(p.warmup_steps):
        step(base, rng, p, "intact")
    target = select_target(base)
    before = region(base, target)
    qualifying = (
        before["core_a"] >= p.min_pre_a and before["core_r"] >= p.min_pre_r
        and before["ring_coverage"] >= p.min_pre_ring
    )
    canonical_checkpoint = sha(compact({
        "seed": seed, "origin": origin, "state": asdict(base),
        "prng_sha": sha(repr(rng.getstate())), "protocol": asdict(p),
    }))
    initial_rng_state = rng.getstate()
    records, traces = [], []
    for arm in ARMS:
        world = base.duplicate()
        branch_rng = random.Random()
        branch_rng.setstate(initial_rng_state)
        removed = damage(world, target, p, arm)
        after_damage = region(world, target)
        # Same A/R/M disturbance in every treatment (resource-denial additionally converts S).
        local_new_m = 0
        dual_streak, core_streak, shell_streak = 0, 0, 0
        first_dual, first_core, first_shell = None, None, None
        at_or_above_dual = 0
        arm_traces = []
        for t in range(1, p.followup_steps + 1):
            produced = step(world, branch_rng, p, arm, target=target)
            local_new_m += produced
            current = region(world, target)
            core_ok = (
                qualifying and
                current["core_a"] >= p.core_recovery_fraction * before["core_a"]
                and current["core_r"] >= p.core_recovery_fraction * before["core_r"]
            )
            shell_ok = (
                qualifying and current["ring_coverage"] >= p.required_ring_after
                and local_new_m >= p.required_local_m_synth
            )
            both = core_ok and shell_ok
            core_streak = core_streak + 1 if core_ok else 0
            shell_streak = shell_streak + 1 if shell_ok else 0
            dual_streak = dual_streak + 1 if both else 0
            if core_streak >= p.recovery_streak and first_core is None:
                first_core = t - p.recovery_streak + 1
            if shell_streak >= p.recovery_streak and first_shell is None:
                first_shell = t - p.recovery_streak + 1
            if dual_streak >= p.recovery_streak and first_dual is None:
                first_dual = t - p.recovery_streak + 1
            at_or_above_dual += int(both)
            whole = world.counts()
            observation = {
                "seed": seed, "origin": origin, "arm": arm,
                "post_step": t, "eligible": qualifying, "target": target,
                "core_a": current["core_a"], "core_r": current["core_r"],
                "ring_coverage": current["ring_coverage"],
                "ring_m": current["ring_m"],
                "local_shell_synth_since_damage": local_new_m,
                "core_recovered_this_step": bool(core_ok),
                "shell_recovered_this_step": bool(shell_ok),
                "dual_recovered_this_step": bool(both),
                "global": whole, "inflow": world.inflow,
                "mass_residual": checked(world, p.initial_s_per_site * CELLS),
            }
            traces.append(observation)
            arm_traces.append(observation)
        counts = world.counts()
        total_active = counts["a"] + counts["r"]
        final_region = region(world, target)
        records.append({
            "seed": seed, "origin": origin, "arm": arm,
            "checkpoint_sha256": canonical_checkpoint,
            "target": target, "eligible": qualifying,
            "ineligible_reason": (
                None if qualifying else "insufficient_predamage_core_and_ring"
            ),
            "pre_damage_region": before,
            "post_damage_region": after_damage,
            "removed_particles": removed,
            "dual_recovery": (first_dual is not None) if qualifying else None,
            "core_recovery": (first_core is not None) if qualifying else None,
            "shell_recovery": (first_shell is not None) if qualifying else None,
            "first_dual_recovery_step": first_dual,
            "first_core_recovery_step": first_core,
            "first_shell_recovery_step": first_shell,
            "post_steps_at_dual_threshold": at_or_above_dual,
            "final_local_synth_m": local_new_m,
            "final_ring_coverage": final_region["ring_coverage"],
            "final_core_a": final_region["core_a"],
            "final_core_r": final_region["core_r"],
            "final_core_active_fraction": (
                final_region["core_active"] / total_active
                if total_active else 0.0
            ),
            "final_global_counts": counts,
            "max_mass_residual": max(abs(x["mass_residual"]) for x in arm_traces),
            "trace_sha256": sha(
                "".join(compact(x) + "\n" for x in arm_traces)
            ),
            "final_grid": {
                key: list(getattr(world, key)) for key in ("s", "a", "r", "m", "w")
            },
        })
    return records, traces


def paired_bootstrap(diffs: list[int], count: int = 4000,
                     seed: int = 20261008) -> list[float] | None:
    if not diffs:
        return None
    rng = random.Random(seed)
    n = len(diffs)
    draws = sorted(
        sum(diffs[rng.randrange(n)] for _ in range(n)) / n
        for _ in range(count)
    )
    return [
        draws[int(.025 * (count - 1))],
        draws[int(.975 * (count - 1))],
    ]


def summarize(records: list[dict], seeds: list[int]) -> dict:
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("Nonempty unique world seed panel required")
    data = {(r["seed"], r["origin"], r["arm"]): r for r in records}
    expected = {
        (s, o, a) for s in seeds for o in ORIGINS for a in ARMS
    }
    if len(data) != len(records) or set(data) != expected:
        raise AssertionError("Missing/duplicate seed, origin or intervention")
    if any(r["max_mass_residual"] != 0 for r in records):
        raise AssertionError("A molecule ledger did not balance")
    by_origin = {}
    for origin in ORIGINS:
        qualifiers = [
            s for s in seeds if data[s, origin, "intact"]["eligible"]
        ]
        for seed in seeds:
            samples = [data[seed, origin, arm] for arm in ARMS]
            if len({x["checkpoint_sha256"] for x in samples}) != 1:
                raise AssertionError("Variants not branched from identical checkpoints")
            if len({x["eligible"] for x in samples}) != 1:
                raise AssertionError("Variants disagree on eligibility")
            if len({(x["post_damage_region"]["core_a"],
                     x["post_damage_region"]["core_r"]) for x in samples}) != 1:
                raise AssertionError("Unequal A/R damage for paired variants")
        by_arm = {}
        for arm in ARMS:
            eligible_rows = [data[s, origin, arm] for s in qualifiers]
            all_rows = [data[s, origin, arm] for s in seeds]
            by_arm[arm] = {
                "eligible": len(qualifiers),
                "dual_recovered": sum(r["dual_recovery"] is True for r in eligible_rows),
                "core_recovered": sum(r["core_recovery"] is True for r in eligible_rows),
                "shell_recovered": sum(r["shell_recovery"] is True for r in eligible_rows),
                "dual_rate_among_eligible": (
                    sum(r["dual_recovery"] is True for r in eligible_rows)
                    / len(eligible_rows) if eligible_rows else None
                ),
                "dual_positive_among_all_36": sum(r["dual_recovery"] is True for r in all_rows),
                "mean_final_active_local_fraction": (
                    sum(r["final_core_active_fraction"] for r in all_rows) / len(all_rows)
                ),
                "total_post_damage_local_M_synthesis": sum(
                    r["final_local_synth_m"] for r in all_rows
                ),
            }
        contrasted = {}
        for arm in ARMS:
            if arm == "intact":
                continue
            diffs = [
                int(data[s, origin, "intact"]["dual_recovery"]) -
                int(data[s, origin, arm]["dual_recovery"])
                for s in qualifiers
            ]
            contrasted[arm] = {
                "intact_minus_arm": sum(diffs) / len(diffs) if diffs else None,
                "paired_bootstrap_95": paired_bootstrap(diffs),
                "intact_only": sum(d == 1 for d in diffs),
                "arm_only": sum(d == -1 for d in diffs),
                "same": sum(d == 0 for d in diffs),
            }
        by_origin[origin] = {
            "sampled_worlds": len(seeds),
            "eligible_pre_damage_worlds": len(qualifiers),
            "ineligible_worlds_retained": len(seeds) - len(qualifiers),
            "by_arm": by_arm, "paired_dual_recovery": contrasted,
        }
    return {
        "experiment": "CLOSURE-01-SPATIAL",
        "status": "authored_local_spatial_chemistry_not_artificial_life",
        "seeds": seeds,
        "sampled_independent_seed_groups": len(seeds),
        "origins": list(ORIGINS), "arms": list(ARMS),
        "total_warmup_worlds": len(seeds) * len(ORIGINS),
        "total_treatment_runs": len(records),
        "analysis_by_origin": by_origin,
        "claim_limits": [
            "Shell permeability and regeneration are designer-coded",
            "No physical free-energy balance or molecular binding is modeled",
            "No endogenous offspring reproduction, genetically encoded machinery, or agency",
            "Nutrient-only worlds still use researcher-coded basal S->A activation",
            "Core target selected pre-damage but spatial individuality remains ambiguous",
            "Multiple modes share PRNG seed families; only descriptive uncertainty",
        ],
    }


def study(output: Path, seeds: list[int], revision: str = "unspecified",
          p: Protocol = Protocol()) -> dict:
    if not seeds or len(set(seeds)) != len(seeds) or min(seeds) < 0:
        raise ValueError("Invalid held-out panel")
    output.mkdir(parents=True, exist_ok=True)
    records = []
    hashes = {name: hashlib.sha256() for name in ("worlds.jsonl", "traces.jsonl")}
    with (output / "worlds.jsonl").open("w", encoding="utf-8") as wf, (
            output / "traces.jsonl").open("w", encoding="utf-8") as tf:
        for seed in seeds:
            for origin in ORIGINS:
                results, traces = run_world(seed, origin, p)
                for row in results:
                    records.append(row)
                    line = compact(row) + "\n"
                    wf.write(line)
                    hashes["worlds.jsonl"].update(line.encode("utf-8"))
                for row in traces:
                    line = compact(row) + "\n"
                    tf.write(line)
                    hashes["traces.jsonl"].update(line.encode("utf-8"))
    result = summarize(records, seeds)
    result.update({
        "source_revision": revision, "python_version": platform.python_version(),
        "protocol": "docs/CLOSURE-01-SPATIAL-PROTOCOL.md",
        "parameters": asdict(p),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "worlds_sha256": hashes["worlds.jsonl"].hexdigest(),
        "traces_sha256": hashes["traces.jsonl"].hexdigest(),
        "world_record_count": len(records),
        "trace_event_count": len(records) * p.followup_steps,
    })
    (output / "summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", default="6100:6136")
    parser.add_argument("--output-dir", type=Path, default=Path("runs/closure01-spatial"))
    parser.add_argument("--source-revision", default="unspecified")
    args = parser.parse_args(argv)
    try:
        low, high = (int(n) for n in args.seeds.split(":", 1))
        if low < 0 or low >= high:
            raise ValueError()
    except ValueError:
        parser.error("--seeds must be nonnegative start:end")
    result = study(args.output_dir, list(range(low, high)),
                   revision=args.source_revision)
    print(json.dumps({
        "total_treatment_runs": result["total_treatment_runs"],
        "total_trace_events": result["trace_event_count"],
        "origins": {
            o: {
                "eligible": data["eligible_pre_damage_worlds"],
                "dual": {arm: row["dual_recovered"]
                         for arm, row in data["by_arm"].items()},
                "core": {arm: row["core_recovered"]
                         for arm, row in data["by_arm"].items()},
                "retention": {arm: round(row["mean_final_active_local_fraction"], 4)
                              for arm, row in data["by_arm"].items()},
            } for o, data in result["analysis_by_origin"].items()
        },
        "interpretation": "designed spatial catalytic chemistry; not living or emergent cellular autonomy",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
