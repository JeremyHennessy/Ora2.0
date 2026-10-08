"""Independent NATURAL-01 execution audit; imports no simulator."""
import argparse
import hashlib
import json
from pathlib import Path

from experiments.process_pilot_audit import expected_setup, law, exact_p
from experiments.process_restoration_audit import CONTRACT, audit

FILES = ("docs/CLOSURE-03-NATURAL-PROTOCOL.md", "docs/CLOSURE-03-PROTOCOL.md",
         "experiments/process_natural.py", "experiments/process_natural_audit.py",
         "experiments/process_pilot.py", "experiments/process_pilot_audit.py",
         "experiments/process_restoration_audit.py")


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def reference_trial(configuration, regime, role):
    initial, p, t, _, _, motif, schedule = configuration
    live = {item["id"]: list(item["genome"]) for item in initial}
    resources, remaining_fuel, waste, number = regime, 160, 0, 0
    events, ticks, trigger = [], [], None
    p_attempts, p_births, intervention_count = 0, 0, 0

    def event(kind, **fields):
        events.append({"kind": kind, **fields, "seq": len(events),
                       "state": {"live_ids": sorted(live), "precursor": resources,
                                 "fuel": remaining_fuel, "waste": waste}})

    def remove(ident, cause):
        nonlocal waste
        live.pop(ident)
        waste += 4
        event("decay", id=ident, cause=cause)

    for tick in range(160):
        if tick == 32:
            targets = sorted(ident for ident, genome in live.items() if genome == p or genome == t)
            for ident in targets:
                live.pop(ident)
                waste += 4
            event("damage", removed_ids=targets)
        first_event = len(events)
        u, v, w = schedule[tick]
        if remaining_fuel > 0 and len(live) >= 2:
            before = sorted(live)
            actor = before[int(u * len(before))]
            partners = [ident for ident in before if ident != actor]
            partner = partners[int(v * len(partners))]
            produced = law(tuple(live[actor]), tuple(live[partner]))
            remaining_fuel -= 1
            if tick >= 32 and produced == tuple(p):
                p_attempts += 1
            newborn = None
            if produced is not None and resources >= 4:
                ident = f"n{number}"
                number += 1
                resources -= 4
                live[ident] = list(produced)
                newborn = {"id": ident, "genome": list(produced)}
                if tick >= 32 and list(produced) == p:
                    p_births += 1
            event("collision", a=actor, b=partner, product=newborn)
            if tick >= 32 and motif and newborn is not None and newborn["genome"] == p and trigger is None:
                available = []
                for ident in before:
                    genome = live[ident]
                    if ident not in (actor, partner) and genome != p and genome != t and genome[0] == p[0] and genome[3] == p[3]:
                        available.append(ident)
                match = min(available) if available else None
                trigger = {"tick": tick, "birth_event": len(events) - 1,
                           "newborn_id": newborn["id"], "match_id": match, "parents": [actor, partner]}
                if match is not None and role in ("remove_p", "remove_other"):
                    remove(newborn["id"] if role == "remove_p" else match, "intervention")
                    intervention_count += 1
        if w < 0.0625 and live:
            ids = sorted(live)
            remove(ids[int(w * 16 * len(ids))], "background")
        ticks.append({"tick": tick, "draws": schedule[tick], "event_start": first_event,
                      "event_end": len(events), "live_ids": sorted(live)})
    receipt = {"contract": CONTRACT, "law": "splice-v1", "initial_tokens": initial,
               "target": t, "prerequisite": p, "precursor": regime, "fuel": 160, "events": events}
    result = audit(receipt)
    exposure = "no_motif" if not motif else "unexposed" if trigger is None else "exposed_unmatched" if trigger["match_id"] is None else "matched"
    return {"role": role, "motif": motif, "receipt": receipt, "ticks": ticks, "first": trigger,
            "exposure": exposure, "P_attempts": p_attempts, "P_births": p_births,
            "intervention_removals": intervention_count, "result": result,
            "primary": motif and result["eligible"] and result["restored"],
            "terminal_counts": {"P": sum(g == p for g in live.values()), "T": sum(g == t for g in live.values())},
            "extinct": not live, "fuel_used": 160 - remaining_fuel, "material_used": regime - resources}


