"""AL03 retrospective saturation audit — read-only original archive verification.

Never edits AL03 world physics or prior recorded results. The cap analysis is
POST HOC / descriptive; see docs/AL03-MAINT-PROTOCOL.md.
"""
from __future__ import annotations

from collections import defaultdict
import argparse
import hashlib
import json
from pathlib import Path
from statistics import median

from experiments.niche_selection import VARIANTS, canonical

AL03_HASHES = {
    "worlds.jsonl": "315bf995bd78df8a9274190753ee1596c710326941f48c94fe57763f726b94dd",
    "events.jsonl": "582dbd84864aa2a2746e505f120c0c7a406897c00e4be2b339b017bf5a44688b",
    "traces.jsonl": "aab4f84f348e0e52f2d9abaa3d2854dd407ca3c12b827106d9c8e2cc38f00b69",
}


def audit(source: Path, destination: Path, *, verify_original: bool = True) -> dict:
    actual_hashes = {
        f: hashlib.sha256((source / f).read_bytes()).hexdigest()
        for f in AL03_HASHES
    }
    if verify_original and actual_hashes != AL03_HASHES:
        raise ValueError("Original AL03 archive SHA256 identity mismatch")
    with (source / "worlds.jsonl").open(encoding="utf-8") as f:
        worlds = [json.loads(row) for row in f if row.strip()]
    mapped = {(w["seed"], w["variant"]): w for w in worlds}
    if len(mapped) != len(worlds):
        raise ValueError("Duplicate original world IDs")
    if verify_original:
        expected = {(seed, variant) for seed in range(8000, 8048) for variant in VARIANTS}
        if set(mapped) != expected:
            raise ValueError("Original world seed/variant coverage changed")
    accum = defaultdict(lambda: {
        "cap_steps": 0, "observed_steps": 0,
        "first_cap": None, "last_tick": 0,
        "last_population": None,
    })
    with (source / "traces.jsonl").open(encoding="utf-8") as f:
        for text in f:
            if not text.strip():
                continue
            record = json.loads(text)
            key = (record["seed"], record["variant"])
            if key not in mapped:
                raise ValueError("Trace not associated with an archived world")
            state = accum[key]
            tick = record["tick"]
            if tick != state["last_tick"] + 1:
                raise ValueError("Noncontiguous step observations")
            if record["mass_residual"] or record["energy_residual"]:
                raise ValueError("Nonzero conservation residual in original data")
            if not 0 <= record["population"] <= 40:
                raise ValueError("Population outside declared cap")
            state["last_tick"] = tick
            state["last_population"] = record["population"]
            state["observed_steps"] += 1
            if record["population"] == 40:
                state["cap_steps"] += 1
                if state["first_cap"] is None:
                    state["first_cap"] = tick
    output_worlds = []
    for key in sorted(mapped):
        rec = mapped[key]
        state = accum.get(key)
        if not state or state["observed_steps"] != rec["steps"]:
            raise ValueError("World step count disagrees with archived traces")
        if state["last_population"] != rec["live_at_end"]:
            raise ValueError("Final population does not match last trace")
        output_worlds.append({
            "seed": key[0], "variant": key[1],
            "observed_steps": state["observed_steps"],
            "at_cap_steps": state["cap_steps"],
            "fraction_at_cap": state["cap_steps"] / state["observed_steps"],
            "first_cap_tick": state["first_cap"],
            "last_population": rec["live_at_end"],
            "extinct": rec["extinct"],
        })
    variants = {}
    for variant in VARIANTS:
        rows = [r for r in output_worlds if r["variant"] == variant]
        times = [r["first_cap_tick"] for r in rows if r["first_cap_tick"] is not None]
        variants[variant] = {
            "worlds": len(rows),
            "cap_at_end": sum(r["last_population"] == 40 for r in rows),
            "ever_at_cap": len(times),
            "fraction_time_at_cap": sum(r["at_cap_steps"] for r in rows) /
                                    sum(r["observed_steps"] for r in rows),
            "median_first_cap_tick": median(times) if times else None,
            "world_extinctions": sum(r["extinct"] for r in rows),
            "combined_observed_steps": sum(r["observed_steps"] for r in rows),
        }
    conclusion = {
        "kind": "post_hoc_saturation_reanalysis",
        "status": "recorded_descriptive_result_not_a_new_organism",
        "original_hashes_verified": verify_original and actual_hashes == AL03_HASHES,
        "source_hashes": actual_hashes,
        "source_worlds": len(worlds),
        "worlds": len(output_worlds),
        "per_variant": variants,
        "interpretation": (
            "Capped populations and scheduled resource input confound ecological persistence. "
            "This read-only analysis is post-hoc, not causal evidence or an organism."
        ),
    }
    destination.mkdir(parents=True, exist_ok=True)
    body = "".join(canonical(row) + "\n" for row in output_worlds)
    (destination / "world-cap-audit.jsonl").write_text(body, encoding="utf-8")
    conclusion["world_cap_audit_sha256"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
    (destination / "saturation-summary.json").write_text(
        json.dumps(conclusion, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return conclusion


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("runs/al03-original"))
    parser.add_argument("--output-dir", type=Path, default=Path("runs/al03-cap-audit"))
    args = parser.parse_args()
    result = audit(args.input_dir, args.output_dir)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
