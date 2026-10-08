"""Independent exposure auditor. Imports no exposure or pilot simulator."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from experiments.process_pilot_audit import expected_setup, law
from experiments.process_restoration_audit import audit

FILES = ("docs/CLOSURE-03-EXPOSURE-PROTOCOL.md", "docs/CLOSURE-03-PROTOCOL.md",
         "experiments/process_exposure.py", "experiments/process_exposure_audit.py",
         "experiments/process_pilot.py", "experiments/process_pilot_audit.py",
         "experiments/process_restoration_audit.py")


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def verify(data):
    if type(data["seed"]) is not int or data["seed"] not in range(16, 24) or type(data["regime"]) is not int or data["regime"] not in (128, 0):
        raise ValueError("fresh diagnostic panel required")
    initial, p, t, original, _, motif, draws = expected_setup(data["seed"])
    receipt = data["receipt"]
    if (receipt["initial_tokens"] != initial or receipt["prerequisite"] != p or receipt["target"] != t or
        receipt["law"] != "splice-v1" or receipt["precursor"] != data["regime"] or receipt["fuel"] != 160 or
        data["original_cut"] != original or data["motif"] is not motif):
        raise ValueError("snapshot generator mismatch")
    result = audit(receipt)
    if data["result"] != result or len(data["ticks"]) != 32:
        raise ValueError("snapshot endpoint/tick mismatch")
    live = {x["id"]: tuple(x["genome"]) for x in initial}
    events, cursor, serial, resources, fuel = receipt["events"], 0, 0, data["regime"], 160

    def consume(kind, **fields):
        nonlocal cursor
        if cursor >= len(events) or events[cursor]["kind"] != kind or any(events[cursor].get(k) != v for k, v in fields.items()):
            raise ValueError("burn-in schedule mismatch")
        cursor += 1

    for tick in range(32):
        start = cursor
        u, v, w = draws[tick]
        if len(live) > 1 and fuel:
            ids = sorted(live)
            a = ids.pop(int(u * len(ids)))
            b = ids[int(v * len(ids))]
            g = law(live[a], live[b])
            fuel -= 1
            newborn = None
            if g is not None and resources >= 4:
                resources -= 4
                ident = f"n{serial}"
                serial += 1
                live[ident] = g
                newborn = {"id": ident, "genome": list(g)}
            consume("collision", a=a, b=b, product=newborn)
        if w < 0.0625 and live:
            ids = sorted(live)
            ident = ids[int(w * 16 * len(ids))]
            consume("decay", id=ident)
            del live[ident]
        expected_tick = {"tick": tick, "draws": draws[tick], "event_start": start,
                         "event_end": cursor, "live_ids": sorted(live)}
        if type(data["ticks"][tick]["tick"]) is not int or data["ticks"][tick] != expected_tick:
            raise ValueError("snapshot draws mismatch")
    removed = sorted(k for k, g in live.items() if list(g) in (p, t))
    consume("damage", removed_ids=removed)
    for ident in removed:
        del live[ident]
    if cursor != len(events) or data["next_id"] != f"n{serial}":
        raise ValueError("snapshot history/ID mismatch")
    pairs = [(a, b) for a in sorted(live) for b in sorted(live) if a != b]
    producers = [(a, b) for a, b in pairs if law(live[a], live[b]) == tuple(p)]
    cut = list(producers[0]) if producers else None
    sham = None
    if cut:
        a, b = cut
        matches = []
        for d in sorted(live):
            if d not in (a, b) and (live[d][0], live[d][3]) == (live[b][0], live[b][3]) and law(live[a], live[d]) not in (tuple(p), tuple(t)):
                matches.append([a, d])
        sham = matches[0] if matches else None
    state = receipt["events"][-1]["state"]
    status = ("no_motif" if not motif else "no_cut_opportunity" if cut is None else
              "no_sham_match" if sham is None else "unaffordable" if resources < 4 or fuel < 1 else "ready")
    original_tuple = tuple(tuple(g) for g in original) if original else None
    selection = {"status": status, "pair_count": len(pairs), "producer_pairs": len(producers),
                 "original_cut_pairs": sum((live[a], live[b]) == original_tuple for a, b in pairs),
                 "cut": cut, "sham": sham}
    if data["selection"] != selection:
        raise ValueError("opportunity/selector mismatch")
    coupons = data["coupons"]
    if len(coupons) != (6 if status == "ready" else 0):
        raise ValueError("coupon count mismatch")
    for index, coupon in enumerate(coupons):
        probe, arm = ("cut", "sham")[index // 3], ("intact", "cut", "sham")[index % 3]
        if coupon["probe"] != probe or coupon["arm"] != arm or coupon["externally_scheduled"] is not True:
            raise ValueError("coupon label/order mismatch")
        expected = copy.deepcopy(receipt)
        a, b = selection[probe]
        ident = f"n{serial}"
        after = {"live_ids": sorted([*live, ident]), "precursor": resources - 4,
                 "fuel": fuel - 1, "waste": state["waste"]}
        expected["events"].append({"seq": len(events), "kind": "collision", "a": a, "b": b,
                                    "product": {"id": ident, "genome": list(law(live[a], live[b]))}, "state": after})
        if arm == probe:
            expected["events"].append({"seq": len(events) + 1, "kind": "decay", "id": ident,
                                        "state": {**after, "live_ids": sorted(live), "waste": state["waste"] + 4}})
        if coupon["receipt"] != expected or coupon["result"] != audit(coupon["receipt"]):
            raise ValueError("coupon provenance/cost/control mismatch")
    return {"seed": data["seed"], "regime": data["regime"], **selection,
            "eligible": result["eligible"], "coupons": len(coupons),
            "suppressed_births": 2 if coupons else 0, "coupon_fuel_used": len(coupons),
            "coupon_material_used": 4 * len(coupons), "matched_triplet_costs": True,
            "spontaneous_repair_evidence": False}


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
    if (source / "snapshots.jsonl").stat().st_size > 128 * 1024**2:
        raise ValueError("archive bound exceeded")
    raw = (source / "snapshots.jsonl").read_bytes()
    manifest = json.loads((source / "manifest.json").read_bytes(), object_pairs_hook=unique)
    root = Path(__file__).resolve().parents[1]
    hashes = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in FILES}
    if (manifest.get("source_revision") != expected_revision or manifest.get("study") != "closure03-exposure-v1" or
        manifest.get("panel") != "development" or manifest.get("seeds") != list(range(16, 24)) or
        manifest.get("snapshots") != 16 or manifest.get("heldout_executed") is not False):
        raise ValueError("source/panel mismatch")
    if manifest.get("source_hashes") != hashes or manifest.get("snapshots_sha256") != hashlib.sha256(raw).hexdigest():
        raise ValueError("archive/source digest mismatch")
    lines = raw.splitlines()
    if len(lines) != 16 or any(len(line) > 1024**2 for line in lines):
        raise ValueError("snapshot count/bound mismatch")
    data = [json.loads(line, object_pairs_hook=unique) for line in lines]
    if [(d["seed"], d["regime"]) for d in data] != [(s, r) for s in range(16, 24) for r in (128, 0)]:
        raise ValueError("missing/duplicate/reordered snapshots")
    rows = [verify(d) for d in data]
    summary = {"study": "closure03-exposure-v1", "source_revision": expected_revision,
               "snapshots": 16, "coupons": sum(r["coupons"] for r in rows),
               "raw_sha256": manifest["snapshots_sha256"], "source_hashes": hashes,
               "heldout_executed": False, "spontaneous_repair_evidence": False,
               "matched_triplet_costs": True, "regimes": []}
    for regime in (128, 0):
        subset = [r for r in rows if r["regime"] == regime]
        summary["regimes"].append({"regime": regime, "total": 8,
            "statuses": {status: sum(r["status"] == status for r in subset) for status in
                         ("no_motif", "no_cut_opportunity", "no_sham_match", "unaffordable", "ready")},
            "snapshots_with_original_cut": sum(r["original_cut_pairs"] > 0 for r in subset),
            "snapshots_with_any_producer": sum(r["producer_pairs"] > 0 for r in subset),
            **{k: sum(r[k] for r in subset) for k in ("eligible", "coupons", "suppressed_births",
                                                     "coupon_fuel_used", "coupon_material_used")}})
    output.mkdir(parents=True)
    (output / "verified-snapshots.jsonl").write_text("".join(encode(r) + "\n" for r in rows), encoding="utf-8", newline="\n")
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
        parser.exit(2, f"invalid exposure archive: {exc}\n")
