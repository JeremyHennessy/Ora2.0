"""Post-hoc read-only opportunity census of validated NATURAL-01 histories."""
import argparse
import hashlib
import json
from pathlib import Path

from experiments.process_natural_audit import audit_study, law, encode


def census(branch):
    receipt = branch["receipt"]
    p = tuple(receipt["prerequisite"])
    live = {x["id"]: tuple(x["genome"]) for x in receipt["initial_tokens"]}
    resources, fuel = receipt["precursor"], receipt["fuel"]
    events, cursor = receipt["events"], 0
    def pairs():
        return sum(a != b and law(ga, gb) == p for a, ga in live.items() for b, gb in live.items())
    initial_pairs = pairs()
    before_damage, after_damage = None, None
    opportunity_ticks, funded_ticks, starved_ticks = 0, 0, 0
    mass = 0.0
    first_starved = None

    def apply(event):
        nonlocal resources, fuel
        if event["kind"] == "collision" and event["product"] is not None:
            token = event["product"]
            live[token["id"]] = tuple(token["genome"])
        elif event["kind"] == "decay":
            del live[event["id"]]
        elif event["kind"] == "damage":
            for ident in event["removed_ids"]:
                del live[ident]
        resources, fuel = event["state"]["precursor"], event["state"]["fuel"]

    for tick in branch["ticks"]:
        while cursor < tick["event_start"]:
            if events[cursor]["kind"] == "damage":
                before_damage = pairs()
            apply(events[cursor])
            cursor += 1
        if tick["tick"] == 32:
            after_damage = pairs()
        if tick["tick"] >= 32:
            count = pairs()
            if resources < 4 and first_starved is None:
                first_starved = tick["tick"]
            if fuel > 0 and count:
                opportunity_ticks += 1
                if resources >= 4:
                    funded_ticks += 1
                    mass += count / (len(live) * (len(live) - 1))
                else:
                    starved_ticks += 1
        while cursor < tick["event_end"]:
            apply(events[cursor])
            cursor += 1
    damage = next(e["seq"] for e in events if e["kind"] == "damage")
    return {"initial_P_pairs": initial_pairs, "pre_damage_P_pairs": before_damage,
            "post_damage_P_pairs": after_damage, "opportunity_ticks": opportunity_ticks,
            "funded_opportunity_ticks": funded_ticks, "starved_opportunity_ticks": starved_ticks,
            "funded_uniform_pair_mass": mass, "first_starved_tick": first_starved,
            "births_total": sum(e["kind"] == "collision" and e["product"] is not None for e in events),
            "births_post_damage": sum(e["seq"] > damage and e["kind"] == "collision" and e["product"] is not None for e in events)}


def diagnose(source, output, expected_revision):
    source, output = Path(source).resolve(), Path(output).resolve()
    audit_study(source, output, expected_revision)
    raw = (source / "worlds.jsonl").read_bytes()
    worlds = [json.loads(line) for line in raw.splitlines()]
    rows = [{"seed": w["seed"], "regime": w["regime"], **census(w["branches"][0])} for w in worlds]
    report = {"post_hoc_exploratory": True, "new_worlds_run": 0,
              "source_revision": expected_revision, "raw_sha256": hashlib.sha256(raw).hexdigest(),
              "analysis_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "mass_limit": "Descriptive sum of conditional uniform-pair fractions along observed histories; not an unconditional probability or significance test. 53-bit rounding ignored.",
              "regimes": []}
    for regime in (128, 0):
        subset = [r for r in rows if r["regime"] == regime]
        report["regimes"].append({"regime": regime, "total": len(subset),
            "with_post_damage_pairs": sum(r["post_damage_P_pairs"] > 0 for r in subset),
            "with_any_funded_opportunity": sum(r["funded_opportunity_ticks"] > 0 for r in subset),
            "starved_before_end": sum(r["first_starved_tick"] is not None for r in subset),
            "first_starved_ticks": [r["first_starved_tick"] for r in subset if r["first_starved_tick"] is not None],
            **{k: sum(r[k] for r in subset) for k in ("births_total", "births_post_damage",
                                                    "opportunity_ticks", "funded_opportunity_ticks",
                                                    "starved_opportunity_ticks", "funded_uniform_pair_mass")}})
    (output / "opportunity-census.jsonl").write_text("".join(encode(r) + "\n" for r in rows), encoding="utf-8", newline="\n")
    (output / "exploratory.json").write_text(encode(report) + "\n", encoding="utf-8", newline="\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--expected-revision", required=True)
    args = parser.parse_args()
    diagnose(args.input_dir, args.output_dir, args.expected_revision)
