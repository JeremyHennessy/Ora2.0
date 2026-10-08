"""Independent schedule and archive auditor; imports no pilot simulator."""
from collections import Counter
import argparse
import hashlib
import json
from math import comb
from pathlib import Path
import random

from experiments.process_restoration_audit import audit

ARMS = ("constructive", "fixed_table", "cut", "sham", "inert", "external_rescue")


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def law(a, b):
    if a[0] != b[3]:
        return None
    return (a[1], b[1], a[2], b[2])


def expected_setup(seed):
    rng = random.Random(seed)
    initial = [{"id": f"g{i}", "genome": [rng.randrange(4) for _ in range(4)]} for i in range(32)]
    genes = [tuple(x["genome"]) for x in initial]
    candidates = set()
    counts = Counter(genes)
    for i, a in enumerate(genes):
        for j, b in enumerate(genes):
            if i == j:
                continue
            p = law(a, b)
            if p not in counts:
                continue
            for c in genes:
                t = law(p, c)
                if t in counts and t != p and (p != c or counts[p] > 1):
                    candidates.add((p, t, a, b, c))
    if candidates:
        p, t, a, b, _ = sorted(candidates)[0]
        cut = [list(a), list(b)]
        choices = []
        for i, left in enumerate(genes):
            for j, right in enumerate(genes):
                if i != j and left == a and right != b and right[0] == b[0] and right[3] == b[3]:
                    if law(left, right) not in (p, t):
                        choices.append((left, right))
        sham = [list(g) for g in min(choices)] if choices else None
    else:
        p, t, cut, sham = (0, 0, 0, 0), (1, 1, 1, 1), None, None
    return initial, list(p), list(t), cut, sham, bool(candidates), [
        [rng.random(), rng.random(), rng.random()] for _ in range(160)]


def verify_world(world, setup):
    initial, p, t, cut, sham, motif, draws = setup
    arm = world["arm"]
    if type(world["seed"]) is not int or type(world["regime"]) is not int:
        raise ValueError("integer panel identities required")
    receipt = world["receipt"]
    if (receipt["initial_tokens"] != initial or receipt["target"] != t or receipt["prerequisite"] != p
            or receipt["precursor"] != world["regime"] or receipt["fuel"] != 160
            or world["cut"] != cut or world["sham"] != sham or world["motif"] is not motif
            or receipt["law"] != ("fixed-graph-v1" if arm == "fixed_table" else "splice-v1")):
        raise ValueError("generator/intervention mismatch")
    result = audit(receipt)
    events, cursor = receipt["events"], 0
    live = {x["id"]: x["genome"] for x in initial}
    resources, fuel, serial = world["regime"], 160, 0
    encountered = {}
    suppressed_births = 0
    targeted_collisions = 0

    def consume(kind, **fields):
        nonlocal cursor
        if cursor >= len(events):
            raise ValueError("missing scheduled event")
        event = events[cursor]
        if event["kind"] != kind or any(event.get(k) != v for k, v in fields.items()):
            raise ValueError("schedule/control mismatch")
        cursor += 1

    def birth(g):
        nonlocal serial
        ident = f"n{serial}"
        serial += 1
        live[ident] = list(g)
        return {"id": ident, "genome": list(g)}

    if len(world["ticks"]) != 160:
        raise ValueError("incomplete tick history")
    for tick in range(160):
        u, v, w = draws[tick]
        if tick == 32:
            removed = sorted(k for k in live if live[k] in (p, t))
            consume("damage", removed_ids=removed)
            for ident in removed:
                del live[ident]
            if arm == "external_rescue" and resources >= 8 and fuel >= 2:
                for payload in (p, t):
                    resources -= 4
                    fuel -= 1
                    consume("rescue", product=birth(payload))
        start = cursor
        if len(live) > 1 and fuel > 0:
            ordered = sorted(live)
            a_id = ordered.pop(int(u * len(ordered)))
            b_id = ordered[int(v * len(ordered))]
            a, b = tuple(live[a_id]), tuple(live[b_id])
            g = law(a, b)
            if g is not None:
                encountered[(a, b)] = g
            fuel -= 1
            newborn = None
            if resources >= 4 and g is not None:
                resources -= 4
                newborn = birth(g)
            consume("collision", a=a_id, b=b_id, product=newborn)
            pair = [list(a), list(b)]
            blocked = (arm == "inert" or (tick >= 32 and
                       ((arm == "cut" and pair == cut) or (arm == "sham" and pair == sham))))
            targeted_collisions += int(blocked)
            if newborn is not None and blocked:
                suppressed_births += 1
                consume("decay", id=newborn["id"])
                del live[newborn["id"]]
        if w < 0.0625 and live:
            ids = sorted(live)
            ident = ids[int(w * 16 * len(ids))]
            consume("decay", id=ident)
            del live[ident]
        expected_tick = {"tick": tick, "draws": draws[tick], "event_start": start,
                         "event_end": cursor, "live_ids": sorted(live)}
        if type(world["ticks"][tick]["tick"]) is not int or world["ticks"][tick] != expected_tick:
            raise ValueError("tick/draw history mismatch")
    if cursor != len(events):
        raise ValueError("unscheduled events")
    if arm == "fixed_table":
        expected = [{"a": list(a), "b": list(b), "product": list(g)} for (a, b), g in sorted(encountered.items())]
        if receipt.get("rules") != expected:
            raise ValueError("incomplete fixed table")
    elif "rules" in receipt:
        raise ValueError("unexpected rule table")
    terminal = {"P": sum(g == p for g in live.values()), "T": sum(g == t for g in live.values())}
    if world["result"] != result or world["terminal_counts"] != terminal:
        raise ValueError("reported endpoint mismatch")
    result = dict(result)
    result.update(seed=world["seed"], regime=world["regime"], arm=arm,
                  motif=motif, matched=sham is not None, extinct=not live,
                  primary=motif and result["eligible"] and result["restored"],
                  material_transformed=world["regime"] - resources, fuel_used=160 - fuel,
                  suppressed_births=suppressed_births, targeted_collisions=targeted_collisions,
                  terminal_counts=terminal,
                  rescue_births=sum(e["kind"] == "rescue" for e in events))
    return result


