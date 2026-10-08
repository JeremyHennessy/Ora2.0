"""NATURAL-01: development-only natural trigger with external matched removals."""
import argparse
import hashlib
from pathlib import Path

from experiments.process_pilot import setup, product, canonical
from experiments.process_restoration_audit import CONTRACT, audit

SEEDS = tuple(range(32, 48))
ROLES = ("intact", "remove_p", "remove_other")
ROOT = Path(__file__).resolve().parents[1]
FILES = ("docs/CLOSURE-03-NATURAL-PROTOCOL.md", "docs/CLOSURE-03-PROTOCOL.md",
         "experiments/process_natural.py", "experiments/process_natural_audit.py",
         "experiments/process_pilot.py", "experiments/process_pilot_audit.py",
         "experiments/process_restoration_audit.py")


def simulate(seed, regime, role="intact"):
    if type(seed) is not int or seed not in SEEDS or type(regime) is not int or regime not in (128, 0) or role not in ROLES:
        raise ValueError("natural development panel only")
    initial, p, t, _, _, motif, draws = setup(seed)
    live = {x["id"]: tuple(x["genome"]) for x in initial}
    resources, fuel, waste, serial = regime, 160, 0, 0
    receipt = {"contract": CONTRACT, "law": "splice-v1", "initial_tokens": initial,
               "target": list(t), "prerequisite": list(p), "precursor": regime,
               "fuel": fuel, "events": []}
    ticks, first = [], None
    attempts, births, removed_by_intervention = 0, 0, 0

    def record(event):
        event.update(seq=len(receipt["events"]), state={"live_ids": sorted(live),
                      "precursor": resources, "fuel": fuel, "waste": waste})
        receipt["events"].append(event)

    def decay(ident, cause):
        nonlocal waste
        del live[ident]
        waste += 4
        record({"kind": "decay", "id": ident, "cause": cause})

    for tick, (u, v, w) in enumerate(draws):
        if tick == 32:
            removed = sorted(k for k, g in live.items() if g in (p, t))
            for ident in removed:
                del live[ident]
                waste += 4
            record({"kind": "damage", "removed_ids": removed})
        start = len(receipt["events"])
        if len(live) > 1 and fuel:
            ids = sorted(live)
            a = ids.pop(int(u * len(ids)))
            b = ids[int(v * len(ids))]
            g = product(live[a], live[b])
            pre_ids = sorted(live)
            fuel -= 1
            if tick >= 32 and g == p:
                attempts += 1
            newborn = None
            if g is not None and resources >= 4:
                ident = f"n{serial}"
                serial += 1
                resources -= 4
                live[ident] = g
                newborn = {"id": ident, "genome": list(g)}
                if tick >= 32 and g == p:
                    births += 1
            record({"kind": "collision", "a": a, "b": b, "product": newborn})
            if tick >= 32 and motif and newborn and g == p and first is None:
                candidates = [k for k in pre_ids if k not in (a, b) and live[k] not in (p, t)
                              and (live[k][0], live[k][3]) == (p[0], p[3])]
                matched = candidates[0] if candidates else None
                first = {"tick": tick, "birth_event": len(receipt["events"]) - 1,
                         "newborn_id": newborn["id"], "match_id": matched, "parents": [a, b]}
                if matched and role != "intact":
                    decay(newborn["id"] if role == "remove_p" else matched, "intervention")
                    removed_by_intervention += 1
        if w < 1 / 16 and live:
            ids = sorted(live)
            decay(ids[int(w * 16 * len(ids))], "background")
        ticks.append({"tick": tick, "draws": [u, v, w], "event_start": start,
                      "event_end": len(receipt["events"]), "live_ids": sorted(live)})
    result = audit(receipt)
    exposure = ("no_motif" if not motif else "unexposed" if first is None else
                "exposed_unmatched" if first["match_id"] is None else "matched")
    return {"role": role, "motif": motif, "receipt": receipt, "ticks": ticks, "first": first,
            "exposure": exposure, "P_attempts": attempts, "P_births": births,
            "intervention_removals": removed_by_intervention, "result": result,
            "primary": motif and result["eligible"] and result["restored"],
            "terminal_counts": {"P": sum(g == p for g in live.values()), "T": sum(g == t for g in live.values())},
            "extinct": not live, "fuel_used": 160 - fuel, "material_used": regime - resources}


def run_world(seed, regime):
    baseline = simulate(seed, regime)
    branches = [baseline]
    if baseline["exposure"] == "matched":
        branches.extend(simulate(seed, regime, role) for role in ROLES[1:])
    return {"seed": seed, "regime": regime, "laboratory_counterfactuals": True, "branches": branches}


def run_study(output, revision):
    output = Path(output)
    if output.exists() or len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("new output and exact revision required")
    output.mkdir(parents=True)
    raw = "".join(canonical(run_world(s, r)) + "\n" for s in SEEDS for r in (128, 0))
    (output / "worlds.jsonl").write_text(raw, encoding="utf-8", newline="\n")
    manifest = {"study": "closure03-natural-v1", "panel": "development", "seeds": list(SEEDS),
                "source_revision": revision, "baseline_worlds": 32, "heldout_executed": False,
                "worlds_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                "source_hashes": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}}
    (output / "manifest.json").write_text(canonical(manifest) + "\n", encoding="utf-8", newline="\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    run_study(args.output_dir, args.source_revision)
