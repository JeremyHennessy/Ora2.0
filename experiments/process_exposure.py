"""Fresh development-only post-damage exposure diagnostic; externally scheduled coupons."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from experiments.process_pilot import setup, product, canonical
from experiments.process_restoration_audit import CONTRACT, audit

SEEDS = tuple(range(16, 24))
ROOT = Path(__file__).resolve().parents[1]
FILES = ("docs/CLOSURE-03-EXPOSURE-PROTOCOL.md", "docs/CLOSURE-03-PROTOCOL.md",
         "experiments/process_exposure.py", "experiments/process_exposure_audit.py",
         "experiments/process_pilot.py", "experiments/process_pilot_audit.py",
         "experiments/process_restoration_audit.py")


def snapshot(seed, regime):
    if type(seed) is not int or seed not in SEEDS or regime not in (128, 0):
        raise ValueError("exposure development panel only")
    initial, p, t, original_cut, _, motif, draws = setup(seed)
    live = {x["id"]: tuple(x["genome"]) for x in initial}
    resources, fuel, waste, serial = regime, 160, 0, 0
    receipt = {"contract": CONTRACT, "law": "splice-v1", "initial_tokens": initial,
               "target": list(t), "prerequisite": list(p), "precursor": regime,
               "fuel": 160, "events": []}
    ticks = []

    def append(event):
        event.update(seq=len(receipt["events"]), state={"live_ids": sorted(live),
                      "precursor": resources, "fuel": fuel, "waste": waste})
        receipt["events"].append(event)

    for tick, (u, v, w) in enumerate(draws[:32]):
        start = len(receipt["events"])
        if len(live) > 1 and fuel:
            ids = sorted(live)
            a_id = ids.pop(int(u * len(ids)))
            b_id = ids[int(v * len(ids))]
            g = product(live[a_id], live[b_id])
            fuel -= 1
            newborn = None
            if g is not None and resources >= 4:
                resources -= 4
                ident = f"n{serial}"
                serial += 1
                live[ident] = g
                newborn = {"id": ident, "genome": list(g)}
            append({"kind": "collision", "a": a_id, "b": b_id, "product": newborn})
        if w < 1 / 16 and live:
            ids = sorted(live)
            ident = ids[int(w * 16 * len(ids))]
            del live[ident]
            waste += 4
            append({"kind": "decay", "id": ident})
        ticks.append({"tick": tick, "draws": [u, v, w], "event_start": start,
                      "event_end": len(receipt["events"]), "live_ids": sorted(live)})
    removed = sorted(k for k, g in live.items() if g in (p, t))
    for ident in removed:
        del live[ident]
        waste += 4
    append({"kind": "damage", "removed_ids": removed})
    return {"seed": seed, "regime": regime, "motif": motif, "original_cut": original_cut,
            "receipt": receipt, "ticks": ticks, "live": live, "next_id": f"n{serial}",
            "result": audit(receipt)}


def select(live, prerequisite, target, original_cut, motif, state):
    pairs = [(a, b) for a in sorted(live) for b in sorted(live) if a != b]
    producers = [(a, b) for a, b in pairs if product(live[a], live[b]) == tuple(prerequisite)]
    cut = producers[0] if producers else None
    sham = None
    if cut:
        a, b = cut
        candidates = [(a, d) for d in sorted(live) if d not in (a, b)
                      and live[d][0] == live[b][0] and live[d][3] == live[b][3]
                      and product(live[a], live[d]) not in (tuple(prerequisite), tuple(target))]
        sham = candidates[0] if candidates else None
    status = ("no_motif" if not motif else "no_cut_opportunity" if cut is None else
              "no_sham_match" if sham is None else "unaffordable" if state["precursor"] < 4 or
              state["fuel"] < 1 else "ready")
    return {"status": status, "pair_count": len(pairs), "producer_pairs": len(producers),
            "original_cut_pairs": sum((live[a], live[b]) == original_cut for a, b in pairs),
            "cut": cut, "sham": sham}


def diagnose(seed, regime):
    data = snapshot(seed, regime)
    receipt, live = data["receipt"], data["live"]
    state = receipt["events"][-1]["state"]
    choice = select(live, receipt["prerequisite"], receipt["target"], data["original_cut"], data["motif"], state)
    coupons = []
    if choice["status"] == "ready":
        for probe in ("cut", "sham"):
            a, b = choice[probe]
            g = product(live[a], live[b])
            for arm in ("intact", "cut", "sham"):
                coupon = copy.deepcopy(receipt)
                ident = data["next_id"]
                after = {"live_ids": sorted([*live, ident]), "precursor": state["precursor"] - 4,
                         "fuel": state["fuel"] - 1, "waste": state["waste"]}
                coupon["events"].append({"seq": len(coupon["events"]), "kind": "collision", "a": a, "b": b,
                                         "product": {"id": ident, "genome": list(g)}, "state": after})
                if arm == probe:
                    coupon["events"].append({"seq": len(coupon["events"]), "kind": "decay", "id": ident,
                                             "state": {**after, "live_ids": sorted(live), "waste": state["waste"] + 4}})
                coupons.append({"probe": probe, "arm": arm, "externally_scheduled": True,
                                "receipt": coupon, "result": audit(coupon)})
    del data["live"]
    data["selection"], data["coupons"] = choice, coupons
    return data


def run_study(output, revision):
    output = Path(output)
    if output.exists() or len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("new output and exact source revision required")
    output.mkdir(parents=True)
    raw = "".join(canonical(diagnose(s, r)) + "\n" for s in SEEDS for r in (128, 0))
    (output / "snapshots.jsonl").write_text(raw, encoding="utf-8", newline="\n")
    manifest = {"study": "closure03-exposure-v1", "panel": "development", "seeds": list(SEEDS),
                "source_revision": revision, "snapshots": 16, "heldout_executed": False,
                "snapshots_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                "source_hashes": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}}
    (output / "manifest.json").write_text(canonical(manifest) + "\n", encoding="utf-8", newline="\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    run_study(args.output_dir, args.source_revision)
