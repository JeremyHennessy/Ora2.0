"""CLOSURE-01 completed-study read-only diagnostic, clearly POST HOC.

Reads fixed JSONL output files and independently checks world and trace hashes.
Does not execute the simulator, mutate the archived experiment, or infer life.
"""
from __future__ import annotations

from collections import defaultdict
import argparse
import hashlib
import json
from pathlib import Path
import random

RAW_SHA256 = {
    "worlds.jsonl": "6a8a81296bffd650ae927a66b7ae21d1ce93690e78ccf4c3190f8aaddd9c6253",
    "traces.jsonl": "79eceef3f3e9e4d492d4b5b955103a50a26ba09569eae9f6322db641f425c28e",
}
ORIGINS = ("clustered", "dispersed", "nutrient_only")
ARMS = (
    "intact", "no_R_to_A", "no_A_to_R",
    "no_M_synthesis", "permeability_null", "resource_denied",
)
METRICS = ("core_recovery", "dual_recovery")


def canonical(row: object) -> str:
    return json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def boot_seed_cluster(seed_lists: dict[int, list[int]],
                      *, resamples: int = 5000, seed: int = 20261008) -> list[float] | None:
    if not seed_lists or not any(seed_lists.values()):
        return None
    keys = sorted(seed_lists)
    rng = random.Random(seed)
    measures = []
    for _ in range(resamples):
        values = []
        for _ in keys:
            values.extend(seed_lists[keys[rng.randrange(len(keys))]])
        if not values:
            raise AssertionError("Impossible all-empty bootstrap replicate")
        measures.append(sum(values) / len(values))
    measures.sort()
    return [
        round(measures[int(.025 * (len(measures)-1))], 4),
        round(measures[int(.975 * (len(measures)-1))], 4),
    ]


def analyze(input_dir: Path, output_dir: Path, *, original_hashes: bool = True) -> dict:
    raw = {name: (input_dir / name).read_bytes() for name in RAW_SHA256}
    hashes = {key: hashlib.sha256(value).hexdigest() for key, value in raw.items()}
    if original_hashes and hashes != RAW_SHA256:
        raise ValueError("CLOSURE-01 archived raw data hash mismatch")
    worlds = [json.loads(line) for line in raw["worlds.jsonl"].splitlines() if line.strip()]
    mapping = {(r["seed"], r["origin"], r["arm"]): r for r in worlds}
    if len(mapping) != len(worlds):
        raise ValueError("Repeated world/origin/intervention records")
    seeds = sorted({s for s, _, _ in mapping})
    required = {(seed, origin, arm) for seed in seeds
                for origin in ORIGINS for arm in ARMS}
    if set(mapping) != required:
        raise ValueError("Incomplete origin/treatment pairs")
    if original_hashes and seeds != list(range(6100, 6136)):
        raise ValueError("Original heldout seed panel changed")
    if any(r["max_mass_residual"] != 0 for r in worlds):
        raise ValueError("Invalid molecule conservation in reported world")
    by_treatment: dict[tuple[int, str, str], hashlib._Hash] = {
        k: hashlib.sha256() for k in mapping
    }
    trace_count = defaultdict(int)
    all_traces = 0
    for line in raw["traces.jsonl"].splitlines():
        if not line.strip():
            continue
        trace = json.loads(line)
        key = (trace["seed"], trace["origin"], trace["arm"])
        if key not in mapping:
            raise ValueError("Trace references an unknown world")
        if trace["mass_residual"] != 0:
            raise ValueError("Trace contains a molecule ledger breach")
        trace_count[key] += 1
        if trace["post_step"] != trace_count[key]:
            raise ValueError("Missing, duplicated or unordered time step")
        by_treatment[key].update((canonical(trace) + "\n").encode("utf-8"))
        all_traces += 1
    if any(trace_count[k] != 60 for k in mapping):
        raise ValueError("Expected exactly 60 post-intervention observations per treatment")
    if any(by_treatment[k].hexdigest() != r["trace_sha256"]
           for k, r in mapping.items()):
        raise ValueError("Trace does not match world-specific SHA256")
    for seed in seeds:
        for origin in ORIGINS:
            cohort = [mapping[seed, origin, arm] for arm in ARMS]
            if len({r["checkpoint_sha256"] for r in cohort}) != 1:
                raise ValueError("Treatments originated from different forks")
            if len({r["eligible"] for r in cohort}) != 1:
                raise ValueError("Inconsistent pre-intervention eligibility")

    eligible = [
        (seed, origin) for seed in seeds for origin in ORIGINS
        if mapping[seed, origin, "intact"]["eligible"]
    ]
    result = {
        "kind": "POST_HOC_CLOSURE01_DIAGNOSTIC",
        "status": "read_only_hash_verified_retrospective_not_new_scientific_experiment",
        "raw_data_sha256": hashes,
        "hashes_verified": original_hashes and hashes == RAW_SHA256,
        "seeds": len(seeds), "origin_groups": len(seeds)*len(ORIGINS),
        "eligible_origin_worlds": len(eligible),
        "treatment_records": len(worlds),
        "verified_step_traces": all_traces,
        "world_and_trace_sha256_verified": True,
        "exploratory_pairwise": {},
    }
    for metric in METRICS:
        measures = {}
        for arm in ARMS:
            if arm == "intact":
                continue
            groups = {seed: [] for seed in seeds}
            intact = comp = wins = losses = 0
            for seed, origin in eligible:
                a = int(mapping[seed, origin, "intact"][metric] is True)
                b = int(mapping[seed, origin, arm][metric] is True)
                intact += a
                comp += b
                wins += int(a > b)
                losses += int(b > a)
                groups[seed].append(a - b)
            measures[arm] = {
                "eligible": len(eligible),
                "intact_successes": intact,
                "control_successes": comp,
                "intact_minus_comparator": (
                    round((intact-comp)/len(eligible), 4) if eligible else None
                ),
                "paired_intact_only": wins,
                "paired_comparator_only": losses,
                "seed_cluster_95_bootstrap": boot_seed_cluster(groups),
            }
        result["exploratory_pairwise"][metric] = measures
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "diagnostic-summary.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", type=Path, default=Path("runs/closure01-spatial"))
    p.add_argument("--output-dir", type=Path, default=Path("runs/closure01-analysis"))
    p.add_argument("--dev-fixture", action="store_true",
                   help="Test fixtures only; never counts as verified original study")
    args = p.parse_args()
    output = analyze(args.input_dir, args.output_dir, original_hashes=not args.dev_fixture)
    print(json.dumps({
        "eligible": output["eligible_origin_worlds"],
        "verified_trace_events": output["verified_step_traces"],
        "core_intact_minus_no_m": output["exploratory_pairwise"]["core_recovery"]["no_M_synthesis"],
        "core_intact_minus_m_inert": output["exploratory_pairwise"]["core_recovery"]["permeability_null"],
        "dual_intact_minus_m_inert": output["exploratory_pairwise"]["dual_recovery"]["permeability_null"],
        "disclaimer": "retrospective exploratory assay, no living organism",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
