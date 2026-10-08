"""AL01-DISCOVERY: preregistered random catalytic-network survey.

This is NOT a simulation of a living organism, chemical thermodynamics, or
spontaneous self-reproducing cells. Read docs/AL01-DISCOVERY-PROTOCOL.md.
No third-party dependencies, network access, or agent/execution interface.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import platform
import random

N = 6
ALL_ARCS = tuple((i, j) for i in range(N) for j in range(N) if i != j)
VARIANTS = (
    "intact",
    "cycle_edge_removed",
    "noncycle_edge_removed",
    "rewired",
    "basal_only",
    "resource_denied",
)


@dataclass(frozen=True)
class Protocol:
    edge_probability: float = 0.26
    supply_per_step: int = 5
    encounters_per_step: int = 10
    catalyst_rate: float = 0.12
    basal_probability: float = 0.02
    decay_probability: float = 0.10
    initial_s: int = 30
    warmup_steps: int = 70
    followup_steps: int = 55
    damage_fraction: float = 0.60
    recovery_threshold: float = 0.75
    recovery_streak: int = 5
    minimum_target: int = 6
    minimum_removed: int = 3

    def __post_init__(self) -> None:
        probabilities = (self.edge_probability, self.basal_probability,
                         self.decay_probability, self.damage_fraction,
                         self.recovery_threshold)
        if any(not 0 <= x <= 1 for x in probabilities):
            raise ValueError("Probabilities/fractions must be in [0,1]")
        if self.catalyst_rate < 0 or min(
            self.supply_per_step, self.encounters_per_step, self.initial_s
        ) < 0:
            raise ValueError("Negative resource/attempt count")
        if min(self.warmup_steps, self.followup_steps, self.recovery_streak,
               self.minimum_target, self.minimum_removed) < 1:
            raise ValueError("Durations and thresholds must be positive")


@dataclass
class State:
    s: int
    x: list[int]
    w: int = 0
    inflow: int = 0
    basal_events: int = 0
    catalytic_events: int = 0
    decay_events: int = 0
    steps: int = 0

    def copy(self) -> "State":
        return State(self.s, self.x.copy(), self.w, self.inflow,
                     self.basal_events, self.catalytic_events,
                     self.decay_events, self.steps)

    def mass(self) -> int:
        return self.s + sum(self.x) + self.w

    def snapshot(self) -> dict:
        return asdict(self)


def canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sample_graph(network_seed: int, p: Protocol) -> tuple[tuple[int, int], ...]:
    rng = random.Random(network_seed)
    return tuple(arc for arc in ALL_ARCS if rng.random() < p.edge_probability)


def path_exists(start: int, goal: int, edges: tuple[tuple[int, int], ...]) -> bool:
    frontier, visited = [start], set()
    while frontier:
        node = frontier.pop()
        if node == goal:
            return True
        if node in visited:
            continue
        visited.add(node)
        frontier.extend(j for i, j in edges if i == node and j not in visited)
    return False


def graph_manifest(network_seed: int, p: Protocol) -> dict:
    edges = sample_graph(network_seed, p)
    cycle_edges = tuple((i, j) for i, j in edges if path_exists(j, i, edges))
    noncycle_edges = tuple(e for e in edges if e not in cycle_edges)
    shuf_rng = random.Random(network_seed ^ 0x5A17)
    rewired = tuple(sorted(shuf_rng.sample(ALL_ARCS, len(edges))))
    return {
        "network_seed": network_seed,
        "arcs": edges,
        "cyclic_arcs": cycle_edges,
        "cycle_edge": cycle_edges[0] if cycle_edges else None,
        "noncycle_edge": noncycle_edges[0] if noncycle_edges else None,
        "target": cycle_edges[0][1] if cycle_edges else None,
        "rewired_arcs": rewired,
        "arc_count": len(edges),
        "has_cycle": bool(cycle_edges),
        "in_degree_of_target": sum(j == cycle_edges[0][1] for _, j in edges) if cycle_edges else None,
    }


def assert_mass(state: State, starting_mass: int) -> int:
    if len(state.x) != N or any(not isinstance(n, int) or n < 0 for n in
                                [state.s, *state.x, state.w, state.inflow]):
        raise AssertionError("Invalid molecule states")
    residual = state.mass() - starting_mass - state.inflow
    if residual:
        raise AssertionError(f"Molecule ledger mismatch: {residual}, step {state.steps}")
    return residual


def step(state: State, rng: random.Random,
         arcs: tuple[tuple[int, int], ...], p: Protocol,
         *, fed: bool, starting_mass: int) -> None:
    new_supply = p.supply_per_step if fed else 0
    state.s += new_supply
    state.inflow += new_supply
    for _ in range(p.encounters_per_step):
        if state.s == 0:
            break
        if rng.random() < p.basal_probability:
            target = rng.randrange(N)
            state.s -= 1
            state.x[target] += 1
            state.basal_events += 1
            continue
        total_weight = 1.0 + sum(p.catalyst_rate * state.x[i] for i, _ in arcs)
        ticket = rng.random() * total_weight - 1.0
        if ticket < 0:
            continue
        for i, j in arcs:
            ticket -= p.catalyst_rate * state.x[i]
            if ticket < 0:
                state.s -= 1
                state.x[j] += 1
                state.catalytic_events += 1
                break
    for i in range(N):
        lost = sum(rng.random() < p.decay_probability for _ in range(state.x[i]))
        state.x[i] -= lost
        state.w += lost
        state.decay_events += lost
    state.steps += 1
    assert_mass(state, starting_mass)


def damage(state: State, p: Protocol, *, deny_resource: bool) -> list[int]:
    removed = [int(count * p.damage_fraction) for count in state.x]
    for i, count in enumerate(removed):
        state.x[i] -= count
        state.w += count
    if deny_resource:
        state.w += state.s
        state.s = 0
    return removed


def variant_arcs(variant: str, graph: dict) -> tuple[tuple[int, int], ...]:
    original = tuple(tuple(e) for e in graph["arcs"])
    if variant in ("intact", "resource_denied"):
        return original
    if variant == "basal_only":
        return ()
    if variant == "rewired":
        return tuple(tuple(e) for e in graph["rewired_arcs"])
    if variant in ("cycle_edge_removed", "noncycle_edge_removed"):
        e = graph["cycle_edge"] if variant == "cycle_edge_removed" else graph["noncycle_edge"]
        return tuple(x for x in original if x != tuple(e)) if e is not None else original
    raise ValueError(f"Unknown variant {variant}")


def run_world(network_seed: int, replica: int, p: Protocol = Protocol(),
              graph: dict | None = None) -> tuple[list[dict], list[dict]]:
    if network_seed < 0 or replica < 0:
        raise ValueError("network_seed and replica must be nonnegative")
    if graph is None:
        graph = graph_manifest(network_seed, p)
    initial = State(p.initial_s, [0] * N)
    starting_mass = initial.mass()
    trajectory_seed = 30000 + network_seed * 10 + replica
    rng = random.Random(trajectory_seed)
    arcs = variant_arcs("intact", graph)
    for _ in range(p.warmup_steps):
        step(initial, rng, arcs, p, fed=True, starting_mass=starting_mass)
    before = initial.snapshot()
    rng_state = rng.getstate()
    checkpoint = digest(canonical({
        "graph": graph, "pre_damage": before,
        "prng": digest(repr(rng_state)), "params": asdict(p),
    }))
    target = graph["target"]
    removed = [int(c * p.damage_fraction) for c in initial.x]
    eligible = bool(target is not None and
                    initial.x[target] >= p.minimum_target and
                    removed[target] >= p.minimum_removed)
    observations = []
    records = []
    for variant in VARIANTS:
        state = initial.copy()
        branch_rng = random.Random()
        branch_rng.setstate(rng_state)
        damage_amounts = damage(state, p, deny_resource=variant == "resource_denied")
        assert_mass(state, starting_mass)
        damaged = state.snapshot()
        active_arcs = variant_arcs(variant, graph)
        streak = 0
        first_recovery = None
        max_residual = 0
        for post_step in range(1, p.followup_steps + 1):
            step(state, branch_rng, active_arcs, p,
                 fed=variant != "resource_denied", starting_mass=starting_mass)
            residual = assert_mass(state, starting_mass)
            max_residual = max(max_residual, abs(residual))
            recovered_now = bool(eligible and state.x[target] >=
                                 p.recovery_threshold * before["x"][target])
            streak = streak + 1 if recovered_now else 0
            if streak >= p.recovery_streak and first_recovery is None:
                first_recovery = post_step - p.recovery_streak + 1
            observations.append({
                "network_seed": network_seed, "replica": replica,
                "variant": variant, "step": post_step,
                "s": state.s, "x": state.x.copy(), "w": state.w,
                "inflow": state.inflow,
                "basal_events": state.basal_events,
                "catalytic_events": state.catalytic_events,
                "decay_events": state.decay_events,
                "residual": residual,
            })
        records.append({
            "network_seed": network_seed, "replica": replica,
            "trajectory_seed": trajectory_seed,
            "variant": variant,
            "checkpoint_sha256": checkpoint,
            "graph_arcs": graph["arcs"], "used_arcs": active_arcs,
            "cycle_edge": graph["cycle_edge"],
            "noncycle_edge": graph["noncycle_edge"],
            "target": target, "in_degree_of_target": graph["in_degree_of_target"],
            "eligible": eligible, "not_evaluable_reason": (
                None if eligible else ("no_cycle" if target is None else "target_below_threshold")
            ),
            "intervention_no_op": (
                variant == "cycle_edge_removed" and graph["cycle_edge"] is None
            ) or (variant == "noncycle_edge_removed" and graph["noncycle_edge"] is None),
            "pre_damage": before, "post_damage": damaged,
            "damage_amounts": damage_amounts,
            "sustained_recovery": (first_recovery is not None) if eligible else None,
            "first_sustained_recovery_step": first_recovery,
            "final": state.snapshot(), "max_abs_mass_residual": max_residual,
        })
    return records, observations


def cluster_bootstrap(groups: dict[int, list[int]], *, n_resamples: int = 4000,
                      seed: int = 20261008) -> list[float] | None:
    if not groups:
        return None
    if n_resamples <= 0:
        raise ValueError("Nonpositive bootstrap sample count")
    keys = sorted(groups)
    rng = random.Random(seed)
    values = []
    for _ in range(n_resamples):
        sampled = [groups[keys[rng.randrange(len(keys))]] for _ in keys]
        all_diffs = [x for group in sampled for x in group]
        values.append(sum(all_diffs) / len(all_diffs))
    values.sort()
    return [values[int(.025 * (len(values) - 1))],
            values[int(.975 * (len(values) - 1))]]


def summarize(records: list[dict], network_seeds: list[int], replicates: int) -> dict:
    if len(set(network_seeds)) != len(network_seeds) or not network_seeds or replicates < 1:
        raise ValueError("Expected unique nonempty network seeds, replicates>=1")
    pairs = {(r["network_seed"], r["replica"], r["variant"]): r for r in records}
    expected = {(seed, k, v) for seed in network_seeds for k in range(replicates)
                for v in VARIANTS}
    if len(pairs) != len(records) or set(pairs) != expected:
        raise ValueError("Duplicate, missing, or unexpected world/variant records")
    eligible_replicates = []
    groups: dict[int, list[int]] = {}
    success_counts = {v: 0 for v in VARIANTS}
    screened = []
    for seed in network_seeds:
        screen_count = 0
        for k in range(replicates):
            by_variant = {v: pairs[(seed, k, v)] for v in VARIANTS}
            if len({r["checkpoint_sha256"] for r in by_variant.values()}) != 1:
                raise AssertionError("Treatments do not share a pre-damage checkpoint")
            if len({r["eligible"] for r in by_variant.values()}) != 1:
                raise AssertionError("Treatments disagree on eligibility")
            for r in by_variant.values():
                if r["max_abs_mass_residual"] != 0:
                    raise AssertionError("Mass accounting invalid")
            if not by_variant["intact"]["eligible"]:
                continue
            eligible_replicates.append((seed, k))
            for v in VARIANTS:
                success_counts[v] += int(by_variant[v]["sustained_recovery"] is True)
            diff = int(by_variant["intact"]["sustained_recovery"]) - int(
                by_variant["cycle_edge_removed"]["sustained_recovery"])
            groups.setdefault(seed, []).append(diff)
            if (by_variant["intact"]["sustained_recovery"] is True
                and by_variant["cycle_edge_removed"]["sustained_recovery"] is False
                and by_variant["basal_only"]["sustained_recovery"] is False):
                screen_count += 1
        if screen_count >= 2:
            screened.append(seed)
    n = len(eligible_replicates)
    contrasts = [d for group in groups.values() for d in group]
    cycle_detected = sum(
        pairs[(seed, 0, "intact")]["cycle_edge"] is not None for seed in network_seeds
    )
    return {
        "experiment": "AL01-DISCOVERY",
        "status": "new_random_network_assay_not_artificial_life_evidence",
        "total_sampled_networks": len(network_seeds),
        "total_trajectories": len(network_seeds) * replicates,
        "total_treatment_runs": len(records),
        "network_seeds": network_seeds,
        "replicates_per_network": replicates,
        "networks_with_cycle": cycle_detected,
        "networks_without_cycle": len(network_seeds) - cycle_detected,
        "eligible_trajectories": n,
        "ineligible_trajectories": len(network_seeds) * replicates - n,
        "eligible_networks": len(groups),
        "sustained_recovery_count_by_variant_among_eligible": success_counts,
        "sustained_recovery_rate_by_variant_among_eligible": {
            v: success_counts[v] / n if n else None for v in VARIANTS
        },
        "paired_intact_minus_cycle_edge_removed": (
            sum(contrasts) / n if n else None
        ),
        "paired_network_cluster_bootstrap_95": cluster_bootstrap(groups),
        "paired_discordance_among_eligible": {
            "intact_only": sum(d == 1 for d in contrasts),
            "knockout_only": sum(d == -1 for d in contrasts),
            "same": sum(d == 0 for d in contrasts),
        },
        "screen_positive_network_seeds": screened,
        "screen_positive_count": len(screened),
        "max_abs_mass_residual": max(r["max_abs_mass_residual"] for r in records),
        "critical_limits": [
            "Graph-cycle target selection is predeclared but may trivially remove the target's only production route",
            "Six-species well-mixed graph dynamics have no individuation, membrane, heredity, or evolved novelty",
            "Basal births and continuing nutrient supply are externally authored assumptions",
            "Screen positives must be replicated on new world RNGs without further parameter tuning",
            "The 3 dynamics replicas are not 3 independent network graphs; uncertainty clusters by network",
        ],
    }


def write_results(output_dir: Path, network_seeds: list[int], replicates: int,
                  params: Protocol = Protocol(),
                  source_revision: str = "unspecified") -> dict:
    if not network_seeds or len(set(network_seeds)) != len(network_seeds) or replicates < 1:
        raise ValueError("Need unique network seeds and a positive replicate count")
    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    record_hash, trace_hash, graph_hash = hashlib.sha256(), hashlib.sha256(), hashlib.sha256()
    with (output_dir / "network-manifest.jsonl").open("w", encoding="utf-8") as fgraph, (
            output_dir / "run-records.jsonl").open("w", encoding="utf-8") as frec, (
            output_dir / "run-traces.jsonl").open("w", encoding="utf-8") as ftrace:
        for network_seed in network_seeds:
            graph = graph_manifest(network_seed, params)
            line = canonical(graph) + "\n"
            fgraph.write(line)
            graph_hash.update(line.encode("utf-8"))
            for replica in range(replicates):
                world_records, world_traces = run_world(network_seed, replica, params, graph)
                for record in world_records:
                    records.append(record)
                    line = canonical(record) + "\n"
                    frec.write(line)
                    record_hash.update(line.encode("utf-8"))
                for trace in world_traces:
                    line = canonical(trace) + "\n"
                    ftrace.write(line)
                    trace_hash.update(line.encode("utf-8"))
    summary = summarize(records, network_seeds, replicates)
    summary.update({
        "source_revision": source_revision,
        "python_version": platform.python_version(),
        "protocol": "docs/AL01-DISCOVERY-PROTOCOL.md",
        "params": asdict(params),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "network_manifest_sha256": graph_hash.hexdigest(),
        "run_records_sha256": record_hash.hexdigest(),
        "run_traces_sha256": trace_hash.hexdigest(),
        "trace_events": len(network_seeds) * replicates * len(VARIANTS) * params.followup_steps,
    })
    (output_dir / "summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("runs/al01-discovery"))
    parser.add_argument("--networks", default="7000:7080",
                        help="Half-open inclusive:start exclusive:end")
    parser.add_argument("--replicates", type=int, default=3)
    parser.add_argument("--source-revision", default="unspecified")
    args = parser.parse_args(argv)
    try:
        start_string, end_string = args.networks.split(":", 1)
        start, end = int(start_string), int(end_string)
        if start < 0 or end <= start or args.replicates < 1:
            raise ValueError()
    except ValueError:
        parser.error("--networks must be nonnegative start:end; replicates >=1")
    summary = write_results(args.output_dir, list(range(start, end)), args.replicates,
                            source_revision=args.source_revision)
    print(json.dumps({
        "sampled_networks": summary["total_sampled_networks"],
        "eligible_trajectories": summary["eligible_trajectories"],
        "cycle_networks": summary["networks_with_cycle"],
        "screen_positive_networks": summary["screen_positive_network_seeds"],
        "recovery_counts": summary["sustained_recovery_count_by_variant_among_eligible"],
        "paired_difference": summary["paired_intact_minus_cycle_edge_removed"],
        "network_cluster_interval": summary["paired_network_cluster_bootstrap_95"],
        "mass_residual": summary["max_abs_mass_residual"],
        "disclaimer": "synthetic exploratory reaction-network assay; no digital life",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
