"""AL01-RVCS: predeclared distributed catalytic redundancy test.

One synthetic, finite, non-physical reaction model; NOT biological life,
artificial intelligence, or independent scientific replication. The protocol
was frozen before evaluating holdout network seeds.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import random

from experiments.network_discovery import (
    N, Protocol, State, assert_mass, canonical, damage, digest,
    path_exists, sample_graph, step,
)

VARIANTS = (
    "intact", "cut_first", "cut_second", "cut_both",
    "sham_two", "basal_only", "resource_denied",
)


def select_structure(edges: tuple[tuple[int, int], ...]) -> dict:
    """Deterministically select redundant target and off-target sham, outcome-blind."""
    cyc = tuple(e for e in edges if path_exists(e[1], e[0], edges))
    for target in range(N):
        incoming = tuple(e for e in edges if e[1] == target)
        cyclic_incoming = tuple(e for e in cyc if e[1] == target)
        unrelated = tuple(e for e in edges if e[1] != target)
        if len(incoming) >= 3 and len(cyclic_incoming) >= 2 and len(unrelated) >= 2:
            return {
                "target": target,
                "target_in_degree": len(incoming),
                "cut_edges": cyclic_incoming[:2],
                "sham_edges": unrelated[:2],
                "cyclic_incoming_count": len(cyclic_incoming),
                "structurally_eligible": True,
                "missing_reason": None,
            }
    return {
        "target": None, "target_in_degree": None,
        "cut_edges": (), "sham_edges": (),
        "cyclic_incoming_count": 0,
        "structurally_eligible": False,
        "missing_reason": "no_structural_candidate",
    }


def network_manifest(network_seed: int, params: Protocol = Protocol()) -> dict:
    arcs = sample_graph(network_seed, params)
    return {
        "network_seed": network_seed,
        "arcs": arcs,
        "arc_count": len(arcs),
        **select_structure(arcs),
    }


def for_variant(variant: str, graph: dict) -> tuple[tuple[int, int], ...]:
    if variant not in VARIANTS:
        raise ValueError(f"Unknown intervention {variant}")
    original = tuple(tuple(e) for e in graph["arcs"])
    if variant == "basal_only":
        return ()
    if not graph["structurally_eligible"] or variant in ("intact", "resource_denied"):
        return original
    first, second = (tuple(e) for e in graph["cut_edges"])
    if variant == "cut_first":
        to_remove = (first,)
    elif variant == "cut_second":
        to_remove = (second,)
    elif variant == "cut_both":
        to_remove = (first, second)
    else:
        to_remove = tuple(tuple(e) for e in graph["sham_edges"])
    return tuple(e for e in original if e not in to_remove)


def run_world(network_seed: int, replica: int, params: Protocol = Protocol(),
              graph: dict | None = None) -> tuple[list[dict], list[dict]]:
    if network_seed < 0 or replica < 0:
        raise ValueError("Expected nonnegative seed and replica")
    graph = graph or network_manifest(network_seed, params)
    start = State(params.initial_s, [0] * N)
    starting_mass = start.mass()
    trajectory_seed = 50000 + network_seed * 10 + replica
    rng = random.Random(trajectory_seed)
    for _ in range(params.warmup_steps):
        step(start, rng, for_variant("intact", graph),
             params, fed=True, starting_mass=starting_mass)
    pre = start.snapshot()
    rng_checkpoint = rng.getstate()
    checkpoint_hash = digest(canonical({
        "graph": graph, "pre": pre, "rng": digest(repr(rng_checkpoint)),
        "params": asdict(params),
    }))
    target = graph["target"]
    expected_damage = [int(c * params.damage_fraction) for c in start.x]
    eligible = bool(graph["structurally_eligible"]
                    and pre["x"][target] >= params.minimum_target
                    and expected_damage[target] >= params.minimum_removed)
    not_eligible_reason = (
        None if eligible
        else ("no_structural_candidate" if target is None else "low_pre_damage_target")
    )
    records, traces = [], []
    for variant in VARIANTS:
        state = start.copy()
        branch_rng = random.Random()
        branch_rng.setstate(rng_checkpoint)
        removed = damage(state, params, deny_resource=(variant == "resource_denied"))
        assert_mass(state, starting_mass)
        post_damage = state.snapshot()
        arcs = for_variant(variant, graph)
        first_recovery, streak, max_residual = None, 0, 0
        for observed_step in range(1, params.followup_steps + 1):
            step(state, branch_rng, arcs, params,
                 fed=(variant != "resource_denied"), starting_mass=starting_mass)
            residual = assert_mass(state, starting_mass)
            max_residual = max(max_residual, abs(residual))
            recovered = bool(
                eligible and state.x[target] >=
                params.recovery_threshold * pre["x"][target]
            )
            streak = streak + 1 if recovered else 0
            if first_recovery is None and streak >= params.recovery_streak:
                first_recovery = observed_step - params.recovery_streak + 1
            traces.append({
                "network_seed": network_seed, "replica": replica, "variant": variant,
                "post_step": observed_step, "s": state.s,
                "x": state.x.copy(), "w": state.w,
                "inflow": state.inflow, "basal_events": state.basal_events,
                "catalytic_events": state.catalytic_events,
                "decay_events": state.decay_events,
                "mass_residual": residual,
            })
        records.append({
            "network_seed": network_seed, "replica": replica,
            "trajectory_seed": trajectory_seed,
            "variant": variant,
            "checkpoint_sha256": checkpoint_hash,
            "structure": graph,
            "eligible": eligible, "not_eligible_reason": not_eligible_reason,
            "used_arcs": arcs,
            "cut_noop_due_to_no_structure": (
                not graph["structurally_eligible"]
                and variant in ("cut_first", "cut_second", "cut_both", "sham_two")
            ),
            "pre_damage": pre, "post_damage": post_damage,
            "damage_amounts": removed,
            "sustained_recovery": (first_recovery is not None) if eligible else None,
            "first_recovery_step": first_recovery,
            "final": state.snapshot(),
            "max_abs_mass_residual": max_residual,
        })
    return records, traces


def signature(by_variant: dict[str, dict]) -> bool:
    """All requirements precommitted; ineligible worlds cannot be signatures."""
    if not by_variant["intact"]["eligible"]:
        return False
    return (
        all(by_variant[v]["sustained_recovery"] is True for v in
            ("intact", "cut_first", "cut_second", "sham_two"))
        and all(by_variant[v]["sustained_recovery"] is False for v in
                ("cut_both", "basal_only", "resource_denied"))
    )


def cluster_percentile(
    groups: dict[int, list[int]], *, repeats: int = 4000,
    seed: int = 20261009,
) -> list[float] | None:
    if not groups:
        return None
    rng = random.Random(seed)
    keys = sorted(groups)
    rates = []
    for _ in range(repeats):
        sampled = [groups[keys[rng.randrange(len(keys))]] for _ in keys]
        values = [v for g in sampled for v in g]
        rates.append(sum(values) / len(values))
    rates.sort()
    return [rates[int(.025 * (repeats-1))],
            rates[int(.975 * (repeats-1))]]


def summarize(records: list[dict], seeds: list[int], replicates: int) -> dict:
    if len(set(seeds)) != len(seeds) or not seeds or replicates < 1:
        raise ValueError("Unique nonempty network seeds and positive replica count required")
    entries = {(r["network_seed"], r["replica"], r["variant"]): r for r in records}
    needed = {(net, rep, v) for net in seeds
              for rep in range(replicates) for v in VARIANTS}
    if len(entries) != len(records) or set(entries) != needed:
        raise ValueError("Missing/duplicate treatment worlds")
    graph_eligible = 0
    trajectory_eligible = 0
    eligible_networks = set()
    counts = dict.fromkeys(VARIANTS, 0)
    screens = []
    signature_groups: dict[int, list[int]] = {}
    dual_minus_sham_groups: dict[int, list[int]] = {}
    for seed in seeds:
        first = entries[(seed, 0, "intact")]
        if first["structure"]["structurally_eligible"]:
            graph_eligible += 1
        graph_signature_count = 0
        for rep in range(replicates):
            by_variant = {v: entries[(seed, rep, v)] for v in VARIANTS}
            if len({r["checkpoint_sha256"] for r in by_variant.values()}) != 1:
                raise AssertionError("Forks do not share checkpoint")
            if len({r["eligible"] for r in by_variant.values()}) != 1:
                raise AssertionError("Forks disagree on eligibility")
            if any(r["max_abs_mass_residual"] for r in by_variant.values()):
                raise AssertionError("Molecule conservation invalid")
            if not by_variant["intact"]["eligible"]:
                continue
            trajectory_eligible += 1
            eligible_networks.add(seed)
            for v in VARIANTS:
                counts[v] += int(by_variant[v]["sustained_recovery"] is True)
            is_signature = int(signature(by_variant))
            graph_signature_count += is_signature
            signature_groups.setdefault(seed, []).append(is_signature)
            dual_minus_sham_groups.setdefault(seed, []).append(
                int(by_variant["sham_two"]["sustained_recovery"] is True) -
                int(by_variant["cut_both"]["sustained_recovery"] is True)
            )
        if graph_signature_count >= 2:
            screens.append(seed)
    paired_values = [x for group in dual_minus_sham_groups.values() for x in group]
    signature_values = [x for group in signature_groups.values() for x in group]
    return {
        "experiment": "AL01-RVCS",
        "status": "synthetic_redundant_catalysis_probe_not_digital_life",
        "sampled_networks": len(seeds),
        "graph_seeds": seeds,
        "replicates_per_graph": replicates,
        "stochastic_trajectories": len(seeds) * replicates,
        "treatment_runs": len(records),
        "structurally_eligible_networks": graph_eligible,
        "structurally_ineligible_networks": len(seeds) - graph_eligible,
        "eligible_networks_after_pre_damage_screen": len(eligible_networks),
        "eligible_trajectories": trajectory_eligible,
        "ineligible_trajectories": len(seeds) * replicates - trajectory_eligible,
        "sustained_recovery_counts_among_eligible": counts,
        "sustained_recovery_rates_among_eligible": {
            v: counts[v] / trajectory_eligible if trajectory_eligible else None
            for v in VARIANTS
        },
        "signature_trajectories": sum(signature_values),
        "signature_fraction_eligible": (
            sum(signature_values) / trajectory_eligible if trajectory_eligible else None
        ),
        "signature_fraction_network_cluster_bootstrap_95": cluster_percentile(
            signature_groups
        ),
        "paired_sham_minus_double_cut": (
            sum(paired_values) / trajectory_eligible if trajectory_eligible else None
        ),
        "paired_sham_minus_double_cut_cluster_bootstrap_95": cluster_percentile(
            dual_minus_sham_groups
        ),
        "screen_positive_network_seeds": screens,
        "screen_positive_network_count": len(screens),
        "max_mass_residual": max(r["max_abs_mass_residual"] for r in records),
        "interpretation_limitations": [
            "Even a positive redundancy signature in a toy graph is NOT evidence of life",
            "Recovery specifically tracks a graph-selected target; testing aligned to topology",
            "Equal-edge-count sham does not preserve catalytic flux",
            "Basal source and food input are model assumptions not metabolism",
            "Screening positives are exploratory and require new independent graph samples",
        ],
    }


def run_study(output: Path, seeds: list[int], replicates: int,
              params: Protocol = Protocol(), revision: str = "unspecified") -> dict:
    if not seeds or len(seeds) != len(set(seeds)) or replicates < 1:
        raise ValueError("Invalid sample definition")
    output.mkdir(parents=True, exist_ok=True)
    all_records = []
    hashes = {name: hashlib.sha256() for name in
              ("network-manifest.jsonl", "run-records.jsonl", "run-traces.jsonl")}
    with (output / "network-manifest.jsonl").open("w", encoding="utf-8") as gn, (
            output / "run-records.jsonl").open("w", encoding="utf-8") as rr, (
            output / "run-traces.jsonl").open("w", encoding="utf-8") as tr:
        for net in seeds:
            graph = network_manifest(net, params)
            raw = canonical(graph) + "\n"
            gn.write(raw)
            hashes["network-manifest.jsonl"].update(raw.encode("utf-8"))
            for rep in range(replicates):
                records, traces = run_world(net, rep, params, graph)
                for r in records:
                    all_records.append(r)
                    raw = canonical(r) + "\n"
                    rr.write(raw)
                    hashes["run-records.jsonl"].update(raw.encode("utf-8"))
                for t in traces:
                    raw = canonical(t) + "\n"
                    tr.write(raw)
                    hashes["run-traces.jsonl"].update(raw.encode("utf-8"))
    result = summarize(all_records, seeds, replicates)
    result.update({
        "protocol": "docs/AL01-RVCS-PROTOCOL.md",
        "revision": revision,
        "python": platform.python_version(),
        "params": asdict(params),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "graph_manifest_sha256": hashes["network-manifest.jsonl"].hexdigest(),
        "run_records_sha256": hashes["run-records.jsonl"].hexdigest(),
        "run_traces_sha256": hashes["run-traces.jsonl"].hexdigest(),
        "trace_events": len(seeds) * replicates * len(VARIANTS) * params.followup_steps,
    })
    (output / "summary.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--networks", default="9000:9144", help="half-open start:end")
    parser.add_argument("--replicates", type=int, default=3)
    parser.add_argument("--output-dir", type=Path, default=Path("runs/al01-rvcs"))
    parser.add_argument("--source-revision", default="unspecified")
    args = parser.parse_args(argv)
    try:
        a, b = (int(t) for t in args.networks.split(":", 1))
        if a < 0 or b <= a or args.replicates < 1:
            raise ValueError()
    except ValueError:
        parser.error("Need --networks nonnegative start:end and replicates>=1")
    result = run_study(args.output_dir, list(range(a, b)), args.replicates,
                       revision=args.source_revision)
    print(json.dumps({
        "sampled_networks": result["sampled_networks"],
        "structurally_eligible": result["structurally_eligible_networks"],
        "eligible_trajectories": result["eligible_trajectories"],
        "counts": result["sustained_recovery_counts_among_eligible"],
        "signature_trajectories": result["signature_trajectories"],
        "screen_positive_networks": result["screen_positive_network_seeds"],
        "signature_cluster_interval": result["signature_fraction_network_cluster_bootstrap_95"],
        "sham_minus_double_cut": result["paired_sham_minus_double_cut"],
        "mass_residual": result["max_mass_residual"],
        "disclaimer": "synthetic reaction graph; NOT artificial life",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