def verify_world(data):
    seed, regime = data["seed"], data["regime"]
    if type(seed) is not int or seed not in range(32, 48) or type(regime) is not int or regime not in (128, 0):
        raise ValueError("natural development identities required")
    configuration = expected_setup(seed)
    baseline = reference_trial(configuration, regime, "intact")
    branches = [baseline]
    if baseline["exposure"] == "matched":
        branches.extend(reference_trial(configuration, regime, role) for role in ("remove_p", "remove_other"))
    expected = {"seed": seed, "regime": regime, "laboratory_counterfactuals": True, "branches": branches}
    if encode(data) != encode(expected):
        raise ValueError("natural schedule/trigger/match/control/endpoint mismatch")
    if len(branches) == 3:
        birth = baseline["first"]["birth_event"]
        prefix = baseline["receipt"]["events"][:birth + 1]
        for branch in branches[1:]:
            if branch["first"] != baseline["first"] or branch["receipt"]["events"][:birth + 1] != prefix:
                raise ValueError("counterfactual prefix mismatch")
        a, b = branches[1]["receipt"]["events"][birth + 1], branches[2]["receipt"]["events"][birth + 1]
        if a["cause"] != "intervention" or b["cause"] != "intervention" or a["state"]["precursor"] != b["state"]["precursor"] or a["state"]["fuel"] != b["state"]["fuel"] or a["state"]["waste"] != b["state"]["waste"]:
            raise ValueError("unequal intervention work")
    return [{"seed": seed, "regime": regime, "role": b["role"], "motif": b["motif"],
             "eligible": b["result"]["eligible"], "primary": b["primary"], "exposure": b["exposure"],
             "first": b["first"], "P_attempts": b["P_attempts"], "P_births": b["P_births"],
             "extinct": b["extinct"], "fuel_used": b["fuel_used"], "material_used": b["material_used"],
             "terminal_counts": b["terminal_counts"], "intervention_removals": b["intervention_removals"]} for b in branches]


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def audit_study(source, output, expected_revision):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists() or source == output or source in output.parents or output in source.parents:
        raise ValueError("new separate audit directory required")
    if (source / "worlds.jsonl").stat().st_size > 128 * 1024**2:
        raise ValueError("archive bound exceeded")
    raw = (source / "worlds.jsonl").read_bytes()
    manifest = json.loads((source / "manifest.json").read_bytes(), object_pairs_hook=unique)
    root = Path(__file__).resolve().parents[1]
    hashes = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in FILES}
    if (manifest.get("source_revision") != expected_revision or manifest.get("study") != "closure03-natural-v1" or
        manifest.get("panel") != "development" or manifest.get("seeds") != list(range(32, 48)) or
        manifest.get("baseline_worlds") != 32 or manifest.get("heldout_executed") is not False):
        raise ValueError("source/panel mismatch")
    if manifest.get("source_hashes") != hashes or manifest.get("worlds_sha256") != hashlib.sha256(raw).hexdigest():
        raise ValueError("archive/source digest mismatch")
    lines = raw.splitlines()
    if len(lines) != 32 or any(len(line) > 1024**2 for line in lines):
        raise ValueError("world count/bound mismatch")
    data = [json.loads(line, object_pairs_hook=unique) for line in lines]
    if [(d["seed"], d["regime"]) for d in data] != [(s, r) for s in range(32, 48) for r in (128, 0)]:
        raise ValueError("missing/duplicate/reordered panel")
    rows = [row for d in data for row in verify_world(d)]
    summary = {"study": "closure03-natural-v1", "source_revision": expected_revision,
               "baseline_worlds": 32, "continuations": len(rows), "independent_seeds": 16,
               "raw_sha256": manifest["worlds_sha256"], "source_hashes": hashes,
               "heldout_executed": False, "regimes": [], "organismhood_evidence": False}
    for regime in (128, 0):
        baseline = [r for r in rows if r["regime"] == regime and r["role"] == "intact"]
        selected = [r["seed"] for r in baseline if r["exposure"] == "matched" and r["eligible"] and r["motif"]]
        by = {(r["seed"], r["role"]): r for r in rows if r["regime"] == regime}
        left_only = sum(by[s, "remove_p"]["primary"] and not by[s, "remove_other"]["primary"] for s in selected)
        right_only = sum(by[s, "remove_other"]["primary"] and not by[s, "remove_p"]["primary"] for s in selected)
        summary["regimes"].append({"regime": regime, "baseline_total": 16,
            "eligible": sum(r["eligible"] for r in baseline), "baseline_restored": sum(r["primary"] for r in baseline),
            "exposure_counts": {status: sum(r["exposure"] == status for r in baseline) for status in
                                ("no_motif", "unexposed", "exposed_unmatched", "matched")},
            "P_attempts": sum(r["P_attempts"] for r in baseline), "P_births": sum(r["P_births"] for r in baseline),
            "baseline_extinct": sum(r["extinct"] for r in baseline),
            "first_birth_ticks": [r["first"]["tick"] for r in baseline if r["first"] is not None],
            "paired_eligible": len(selected), "remove_p_restored": sum(by[s, "remove_p"]["primary"] for s in selected),
            "remove_other_restored": sum(by[s, "remove_other"]["primary"] for s in selected),
            "remove_p_only": left_only, "remove_other_only": right_only,
            "p_two_sided": exact_p(left_only, right_only),
            "branch_totals": [{"role": role, "available": len(subset),
                               **{k: sum(r[k] for r in subset) for k in ("fuel_used", "material_used", "intervention_removals", "extinct")}}
                              for role in ("intact", "remove_p", "remove_other")
                              for subset in [[r for r in rows if r["regime"] == regime and r["role"] == role]]]})
    output.mkdir(parents=True)
    (output / "verified-branches.jsonl").write_text("".join(encode(r) + "\n" for r in rows), encoding="utf-8", newline="\n")
    (output / "audit.json").write_text(encode(summary) + "\n", encoding="utf-8", newline="\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--expected-revision", required=True)
    args = parser.parse_args()
    try:
        audit_study(args.input_dir, args.output_dir, args.expected_revision)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(2, f"invalid natural archive: {exc}\n")