def exact_p(left, right):
    n = left + right
    return min(1.0, 2 * sum(comb(n, i) for i in range(min(left, right) + 1)) / 2**n) if n else 1.0


def audit_study(source, output, expected_revision):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists() or source == output or source in output.parents or output in source.parents:
        raise ValueError("new separate audit output required")
    if (source / "worlds.jsonl").stat().st_size > 128 * 1024**2:
        raise ValueError("archive size bound exceeded")
    raw = (source / "worlds.jsonl").read_bytes()
    manifest = json.loads((source / "manifest.json").read_bytes())
    root = Path(__file__).resolve().parents[1]
    if (manifest.get("source_revision") != expected_revision or
        manifest.get("panel") != "development" or manifest.get("seeds") != list(range(8)) or
        manifest.get("worlds") != 96 or manifest.get("heldout_executed") is not False or
        manifest.get("study") != "closure03-pilot-v1"):
        raise ValueError("source/panel mismatch")
    hashes = {"worlds_sha256": hashlib.sha256(raw).hexdigest(),
              "protocol_sha256": hashlib.sha256((root / "docs/CLOSURE-03-PROTOCOL.md").read_bytes()).hexdigest(),
              "simulator_sha256": hashlib.sha256((root / "experiments/process_pilot.py").read_bytes()).hexdigest()}
    if any(manifest.get(k) != v for k, v in hashes.items()):
        raise ValueError("archive/source digest mismatch")
    lines = raw.splitlines()
    if len(lines) != 96 or any(len(line) > 1024**2 for line in lines):
        raise ValueError("world count/receipt bound mismatch")
    worlds = [json.loads(line) for line in lines]
    keys = [(w["seed"], w["regime"], w["arm"]) for w in worlds]
    expected_keys = [(s, r, a) for s in range(8) for r in (128, 0) for a in ARMS]
    if keys != expected_keys:
        raise ValueError("missing/duplicate/reordered panel entries")
    setups = {s: expected_setup(s) for s in range(8)}
    rows = [verify_world(w, setups[w["seed"]]) for w in worlds]
    for i in range(0, len(worlds), 6):
        if worlds[i]["receipt"]["events"] != worlds[i + 1]["receipt"]["events"]:
            raise ValueError("fixed-table equivalence failure")
    summary = {"study": "closure03-pilot-v1", "panel": "development", "source_revision": expected_revision,
               "worlds": 96, "fixed_equivalence": True, "heldout_executed": False,
               "scientific_success_claim": False, "hashes": hashes, "arms": [], "contrasts": []}
    for regime in (128, 0):
        for arm in ARMS:
            subset = [r for r in rows if r["regime"] == regime and r["arm"] == arm]
            summary["arms"].append({"regime": regime, "arm": arm, "total": len(subset),
                                     **{k: sum(r[k] for r in subset) for k in
                                        ("eligible", "motif", "matched", "primary", "extinct", "fuel_used",
                                         "suppressed_births", "targeted_collisions",
                                         "material_transformed", "rescue_births")}})
        by = {(r["seed"], r["arm"]): r for r in rows if r["regime"] == regime}
        selected = [s for s in range(8) if by[s, "constructive"]["motif"] and
                    by[s, "constructive"]["matched"] and by[s, "constructive"]["eligible"]]
        for left, right in (("constructive", "cut"), ("cut", "sham")):
            wins = sum(by[s, left]["primary"] and not by[s, right]["primary"] for s in selected)
            losses = sum(by[s, right]["primary"] and not by[s, left]["primary"] for s in selected)
            summary["contrasts"].append({"regime": regime, "left": left, "right": right,
                                         "paired_total": len(selected), "left_only": wins,
                                         "right_only": losses, "p_two_sided": exact_p(wins, losses),
                                         "unmatched_total": sum(not by[s, "constructive"]["matched"] for s in range(8))})
    output.mkdir(parents=True)
    (output / "verified-worlds.jsonl").write_text("".join(encode(r) + "\n" for r in rows), encoding="utf-8", newline="\n")
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
        parser.exit(2, f"invalid archive: {exc}\n")
