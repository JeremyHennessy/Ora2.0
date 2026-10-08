"""Finite CLOSURE-03 pilot. Only the frozen development panel is executable."""
import argparse
from collections import Counter
import hashlib
import json
from itertools import product as cartesian_product
from pathlib import Path
import random

from experiments.process_restoration_audit import CONTRACT, audit

ARMS = ("constructive", "fixed_table", "cut", "sham", "inert", "external_rescue")
REGIMES = (128, 0)
SEEDS = tuple(range(8))
ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs" / "CLOSURE-03-PROTOCOL.md"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def product(a, b):
    return (a[1], b[1], a[2], b[2]) if a[0] == b[3] else None


UNIVERSE = tuple(cartesian_product(range(4), repeat=4))
FIXED_TABLE = {(a, b): product(a, b) for a in UNIVERSE for b in UNIVERSE if a[0] == b[3]}


def setup(seed):
    rng = random.Random(seed)
    genesis = [{"id": f"g{i}", "genome": [rng.randrange(4) for _ in range(4)]} for i in range(32)]
    counts = Counter(tuple(t["genome"]) for t in genesis)
    signatures = sorted(counts)
    pairs = [(a, b, product(a, b)) for a in signatures for b in signatures
             if a != b or counts[a] >= 2]
    motifs = []
    for a, b, p in pairs:
        if p not in counts:
            continue
        for c in signatures:
            if p == c and counts[p] < 2:
                continue
            t = product(p, c)
            if t in counts and t != p:
                motifs.append((p, t, a, b, c))
    if motifs:
        p, t, a, b, c = min(motifs)
        cut = (a, b)
        candidates = [(a, d) for d in signatures if d != b and d[0] == b[0] and d[3] == b[3]
                      and (a != d or counts[a] >= 2) and product(a, d) not in (p, t)]
        sham = min(candidates) if candidates else None
    else:
        p, t, cut, sham = (0, 0, 0, 0), (1, 1, 1, 1), None, None
    draws = [[rng.random(), rng.random(), rng.random()] for _ in range(160)]
    return genesis, p, t, cut, sham, bool(motifs), draws


def run_world(seed, precursor, arm):
    if seed not in SEEDS or precursor not in REGIMES or arm not in ARMS:
        raise ValueError("development panel only")
    genesis, p, t, cut, sham, motif, draws = setup(seed)
    live = {x["id"]: tuple(x["genome"]) for x in genesis}
    fuel, waste, serial = 160, 0, 0
    receipt = {"contract": CONTRACT, "law": "fixed-graph-v1" if arm == "fixed_table" else "splice-v1",
               "target": list(t), "prerequisite": list(p), "initial_tokens": genesis,
               "precursor": precursor, "fuel": fuel, "events": []}
    rules, ticks = {}, []

    def record(event):
        event["seq"] = len(receipt["events"])
        event["state"] = {"live_ids": sorted(live), "precursor": precursor, "fuel": fuel, "waste": waste}
        receipt["events"].append(event)

    def remove(ident):
        nonlocal waste
        del live[ident]
        waste += 4
        record({"kind": "decay", "id": ident})

    def token(payload):
        nonlocal serial
        ident = f"n{serial}"
        serial += 1
        live[ident] = payload
        return {"id": ident, "genome": list(payload)}

    for tick, (u, v, w) in enumerate(draws):
        if tick == 32:
            removed = sorted(k for k, g in live.items() if g in (p, t))
            for ident in removed:
                del live[ident]
                waste += 4
            record({"kind": "damage", "removed_ids": removed})
            if arm == "external_rescue" and precursor >= 8 and fuel >= 2:
                for payload in (p, t):
                    precursor -= 4
                    fuel -= 1
                    record({"kind": "rescue", "product": token(payload)})
        start = len(receipt["events"])
        if len(live) >= 2 and fuel:
            ids = sorted(live)
            a_id = ids[int(u * len(ids))]
            ids.remove(a_id)
            b_id = ids[int(v * len(ids))]
            a, b = live[a_id], live[b_id]
            payload = FIXED_TABLE.get((a, b)) if arm == "fixed_table" else product(a, b)
            if payload is not None:
                rules[(a, b)] = payload
            fuel -= 1
            newborn = None
            if payload is not None and precursor >= 4:
                precursor -= 4
                newborn = token(payload)
            record({"kind": "collision", "a": a_id, "b": b_id, "product": newborn})
            suppressed = arm == "inert" or (tick >= 32 and
                         ((arm == "cut" and (a, b) == cut) or (arm == "sham" and (a, b) == sham)))
            if newborn and suppressed:
                remove(newborn["id"])
        if w < 1 / 16 and live:
            ids = sorted(live)
            remove(ids[int(w * 16 * len(ids))])
        ticks.append({"tick": tick, "draws": [u, v, w], "event_start": start,
                      "event_end": len(receipt["events"]), "live_ids": sorted(live)})
    if arm == "fixed_table":
        receipt["rules"] = [{"a": list(a), "b": list(b), "product": list(g)} for (a, b), g in sorted(rules.items())]
    result = audit(receipt)
    return {"seed": seed, "regime": receipt["precursor"], "arm": arm, "motif": motif,
            "cut": cut, "sham": sham, "ticks": ticks, "receipt": receipt,
            "result": result, "terminal_counts": {"P": sum(g == p for g in live.values()),
                                                      "T": sum(g == t for g in live.values())}}


def run_study(output, revision):
    output = Path(output)
    if output.exists() or len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("new output directory and exact revision required")
    output.mkdir(parents=True)
    raw = "".join(canonical(run_world(seed, regime, arm)) + "\n"
                  for seed in SEEDS for regime in REGIMES for arm in ARMS)
    (output / "worlds.jsonl").write_text(raw, encoding="utf-8", newline="\n")
    manifest = {"study": "closure03-pilot-v1", "panel": "development", "seeds": list(SEEDS),
                "source_revision": revision, "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
                "simulator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "worlds_sha256": hashlib.sha256(raw.encode()).hexdigest(), "worlds": 96,
                "heldout_executed": False}
    (output / "manifest.json").write_text(canonical(manifest) + "\n", encoding="utf-8", newline="\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    run_study(args.output_dir, args.source_revision)
