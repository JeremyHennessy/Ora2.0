"""Frozen static encounter reference. No dynamical worlds or repair trials."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
from itertools import product
import json
import math
from pathlib import Path
import random

P, T = (0, 1, 2, 3), (1, 2, 3, 0)
SEEDS = tuple(range(48, 80))
ROOT = Path(__file__).resolve().parents[1]
FILES = ("docs/CLOSURE-03-ADEQUACY-PROTOCOL.md", "experiments/process_adequacy.py",
         "experiments/process_adequacy_audit.py")


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def splice(a, b):
    return (a[1], b[1], a[2], b[2]) if a[0] == b[3] else None


def reaches(q, attempts):
    return (1 - q) ** attempts <= Fraction(1, 5)


def minimum_draws(q):
    if not q:
        return None
    if q == 1:
        return 1
    estimate = max(1, math.ceil(math.log(0.2) / math.log1p(-float(q))))
    while not reaches(q, estimate):
        estimate += 1
    while estimate > 1 and reaches(q, estimate - 1):
        estimate -= 1
    return estimate


def rate(q, attempts):
    return {"numerator": q.numerator, "denominator": q.denominator,
            "at_least_one_reference": float(1 - (1 - q) ** attempts),
            "throughput_reference_pass": reaches(q, attempts),
            "minimum_static_draws_for_four_fifths": minimum_draws(q)}


def tokens(genomes):
    return [{"id": f"g{i}", "genome": list(g)} for i, g in enumerate(genomes)]


def genesis(seed):
    rng = random.Random(seed)
    return tokens([tuple(rng.randrange(4) for _ in range(4)) for _ in range(32)])


def fixtures():
    a, b, s, z = (1, 0, 2, 0), (2, 1, 3, 1), (0, 0, 0, 3), (3, 3, 3, 3)
    return {"dense_match": tokens([a] * 8 + [b] * 8 + [s] * 16),
            "sparse_match": tokens([a, b, s] + [z] * 29),
            "sparse_unmatched": tokens([a, b] + [z] * 30),
            "absent": tokens([z] * 32)}


def measure(initial, precursor, fuel=128):
    live = {x["id"]: tuple(x["genome"]) for x in initial if tuple(x["genome"]) not in (P, T)}
    sham = {k for k, g in live.items() if (g[0], g[3]) == (P[0], P[3])}
    recipes = matched = 0
    for a, ga in live.items():
        for b, gb in live.items():
            if a != b and splice(ga, gb) == P:
                recipes += 1
                matched += bool(sham - {a, b})
    denominator = len(live) * (len(live) - 1)
    q = Fraction(recipes, denominator) if denominator else Fraction(0)
    qm = Fraction(matched, denominator) if denominator else Fraction(0)
    attempts = min(128, fuel)
    return {"initial_tokens": initial, "removed_ids": [x["id"] for x in initial if tuple(x["genome"]) in (P, T)],
            "live_tokens": len(live), "ordered_distinct_id_pairs": denominator,
            "recipe_pairs": recipes, "matched_recipe_pairs": matched,
            "precursor": precursor, "fuel": fuel, "reference_attempts": attempts,
            "recipe_rate": rate(q, attempts), "matched_rate": rate(qm, attempts),
            "paid_recipe_rate": rate(q if precursor >= 4 else Fraction(0), attempts),
            "paid_matched_rate": rate(qm if precursor >= 4 else Fraction(0), attempts)}


def table_reference():
    universe = tuple(product(range(4), repeat=4))
    counts = Counter(splice(a, b) for a in universe for b in universe)
    recipes = [{"target": list(g), "recipes": counts[g]} for g in universe]
    q = Fraction(counts[P], len(universe) ** 2)
    return {"genomes": 256, "ordered_genome_pairs_with_replacement": 65536,
            "gated_pairs": sum(counts[g] for g in universe), "all_target_counts": recipes,
            "unselected_target_genotype_reference": rate(q, 128)}


def assess():
    cases = [{"panel": "structural_calibration", "seed": seed, **measure(genesis(seed), regime)}
             for seed in SEEDS for regime in (128, 0)]
    cases.extend({"panel": "authored_fixture", "fixture": name, **measure(pool, regime)}
                 for name, pool in fixtures().items() for regime in (128, 0))
    return {"study": "closure03-adequacy-v1", "target": list(P), "excluded_target": list(T),
            "new_dynamical_worlds": 0, "independent_genesis_draws": 32, "structural_cases": 64,
            "authored_cases": 8, "reserved_seeds_executed": False,
            "probability_scope": "Independent ideal uniform draws from externally static pools; not the installed dynamics, a universal bound, or a probability for NATURAL-01.",
            "table": table_reference(), "cases": cases}


def run_assessment(output, revision):
    output = Path(output)
    if output.exists() or len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("New output and exact revision required")
    report = (encode(assess()) + "\n").encode()
    manifest = {"study": "closure03-adequacy-v1", "source_revision": revision,
                "report_sha256": hashlib.sha256(report).hexdigest(),
                "source_hashes": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}}
    output.mkdir(parents=True)
    (output / "assessment.json").write_bytes(report)
    (output / "manifest.json").write_text(encode(manifest) + "\n", encoding="utf-8", newline="\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    run_assessment(args.output_dir, args.source_revision)
