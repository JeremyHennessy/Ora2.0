"""AL01-CAL: deterministic measurement calibration, NOT an artificial organism.

See docs/AL01-CAL-PROTOCOL.md for pre-registered experiment parameters,
interventions, outcomes and interpretation limits. Standard library only.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict, dataclass, replace
import hashlib
import json
from pathlib import Path
import platform
import random
from typing import Iterable

VARIANTS = ("intact", "feedback-knockout", "inert", "starved")


@dataclass(frozen=True)
class Protocol:
    initial_s: int = 35
    initial_a: int = 10
    initial_b: int = 10
    supply: int = 4
    attempts: int = 6
    catalytic_rate: float = 0.08
    decay_probability: float = 0.10
    warmup_steps: int = 40
    observation_steps: int = 60
    damage_a: float = 0.75
    damage_b: float = 0.35
    recovery_ratio: float = 0.75
    consecutive_recovery_steps: int = 5

    def __post_init__(self) -> None:
        if min(self.initial_s, self.initial_a, self.initial_b) < 0:
            raise ValueError("Initial molecule counts must be nonnegative")
        if self.supply < 0 or self.attempts < 0 or self.warmup_steps < 0 or self.observation_steps <= 0:
            raise ValueError("Invalid duration or number of events")
        if self.catalytic_rate < 0 or not 0 <= self.decay_probability <= 1:
            raise ValueError("Invalid reaction or decay rate")
        if any(not 0 <= v <= 1 for v in (self.damage_a, self.damage_b, self.recovery_ratio)):
            raise ValueError("Invalid fractional intervention")
        if self.consecutive_recovery_steps < 1:
            raise ValueError("Consecutive recovery must be positive")


@dataclass
class Reactor:
    s: int
    a: int
    b: int
    w: int = 0
    cumulative_supply: int = 0
    conversions_a_to_b: int = 0
    conversions_b_to_a: int = 0
    decay_a: int = 0
    decay_b: int = 0
    steps: int = 0

    @property
    def mass(self) -> int:
        return self.s + self.a + self.b + self.w


def assert_valid(state: Reactor, initial_mass: int) -> int:
    populations = (state.s, state.a, state.b, state.w)
    if any(not isinstance(x, int) or x < 0 for x in populations):
        raise AssertionError(f"Invalid constituent population: {populations}")
    residual = state.mass - initial_mass - state.cumulative_supply
    if residual:
        raise AssertionError(f"Non-conservation: {residual} at step {state.steps}")
    return residual


def tick(state: Reactor, rng: random.Random, params: Protocol, variant: str, initial_mass: int) -> None:
    """Advance a well-mixed reaction system, without creature-specific rescue rules."""
    if variant not in VARIANTS:
        raise ValueError(f"Unknown intervention {variant}")
    supplied = 0 if variant == "starved" else params.supply
    state.s += supplied
    state.cumulative_supply += supplied
    for _ in range(params.attempts):
        if not state.s:
            break
        weight_ab = params.catalytic_rate * state.a if variant in ("intact", "feedback-knockout", "starved") else 0.0
        weight_ba = params.catalytic_rate * state.b if variant in ("intact", "starved") else 0.0
        sample = rng.random() * (1.0 + weight_ab + weight_ba)
        if sample < weight_ab:
            state.s -= 1
            state.b += 1
            state.conversions_a_to_b += 1
        elif sample < weight_ab + weight_ba:
            state.s -= 1
            state.a += 1
            state.conversions_b_to_a += 1
    d_a = sum(rng.random() < params.decay_probability for _ in range(state.a))
    d_b = sum(rng.random() < params.decay_probability for _ in range(state.b))
    state.a -= d_a
    state.b -= d_b
    state.w += d_a + d_b
    state.decay_a += d_a
    state.decay_b += d_b
    state.steps += 1
    assert_valid(state, initial_mass)


def damage(state: Reactor, params: Protocol, *, starve: bool = False) -> dict[str, int]:
    """Move damaged molecules and, optionally, remaining feedstock to inert waste."""
    d_a = int(state.a * params.damage_a)
    d_b = int(state.b * params.damage_b)
    state.a -= d_a
    state.b -= d_b
    state.w += d_a + d_b
    if starve:
        state.w += state.s
        state.s = 0
    return {"a_removed": d_a, "b_removed": d_b}


def passes_recovery(pre_a: int, pre_b: int, post_a: int, post_b: int, ratio: float) -> bool:
    # Zero baseline is uninformative: don't classify extinct/trivial wells as recovered.
    return pre_a > 0 and pre_b > 0 and post_a >= ratio * pre_a and post_b >= ratio * pre_b


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def run_world(seed: int, params: Protocol = Protocol()) -> tuple[list[dict], list[dict]]:
    if not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be nonnegative integer")
    baseline = Reactor(params.initial_s, params.initial_a, params.initial_b)
    initial_mass = baseline.mass
    rng = random.Random(seed)
    for _ in range(params.warmup_steps):
        tick(baseline, rng, params, "intact", initial_mass)
    checkpoint = replace(baseline)
    rng_checkpoint = rng.getstate()
    checkpoint_hash = sha256_text(canonical_json({
        "seed": seed, "state": asdict(checkpoint),
        "rng_state_hash": sha256_text(repr(rng_checkpoint)), "config": asdict(params),
    }))
    records: list[dict] = []
    traces: list[dict] = []
    for variant in VARIANTS:
        state = replace(checkpoint)
        branch_rng = random.Random()
        branch_rng.setstate(rng_checkpoint)
        intervention = damage(state, params, starve=(variant == "starved"))
        assert_valid(state, initial_mass)
        post_intervention = asdict(state)
        streak = 0
        first_recovery = None
        variant_traces: list[dict] = []
        for step in range(1, params.observation_steps + 1):
            tick(state, branch_rng, params, variant, initial_mass)
            recovered = passes_recovery(checkpoint.a, checkpoint.b, state.a, state.b, params.recovery_ratio)
            streak = streak + 1 if recovered else 0
            if streak >= params.consecutive_recovery_steps and first_recovery is None:
                first_recovery = step - params.consecutive_recovery_steps + 1
            trace = {
                "seed": seed, "variant": variant, "post_step": step,
                "s": state.s, "a": state.a, "b": state.b, "w": state.w,
                "total": state.mass, "cumulative_supply": state.cumulative_supply,
                "mass_residual": assert_valid(state, initial_mass),
                "conversions_a_to_b": state.conversions_a_to_b - checkpoint.conversions_a_to_b,
                "conversions_b_to_a": state.conversions_b_to_a - checkpoint.conversions_b_to_a,
                "decay_a": state.decay_a - checkpoint.decay_a,
                "decay_b": state.decay_b - checkpoint.decay_b,
            }
            variant_traces.append(trace)
            traces.append(trace)
        records.append({
            "seed": seed, "variant": variant,
            "pristine_checkpoint_sha256": checkpoint_hash,
            "pre_damage": asdict(checkpoint), "intervention": intervention,
            "post_intervention": post_intervention,
            "sustained_recovery": first_recovery is not None,
            "first_sustained_recovery_step": first_recovery,
            "post_conversions_a_to_b": state.conversions_a_to_b - checkpoint.conversions_a_to_b,
            "post_conversions_b_to_a": state.conversions_b_to_a - checkpoint.conversions_b_to_a,
            "post_decay_a": state.decay_a - checkpoint.decay_a,
            "post_decay_b": state.decay_b - checkpoint.decay_b,
            "final": asdict(state),
            "max_abs_ledger_residual": max(abs(t["mass_residual"]) for t in variant_traces),
            "trace_sha256": sha256_text("\n".join(canonical_json(t) for t in variant_traces) + "\n"),
        })
    return records, traces


def paired_bootstrap(differences: list[int], *, resamples: int = 5000, seed: int = 424242) -> list[float]:
    if not differences or resamples < 1:
        raise ValueError("Bootstrap needs data and a positive resample count")
    rng = random.Random(seed)
    n = len(differences)
    samples = sorted(sum(differences[rng.randrange(n)] for _ in range(n)) / n for _ in range(resamples))
    return [samples[int(0.025 * (resamples - 1))], samples[int(0.975 * (resamples - 1))]]


def analyze(records: list[dict], seed_order: list[int]) -> dict:
    if not seed_order or len(set(seed_order)) != len(seed_order):
        raise ValueError("seed order must be unique and nonempty")
    by_key = {(r["seed"], r["variant"]): r for r in records}
    if len(by_key) != len(records):
        raise ValueError("Duplicate seed/variant records")
    if set(by_key) != {(seed, variant) for seed in seed_order for variant in VARIANTS}:
        raise ValueError("Missing or extra treatment records")
    counts = {
        variant: sum(bool(by_key[(seed, variant)]["sustained_recovery"]) for seed in seed_order)
        for variant in VARIANTS
    }
    differences = [
        int(by_key[(seed, "intact")]["sustained_recovery"]) -
        int(by_key[(seed, "feedback-knockout")]["sustained_recovery"])
        for seed in seed_order
    ]
    return {
        "status": "engineering_calibration_not_alife_evidence",
        "n_independent_worlds": len(seed_order),
        "seed_order": seed_order,
        "recovered_by_variant": counts,
        "recovery_rates_by_variant": {k: v / len(seed_order) for k, v in counts.items()},
        "intact_minus_knockout_paired_difference": sum(differences) / len(seed_order),
        "paired_bootstrap_percentile_95_interval": paired_bootstrap(differences),
        "paired_discordance": {
            "intact_only": sum(x == 1 for x in differences),
            "knockout_only": sum(x == -1 for x in differences),
            "both_same": sum(x == 0 for x in differences),
        },
        "max_mass_conservation_residual": max(r["max_abs_ledger_residual"] for r in records),
        "pre_damage_zero_constituent_worlds": sum(
            by_key[(seed, "intact")]["pre_damage"]["a"] == 0 or
            by_key[(seed, "intact")]["pre_damage"]["b"] == 0 for seed in seed_order
        ),
        "limitation": ("Hand-authored catalytic topology and initial reagents; calibration only, "
                       "NOT evidence of spontaneous life, self-produced boundary, heredity, "
                       "evolution, intelligence, or consciousness."),
    }


def write_results(output_dir: Path, seeds: list[int], params: Protocol, source_revision: str = "unspecified") -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    traces: list[dict] = []
    for seed in seeds:
        results, events = run_world(seed, params)
        records.extend(results)
        traces.extend(events)
    summary = analyze(records, seeds)
    summary["protocol"] = "docs/AL01-CAL-PROTOCOL.md"
    summary["protocol_parameters"] = asdict(params)
    summary["source_revision"] = source_revision
    summary["python_version"] = platform.python_version()
    summary["source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    summary["run_records_sha256"] = sha256_text("\n".join(canonical_json(r) for r in records) + "\n")
    summary["run_traces_sha256"] = sha256_text("\n".join(canonical_json(t) for t in traces) + "\n")
    for filename, rows in (("run-records.jsonl", records), ("run-traces.jsonl", traces)):
        (output_dir / filename).write_text("\n".join(canonical_json(x) for x in rows) + "\n", encoding="utf-8")
    (output_dir / "summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return summary


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("runs/al01-cal"))
    parser.add_argument("--seeds", default="1000:1032", help="half-open range start:end")
    parser.add_argument("--source-revision", default="unspecified")
    args = parser.parse_args(argv)
    try:
        start_string, end_string = args.seeds.split(":", 1)
        start, end = int(start_string), int(end_string)
        if start < 0 or end <= start:
            raise ValueError()
    except ValueError:
        parser.error("Expected --seeds start:end with 0<=start<end")
    summary = write_results(args.output_dir, list(range(start, end)), Protocol(), args.source_revision)
    print(json.dumps({
        "output_dir": str(args.output_dir),
        "n": summary["n_independent_worlds"],
        "recovered": summary["recovered_by_variant"],
        "paired_difference": summary["intact_minus_knockout_paired_difference"],
        "interval_95": summary["paired_bootstrap_percentile_95_interval"],
        "max_mass_ledger_residual": summary["max_mass_conservation_residual"],
        "interpretation": "measurement calibration only, not digital life",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
