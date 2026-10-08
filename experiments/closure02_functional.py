"""CLOSURE-02-FUNCTION: cost-controlled shell-production and permeability nulls.

The chemistry is deliberately authored and NOT living digital organization.
All existing CLOSURE-01 and ALxx source/results remain untouched.
See docs/CLOSURE-02-PROTOCOL.md for preregistration and model limitations.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import random

from experiments import closure_spatial as old

ARMS = (
    "shell_effect", "shell_inert", "ghost_effect",
    "ghost_inert", "no_shell",
)
ORIGINS = old.ORIGINS
CORE_HORIZON = old.Protocol().followup_steps


def canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def origin_core(target: int) -> frozenset[int]:
    return frozenset((target,) + old.NEIGH8[target])


def advance(
    world: old.World, rng: random.Random, p: old.Protocol,
    arm: str, *, core: frozenset[int],
) -> dict[str, int]:
    """Exact original model transition augmented by a ghost-M product and flux ledger.

    For old-equivalent arms, the new counters consume NO additional RNG and
    the full state and RNG output must be identical to old.step().
    """
    if arm not in ARMS:
        raise ValueError("Unknown arm")
    if not core or not core.issubset(range(old.CELLS)):
        raise ValueError("Expected previously fixed spatial core")
    counters = {
        "new_a": 0, "new_r": 0, "new_m": 0, "ghost_w": 0,
        "outward_proposals": 0, "outward_moves": 0,
        "inward_proposals": 0, "inward_moves": 0,
        "catalytic_s_consumed": 0,
    }
    for _ in range(p.added_s_per_step):
        world.s[rng.randrange(old.CELLS)] += 1
    world.inflow += p.added_s_per_step

    # Basal activation is unchanged and investigator-designed.
    for pos in range(old.CELLS):
        if world.s[pos] and rng.random() < p.basal_p:
            world.s[pos] -= 1
            world.a[pos] += 1
            world.basal_births += 1

    for pos in range(old.CELLS):
        for _ in range(p.attempts_per_site):
            if world.s[pos] == 0:
                continue
            aw, rw = p.reaction_rate * world.a[pos], p.reaction_rate * world.r[pos]
            if arm == "no_shell":
                weights = (aw, rw, 0.0, 0.0)
            else:
                weights = (aw, rw, aw, rw)
            threshold = rng.random() * (1.0 + sum(weights)) - 1.0
            if threshold < 0:
                continue
            chosen = None
            for index, weight in enumerate(weights):
                threshold -= weight
                if threshold < 0:
                    chosen = index
                    break
            if chosen is None:
                raise AssertionError("Invalid transition selection")
            world.s[pos] -= 1
            world.reaction_events += 1
            counters["catalytic_s_consumed"] += 1
            if chosen == 0:
                world.r[pos] += 1
                world.synth_r += 1
                counters["new_r"] += 1
            elif chosen == 1:
                world.a[pos] += 1
                world.synth_a += 1
                counters["new_a"] += 1
            else:
                dest = old.NEIGH4[pos][rng.randrange(4)]
                if arm in ("ghost_effect", "ghost_inert"):
                    # Same successful synthesis event / spent S / chosen site,
                    # but no functional shell material is made at that event.
                    world.w[dest] += 1
                    counters["ghost_w"] += 1
                else:
                    world.m[dest] += 1
                    world.synth_m += 1
                    counters["new_m"] += 1

    for molecules, probability in (
        (world.a, p.decay_a),
        (world.r, p.decay_r),
        (world.m, p.decay_m),
    ):
        for pos in range(old.CELLS):
            lost = sum(rng.random() < probability for _ in range(molecules[pos]))
            molecules[pos] -= lost
            world.w[pos] += lost
            world.decay_events += lost

    # Preserve original synchronous proposal, RNG draw and update order.
    for molecules, species in (
        (world.s, "s"), (world.a, "a"), (world.r, "r")
    ):
        before = molecules.copy()
        after = [0] * old.CELLS
        for pos, quantity in enumerate(before):
            for _ in range(quantity):
                destination = old.NEIGH4[pos][rng.randrange(4)]
                if species == "s":
                    hop_probability = p.substrate_move_p
                else:
                    hop_probability = old.catalyst_hop_probability(
                        world.m[pos], world.m[destination], p,
                        shell_has_effect=arm not in ("shell_inert", "ghost_inert"),
                    )
                out = species != "s" and pos in core and destination not in core
                in_ = species != "s" and pos not in core and destination in core
                if out:
                    counters["outward_proposals"] += 1
                if in_:
                    counters["inward_proposals"] += 1
                moved = rng.random() < hop_probability
                if moved:
                    after[destination] += 1
                    if out:
                        counters["outward_moves"] += 1
                    if in_:
                        counters["inward_moves"] += 1
                else:
                    after[pos] += 1
        molecules[:] = after
    world.steps += 1
    old.checked(world, p.initial_s_per_site * old.CELLS)
    if (world.reaction_events !=
        world.synth_a + world.synth_r + world.synth_m +
        counters["ghost_w"] + getattr(world, "_prior_ghost", 0)):
        # Incremental ghost count is tracked externally only, without
        # modifying old.World dataclass (see run_world for cumulative sum).
        raise AssertionError("C02 reaction accounting inconsistent")
    return counters


def run_world(seed: int, origin: str, p: old.Protocol = old.Protocol()) -> tuple[list[dict], list[dict]]:
    if not isinstance(seed, int) or seed < 0:
        raise ValueError("Seed must be nonnegative")
    if origin not in ORIGINS:
        raise ValueError("Invalid spatial initial origin")
    rng = random.Random(seed * 7 + ORIGINS.index(origin))
    original = old.initialize(origin, rng, p)
    for _ in range(p.warmup_steps):
        old.step(original, rng, p, "intact")
    target = old.select_target(original)
    before = old.region(original, target)
    eligible = bool(
        before["core_a"] >= p.min_pre_a
        and before["core_r"] >= p.min_pre_r
        and before["ring_coverage"] >= p.min_pre_ring
    )
    checkpoint_hash = sha(canonical({
        "state": asdict(original), "seed": seed, "origin": origin,
        "params": asdict(p), "rng_sha256": sha(repr(rng.getstate())),
    }))
    rng_snapshot = rng.getstate()
    core = origin_core(target)
    initial_mass = p.initial_s_per_site * old.CELLS
    rows, traces = [], []
    for arm in ARMS:
        world = original.duplicate()
        branch_rng = random.Random()
        branch_rng.setstate(rng_snapshot)
        damage = old.damage(world, target, p, "intact")
        damaged_region = old.region(world, target)
        metrics = {
            "new_a": 0, "new_r": 0, "new_m": 0, "ghost_w": 0,
            "outward_proposals": 0, "outward_moves": 0,
            "inward_proposals": 0, "inward_moves": 0,
            "catalytic_s_consumed": 0,
        }
        first_recovery, streak = None, 0
        per_arm = []
        for t in range(1, p.followup_steps + 1):
            # Keep total ghost count outside the original data class.
            world._prior_ghost = metrics["ghost_w"]
            changes = advance(world, branch_rng, p, arm, core=core)
            for name, change in changes.items():
                metrics[name] += change
            current = old.region(world, target)
            qualified = bool(
                eligible and
                current["core_a"] >= p.core_recovery_fraction * before["core_a"] and
                current["core_r"] >= p.core_recovery_fraction * before["core_r"]
            )
            streak = streak+1 if qualified else 0
            if first_recovery is None and streak >= p.recovery_streak:
                first_recovery = t-p.recovery_streak+1
            observation = {
                "seed": seed, "origin": origin, "arm": arm,
                "t": t, "target": target, "eligible": eligible,
                "core_a": current["core_a"], "core_r": current["core_r"],
                "ring_coverage": current["ring_coverage"],
                "core_ok": qualified,
                "inflow": world.inflow,
                "counts": world.counts(),
                "cumulative_flow": metrics.copy(),
                "mass_residual": old.checked(world, initial_mass),
            }
            traces.append(observation)
            per_arm.append(observation)
        core_result = old.region(world, target)
        global_counts = world.counts()
        rows.append({
            "seed": seed, "origin": origin, "arm": arm,
            "checkpoint_sha256": checkpoint_hash,
            "eligible": eligible,
            "ineligible_reason": None if eligible else "below_fixed_predamage_screen",
            "target": target, "pre_damage_region": before,
            "damage_removed": damage, "post_damage_region": damaged_region,
            "core_recovered": (first_recovery is not None) if eligible else None,
            "first_core_recovery": first_recovery,
            "final_core_a": core_result["core_a"],
            "final_core_r": core_result["core_r"],
            "final_local_active_fraction": (
                (core_result["core_a"] + core_result["core_r"]) /
                (global_counts["a"] + global_counts["r"])
                if global_counts["a"] + global_counts["r"] else 0.0
            ),
            "flow": metrics,
            "outward_acceptance_rate": (
                metrics["outward_moves"]/metrics["outward_proposals"]
                if metrics["outward_proposals"] else None
            ),
            "inward_acceptance_rate": (
                metrics["inward_moves"]/metrics["inward_proposals"]
                if metrics["inward_proposals"] else None
            ),
            "final_global_counts": global_counts,
            "max_mass_residual": max(abs(x["mass_residual"]) for x in per_arm),
            "trace_sha256": sha("".join(canonical(t)+"\n" for t in per_arm)),
            "final_grid": {k: getattr(world,k).copy() for k in ("s","a","r","m","w")},
            "rng_sha256": sha(repr(branch_rng.getstate())),
        })
    return rows, traces


def grouped_bootstrap(diffs: dict[int, list[int]], *, n: int = 4000,
                      seed: int = 20261008) -> list[float] | None:
    if not diffs:
        return None
    keys = sorted(diffs)
    rng = random.Random(seed)
    estimates = []
    for _ in range(n):
        values = [v for _ in keys for v in diffs[keys[rng.randrange(len(keys))]]]
        if not values:
            raise AssertionError("Unexpected empty bootstrap resample")
        estimates.append(sum(values) / len(values))
    estimates.sort()
    return [estimates[int(.025*(n-1))], estimates[int(.975*(n-1))]]


def summarize(rows: list[dict], seeds: list[int], p: old.Protocol) -> dict:
    if not seeds or len(seeds) != len(set(seeds)):
        raise ValueError("Nonempty unique seed panel required")
    index = {(row["seed"],row["origin"],row["arm"]):row for row in rows}
    expected = {(seed,origin,arm) for seed in seeds
                for origin in ORIGINS for arm in ARMS}
    if len(index)!=len(rows) or set(index)!=expected:
        raise AssertionError("Missing, unexpected or duplicate treatment")
    if any(row["max_mass_residual"] for row in rows):
        raise AssertionError("Nonconservation in treatment")
    denominators={}
    for origin in ORIGINS:
        valid=[seed for seed in seeds if index[seed,origin,"shell_effect"]["eligible"]]
        for seed in seeds:
            related=[index[seed,origin,arm] for arm in ARMS]
            if len({r["checkpoint_sha256"] for r in related})!=1:
                raise AssertionError("Unequal preintervention checkpoints")
            if len({r["eligible"] for r in related})!=1:
                raise AssertionError("Eligibility differs across forked arms")
            if len({(r["post_damage_region"]["core_a"],
                     r["post_damage_region"]["core_r"],
                     r["post_damage_region"]["ring_coverage"]) for r in related})!=1:
                raise AssertionError("Damage differs across arms")
        rates={}
        for arm in ARMS:
            eligible_rows=[index[seed,origin,arm] for seed in valid]
            attempted_out=sum(row["flow"]["outward_proposals"] for row in eligible_rows)
            accepted_out=sum(row["flow"]["outward_moves"] for row in eligible_rows)
            attempted_in=sum(row["flow"]["inward_proposals"] for row in eligible_rows)
            accepted_in=sum(row["flow"]["inward_moves"] for row in eligible_rows)
            rates[arm]={
                "eligible":len(valid),
                "core_recovery_count":sum(row["core_recovered"] is True for row in eligible_rows),
                "core_recovery_rate":(sum(row["core_recovered"] is True for row in eligible_rows)/len(valid)) if valid else None,
                "outward_proposals":attempted_out,
                "outward_hops":accepted_out,
                "outward_hop_fraction":accepted_out/attempted_out if attempted_out else None,
                "inward_proposals":attempted_in,
                "inward_hops":accepted_in,
                "inward_hop_fraction":accepted_in/attempted_in if attempted_in else None,
                "mean_final_core_active_fraction":sum(row["final_local_active_fraction"] for row in eligible_rows)/len(valid) if valid else None,
                "catalytic_resource_cost":sum(row["flow"]["catalytic_s_consumed"] for row in eligible_rows),
                "new_a":sum(row["flow"]["new_a"] for row in eligible_rows),
                "new_r":sum(row["flow"]["new_r"] for row in eligible_rows),
                "new_m":sum(row["flow"]["new_m"] for row in eligible_rows),
                "ghost_w":sum(row["flow"]["ghost_w"] for row in eligible_rows),
            }
        pairs={}
        for arm in ARMS:
            if arm=="shell_effect": continue
            d={seed:[int(index[seed,origin,"shell_effect"]["core_recovered"])-
                      int(index[seed,origin,arm]["core_recovered"])] for seed in valid}
            vals=[v for vs in d.values() for v in vs]
            pairs[arm]={
                "shell_effect_minus_control":sum(vals)/len(vals) if vals else None,
                "seed_cluster_bootstrap_95":grouped_bootstrap(d),
                "shell_effect_only":sum(v==1 for v in vals),
                "control_only":sum(v==-1 for v in vals),
                "same":sum(v==0 for v in vals),
            }
        denominators[origin]={
            "sampled":len(seeds),"eligible":len(valid),
            "ineligible_retained":len(seeds)-len(valid),
            "arms":rates,"paired_core_recovery":pairs,
        }
    # Pool all matched origins while resampling by independent base seed.
    eligible_pairs=[(seed,origin) for seed in seeds for origin in ORIGINS
                    if index[seed,origin,"shell_effect"]["eligible"]]
    combined={}
    for arm in ARMS:
        active=[index[seed,origin,arm] for seed,origin in eligible_pairs]
        o=sum(row["flow"]["outward_proposals"] for row in active)
        ih=sum(row["flow"]["inward_proposals"] for row in active)
        combined[arm]={
            "eligible":len(active),
            "core_recovered":sum(row["core_recovered"] is True for row in active),
            "outward_proposals":o,
            "outward_hops":sum(row["flow"]["outward_moves"] for row in active),
            "outward_escape_fraction":sum(row["flow"]["outward_moves"] for row in active)/o if o else None,
            "inward_proposals":ih,
            "inward_hops":sum(row["flow"]["inward_moves"] for row in active),
            "inward_entry_fraction":sum(row["flow"]["inward_moves"] for row in active)/ih if ih else None,
            "total_m_or_ghost":sum(row["flow"]["new_m"]+row["flow"]["ghost_w"] for row in active),
            "new_a_and_r":sum(row["flow"]["new_a"]+row["flow"]["new_r"] for row in active),
        }
    combined_pairs={}
    for arm in ARMS:
        if arm=="shell_effect":continue
        d={seed:[] for seed in seeds}
        for seed,origin in eligible_pairs:
            d[seed].append(int(index[seed,origin,"shell_effect"]["core_recovered"])-
                           int(index[seed,origin,arm]["core_recovered"]))
        d={seed:values for seed,values in d.items() if values}
        all_diff=[v for values in d.values() for v in values]
        combined_pairs[arm]={
            "effect":sum(all_diff)/len(all_diff) if all_diff else None,
            "bootstrap_95_seed_cluster":grouped_bootstrap(d),
            "effect_only":sum(x==1 for x in all_diff),
            "control_only":sum(x==-1 for x in all_diff),
        }
    return {
        "experiment":"CLOSURE-02-FUNCTION",
        "status":"finite_authored_chemistry_mechanism_test_not_organism",
        "sampled_seed_groups":len(seeds),
        "three_origin_worlds":len(seeds)*len(ORIGINS),
        "total_treatments":len(rows),
        "eligible_core_worlds":len(eligible_pairs),
        "ineligible_core_worlds":len(seeds)*len(ORIGINS)-len(eligible_pairs),
        "origin_results":denominators,
        "combined_eligible_results":combined,
        "combined_paired_core_recovery":combined_pairs,
        "limitations":[
            "Membrane physics, chemistry, basal activation and observer target are predefined",
            "Ghost reaction matches substrate/event expenditure, not diverged trajectory flux",
            "Transport effect is hardcoded and escape fraction alone is not ecological success",
            "Original mass tally is not a thermodynamic potential ledger",
            "No self-sustaining organism, reproduction, hereditary organization or intelligence",
        ],
    }


def run_study(
    folder: Path, seeds: list[int], revision: str = "unspecified",
    p: old.Protocol = old.Protocol(),
) -> dict:
    if not seeds or len(set(seeds)) != len(seeds) or min(seeds)<0:
        raise ValueError("Nonempty unique nonnegative seeds required")
    folder.mkdir(parents=True,exist_ok=True)
    paths=("worlds.jsonl","traces.jsonl")
    checksums={name:hashlib.sha256() for name in paths}
    rows=[]
    with (folder/paths[0]).open("w",encoding="utf-8",newline="\n") as wf, (
         folder/paths[1]).open("w",encoding="utf-8",newline="\n") as tf:
        for seed in seeds:
            for origin in ORIGINS:
                world_rows,observations=run_world(seed,origin,p)
                for name,handle,data in ((paths[0],wf,world_rows),(paths[1],tf,observations)):
                    for value in data:
                        line=canonical(value)+"\n"
                        handle.write(line)
                        checksums[name].update(line.encode("utf-8"))
                rows.extend(world_rows)
    summary=summarize(rows,seeds,p)
    summary.update({
        "protocol":"docs/CLOSURE-02-PROTOCOL.md",
        "source_revision":revision,
        "source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "original_model_source_sha256":hashlib.sha256(Path(old.__file__).read_bytes()).hexdigest(),
        "python_version":platform.python_version(),
        "parameters":asdict(p),
        "seed_list":seeds,
        "worlds_sha256":checksums[paths[0]].hexdigest(),
        "traces_sha256":checksums[paths[1]].hexdigest(),
        "world_rows":len(rows),
        "trace_rows":len(rows)*p.followup_steps,
    })
    (folder/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds",default="6400:6464")
    parser.add_argument("--output-dir",type=Path,default=Path("runs/closure02-functional"))
    parser.add_argument("--source-revision",default="unspecified")
    args=parser.parse_args(argv)
    try:
        lo,hi=(int(x) for x in args.seeds.split(":",1))
        if lo<0 or hi<=lo:raise ValueError()
    except ValueError:
        parser.error("--seeds must be nonnegative start:end")
    result=run_study(args.output_dir,list(range(lo,hi)),revision=args.source_revision)
    print(json.dumps({
        "total_treatments":result["total_treatments"],
        "eligible_core_worlds":result["eligible_core_worlds"],
        "combined_eligible_results":result["combined_eligible_results"],
        "combined_paired_core_recovery":result["combined_paired_core_recovery"],
        "mass_conservation":"verified all transitions",
        "claim":"controlled engineered reaction-diffusion physics only",
    },sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
