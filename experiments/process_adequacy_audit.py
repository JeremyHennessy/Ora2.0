"""Independent multiplicity/constraint audit; imports no simulator or producer."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
from itertools import product
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
FILES = ("docs/CLOSURE-03-ADEQUACY-PROTOCOL.md", "experiments/process_adequacy.py",
         "experiments/process_adequacy_audit.py")
P, T = (0, 1, 2, 3), (1, 2, 3, 0)


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def expected_rate(k, total, paid=True):
    q = Fraction(k, total) if total and paid else Fraction(0)
    def passes(draws):
        return 5 * (q.denominator - q.numerator) ** draws <= q.denominator ** draws
    minimum = None
    if q:
        low, high = 0, 1
        while not passes(high):
            high *= 2
        while high - low > 1:
            middle = (low + high) // 2
            if passes(middle):
                high = middle
            else:
                low = middle
        minimum = high
    return {"numerator": q.numerator, "denominator": q.denominator,
            "at_least_one_reference": float(1 - (1 - q) ** 128),
            "throughput_reference_pass": passes(128),
            "minimum_static_draws_for_four_fifths": minimum}


def expected_measure(initial, precursor):
    counts = Counter(tuple(x["genome"]) for x in initial if tuple(x["genome"]) not in (P, T))
    n = sum(counts.values())
    sham_total = sum(v for g, v in counts.items() if (g[0], g[3]) == (0, 3))
    recipes = matched = 0
    for a, na in counts.items():
        for b, nb in counts.items():
            if a[0] == b[3] and a[1] == 0 and b[1] == 1 and a[2] == 2 and b[2] == 3:
                count = na * (nb - int(a == b))
                recipes += count
                if sham_total - int((a[0], a[3]) == (0, 3)) - int((b[0], b[3]) == (0, 3)) > 0:
                    matched += count
    total = n * (n - 1)
    return {"initial_tokens": initial, "removed_ids": [x["id"] for x in initial if tuple(x["genome"]) in (P, T)],
            "live_tokens": n, "ordered_distinct_id_pairs": total, "recipe_pairs": recipes,
            "matched_recipe_pairs": matched, "precursor": precursor, "fuel": 128, "reference_attempts": 128,
            "recipe_rate": expected_rate(recipes, total), "matched_rate": expected_rate(matched, total),
            "paid_recipe_rate": expected_rate(recipes, total, precursor >= 4),
            "paid_matched_rate": expected_rate(matched, total, precursor >= 4)}


def expected_assessment():
    cases = []
    for seed in range(48, 80):
        rng = random.Random(seed)
        initial = [{"id": f"g{i}", "genome": [rng.randrange(4) for _ in range(4)]} for i in range(32)]
        cases.extend({"panel": "structural_calibration", "seed": seed, **expected_measure(initial, r)} for r in (128, 0))
    for name, runs in (("dense_match", (([1, 0, 2, 0], 8), ([2, 1, 3, 1], 8), ([0, 0, 0, 3], 16))),
                       ("sparse_match", (([1, 0, 2, 0], 1), ([2, 1, 3, 1], 1), ([0, 0, 0, 3], 1), ([3, 3, 3, 3], 29))),
                       ("sparse_unmatched", (([1, 0, 2, 0], 1), ([2, 1, 3, 1], 1), ([3, 3, 3, 3], 30))),
                       ("absent", (([3, 3, 3, 3], 32),))):
        genomes = [g for g, count in runs for _ in range(count)]
        initial = [{"id": f"g{i}", "genome": g} for i, g in enumerate(genomes)]
        cases.extend({"panel": "authored_fixture", "fixture": name, **expected_measure(initial, r)} for r in (128, 0))
    # Fixed target leaves a0=b3, a3 and b0 free: 4*4*4 recipes.
    counts = [{"target": list(g), "recipes": sum(1 for gate in range(4) for a3 in range(4) for b0 in range(4))}
              for g in product(range(4), repeat=4)]
    return {"study": "closure03-adequacy-v1", "target": list(P), "excluded_target": list(T),
            "new_dynamical_worlds": 0, "independent_genesis_draws": 32, "structural_cases": 64,
            "authored_cases": 8, "reserved_seeds_executed": False,
            "probability_scope": "Independent ideal uniform draws from externally static pools; not the installed dynamics, a universal bound, or a probability for NATURAL-01.",
            "table": {"genomes": 256, "ordered_genome_pairs_with_replacement": 65536,
                      "gated_pairs": sum(c["recipes"] for c in counts), "all_target_counts": counts,
                      "unselected_target_genotype_reference": expected_rate(64, 65536)}, "cases": cases}


def audit_assessment(source, output, expected_revision):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError("New audit output required")
    raw = (source / "assessment.json").read_bytes()
    if len(raw) > 4 * 1024**2:
        raise ValueError("Oversized assessment")
    expected = expected_assessment()
    if raw != (encode(expected) + "\n").encode():
        raise ValueError("Independent count/reference reconstruction differs")
    manifest = json.loads((source / "manifest.json").read_bytes())
    expected_manifest = {"study": "closure03-adequacy-v1", "source_revision": expected_revision,
                         "report_sha256": hashlib.sha256(raw).hexdigest(),
                         "source_hashes": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}}
    if len(expected_revision) != 40 or any(c not in "0123456789abcdef" for c in expected_revision) or manifest != expected_manifest:
        raise ValueError("Source/revision/manifest mismatch")
    summary = {"verified": True, "new_dynamical_worlds": 0, "source_revision": expected_revision,
               "report_sha256": expected_manifest["report_sha256"], "table": expected["table"], "panels": []}
    for panel in ("structural_calibration", "authored_fixture"):
        for regime in (128, 0):
            cases = [r for r in expected["cases"] if r["panel"] == panel and r["precursor"] == regime]
            summary["panels"].append({"panel": panel, "precursor": regime, "total": len(cases),
                "with_recipe": sum(r["recipe_pairs"] > 0 for r in cases),
                "with_matched_recipe": sum(r["matched_recipe_pairs"] > 0 for r in cases),
                "paid_throughput_reference_pass": sum(r["paid_matched_rate"]["throughput_reference_pass"] for r in cases)})
    output.mkdir(parents=True)
    (output / "audit.json").write_text(encode(summary) + "\n", encoding="utf-8", newline="\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--expected-revision", required=True)
    args = parser.parse_args()
    audit_assessment(args.input_dir, args.output_dir, args.expected_revision)
