"""Frozen finite binary-chain turnover pilot. No organism reward or service."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
LAW_PATH = ROOT / "data/turnover01-law-v1.json"
LAW = json.loads(LAW_PATH.read_text(encoding="utf-8"))
ARMS = tuple(LAW["pilot"]["arms"])
FILES = ("data/turnover01-law-v1.json", "docs/TURNOVER-01-PROTOCOL.md",
         "experiments/material_turnover.py", "experiments/material_turnover_audit.py")


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()


def genesis(seed, work):
    rng = random.Random(seed)
    state = {"W": work, "heat": 0, "atoms": {}, "objects": {}, "waste": {}, "nutrients": {}}
    for site in range(8):
        for offset in range(4):
            index = site * 4 + offset
            aid, oid = f"a{index}", f"g{index}"
            bit = str(rng.randrange(2))
            state["atoms"][aid] = {"bit": bit, "origin": "genesis_monomer", "polymer_reclaims": 0, "last_polymer_reclaim_tick": None}
            state["objects"][oid] = {"site": site, "bits": bit, "atoms": [aid], "born_tick": -1, "parents": [], "origin": "genesis"}
    for index in range(32):
        site, bit = rng.randrange(8), str(rng.randrange(2))
        aid = f"a{index + 32}"
        state["atoms"][aid] = {"bit": bit, "origin": "genesis_nutrient", "polymer_reclaims": 0, "last_polymer_reclaim_tick": None}
        state["nutrients"][f"n{index}"] = {"site": site, "atom": aid}
    draws = [[rng.randrange(8), rng.randrange(8), rng.randrange(65536), rng.randrange(65536), rng.randrange(65536)] for _ in range(128)]
    return state, draws


def balance(state):
    bits = [state["atoms"][aid]["bit"] for obj in state["objects"].values() for aid in obj["atoms"]]
    bits += [state["atoms"][aid]["bit"] for aid in state["waste"]]
    bits += [state["atoms"][n["atom"]]["bit"] for n in state["nutrients"].values()]
    bond = sum(len(o["bits"]) - 1 for o in state["objects"].values())
    return (bits.count("0"), bits.count("1"), state["W"] + state["heat"] + bond + 8 * len(state["nutrients"]))


def binding(bits, nutrient):
    return len(bits) >= 2 and bits[-1] != nutrient


class Engine:
    def __init__(self, initial, mode):
        if mode not in ARMS:
            raise ValueError("Unknown arm")
        self.s = copy.deepcopy(initial)
        self.mode = mode
        self.events = []
        self.chain = digest(initial)
        self.initial_balance = balance(initial)

    def step(self, tick, draw):
        s = self.s
        site, action, left, right, resource = draw
        before = digest(s)
        work_before = s["W"]
        pool = sorted(k for k, o in s["objects"].items() if o["site"] == site or self.mode == "shared_stock" and action in (0, 1))
        first = pool[left % len(pool)] if pool else None
        rest = [k for k in pool if k != first]
        second = rest[right % len(rest)] if rest else None
        wastes = sorted(k for k, w in s["waste"].items() if w["site"] == site)
        aid = wastes[left % len(wastes)] if wastes else None
        nutrients = sorted(k for k, n in s["nutrients"].items() if n["site"] == site)
        nid = nutrients[resource % len(nutrients)] if nutrients else None
        joined = s["objects"][first]["bits"] + s["objects"][second]["bits"] if second else ""
        match = bool(first and nid and binding(s["objects"][first]["bits"], s["atoms"][s["nutrients"][nid]["atom"]]["bit"]))
        if self.mode == "fixed" and first and nid:
            # Same fixed physical relation evaluated by a different expression.
            bits, bit = s["objects"][first]["bits"], s["atoms"][s["nutrients"][nid]["atom"]]["bit"]
            match = len(bits) > 1 and (bits[-1], bit) in (("0", "1"), ("1", "0"))
        opp = {"ligation_structural": action in (0, 1) and bool(second) and len(joined) <= 6,
               "ligation_funded": action in (0, 1) and bool(second) and len(joined) <= 6 and s["W"] >= 2,
               "reclaim_structural": action == 2 and aid is not None,
               "reclaim_funded": action == 2 and aid is not None and s["W"] >= 1,
               "contact_binding": action == 3 and match,
               "contact_funded": action == 3 and match and s["W"] >= 2,
               "direct_contact_funded": action == 3 and nid is not None and s["W"] >= 2}
        result = {"outcome": "unavailable", "reason": None, "targets": [], "product_id": None,
                  "charged_W": 0, "returned_W": 0, "heat_delta": 0, "binding_match": match if action == 3 else False,
                  "source": None, "qualifying_turnover": False, "polymer_origin_reclaim": False}

        def pay(n, heat=None):
            h = n if heat is None else heat
            s["W"] -= n
            s["heat"] += h
            result["charged_W"] += n
            result["heat_delta"] += h

        if action in (0, 1):
            result["targets"] = [x for x in (first, second) if x is not None]
            if not opp["ligation_structural"]:
                result["reason"] = "no_pair_or_length"
            elif s["W"] < 2:
                result["reason"] = "no_work"
            else:
                oid = f"b{tick}"
                obj = {"site": site, "bits": joined, "atoms": s["objects"][first]["atoms"] + s["objects"][second]["atoms"],
                       "born_tick": tick, "parents": [first, second], "origin": "ligation"}
                del s["objects"][first], s["objects"][second]
                s["objects"][oid] = obj
                pay(2, 1)
                result.update(outcome="ligated", product_id=oid)
        elif action == 2:
            result["targets"] = [] if aid is None else [aid]
            if self.mode in ("local_stock", "shared_stock"):
                result["reason"] = "reclaim_disabled"
            elif aid is None or s["W"] == 0:
                result["reason"] = "no_waste_or_work"
            else:
                pay(1)
                if self.mode == "ghost_reclaim":
                    result["outcome"] = "paid_ghost"
                else:
                    waste = s["waste"].pop(aid)
                    polymer = waste["retired_length"] >= 2
                    if polymer:
                        s["atoms"][aid]["polymer_reclaims"] += 1
                        s["atoms"][aid]["last_polymer_reclaim_tick"] = tick
                    oid = f"r{tick}"
                    s["objects"][oid] = {"site": site, "bits": s["atoms"][aid]["bit"], "atoms": [aid], "born_tick": tick,
                                         "parents": [] if waste["retired_id"] is None else [waste["retired_id"]], "origin": "reclaim"}
                    result.update(outcome="reclaimed", product_id=oid, polymer_origin_reclaim=polymer)
        elif action == 3:
            result["targets"] = [x for x in (first, nid) if x is not None]
            if s["W"] == 0:
                result["reason"] = "no_work"
            else:
                pay(1)
                result["outcome"] = "contact_partial"
                if s["W"] >= 1:
                    pay(1)
                    result["outcome"] = "contact_spent"
                    enabled = self.mode == "direct_access" or match and self.mode != "ghost_capture"
                    if enabled and nid is not None:
                        if self.mode != "direct_access":
                            obj = s["objects"][first]
                            result["qualifying_turnover"] = obj["origin"] == "ligation" and any(
                                s["atoms"][a]["polymer_reclaims"] > 0 and s["atoms"][a]["last_polymer_reclaim_tick"] < obj["born_tick"] for a in obj["atoms"])
                        atom = s["nutrients"].pop(nid)["atom"]
                        s["waste"][atom] = {"site": site, "retired_id": None, "retired_length": 0, "retired_tick": tick}
                        s["W"] += 3
                        s["heat"] += 5
                        result.update(outcome="converted", returned_W=3, source="engine_direct" if self.mode == "direct_access" else "binding")
                        result["heat_delta"] += 5
        elif action == 4:
            result["targets"] = [] if first is None else [first]
            if first is None:
                result["reason"] = "no_object"
            else:
                obj = s["objects"].pop(first)
                for atom in obj["atoms"]:
                    s["waste"][atom] = {"site": site, "retired_id": first, "retired_length": len(obj["bits"]), "retired_tick": tick}
                heat = len(obj["bits"]) - 1
                s["heat"] += heat
                result.update(outcome="decayed", heat_delta=heat)
        elif action == 5:
            result["targets"] = [] if first is None else [first]
            if first is None:
                result["reason"] = "no_object"
            else:
                s["objects"][first]["site"] = (site + (1 if right % 2 else -1)) % 8
                result["outcome"] = "moved"
        else:
            result["outcome"] = "idle"
        if balance(s) != self.initial_balance or s["W"] < 0:
            raise ValueError("Ledger violation")
        event = {"tick": tick, "draw": draw, "work_before": work_before, "opportunities": opp, "result": result, "before_sha256": before,
                 "after_sha256": digest(s), "previous_sha256": self.chain}
        event["event_sha256"] = digest(event)
        self.events.append(event)
        self.chain = event["event_sha256"]


def statistics(receipt):
    events, terminal = receipt["events"], receipt["terminal"]
    results = [e["result"] for e in events]
    qualifying = [r for r in results if r["qualifying_turnover"]]
    birth_sequences = {}
    # Birth composition is reconstructed from consumed object histories below.
    objects = {k: v["bits"] for k, v in receipt["initial"]["objects"].items()}
    for e in events:
        r = e["result"]
        if r["outcome"] == "ligated":
            bits = "".join(objects[k] for k in r["targets"])
            objects[r["product_id"]] = bits
            birth_sequences[bits] = birth_sequences.get(bits, 0) + 1
        elif r["outcome"] == "reclaimed":
            objects[r["product_id"]] = terminal["atoms"][r["targets"][0]]["bit"]
    return {"births": sum(r["outcome"] == "ligated" for r in results), "birth_sequences": birth_sequences,
            "reclaims": sum(r["outcome"] == "reclaimed" for r in results),
            "polymer_origin_reclaims": sum(r["polymer_origin_reclaim"] for r in results),
            "decays": sum(r["outcome"] == "decayed" for r in results),
            "conversions": sum(r["outcome"] == "converted" for r in results),
            "binding_conversions": sum(r["source"] == "binding" for r in results),
            "qualifying_uses": len(qualifying), "distinct_qualifying_polymers": len({r["targets"][0] for r in qualifying}),
            "charged_W": sum(r["charged_W"] for r in results), "returned_W": sum(r["returned_W"] for r in results),
            "unavailable_events": sum(r["outcome"] == "unavailable" for r in results),
            "partial_contacts": sum(r["outcome"] == "contact_partial" for r in results),
            "exhausted_events": sum(e["work_before"] == 0 for e in events),
            "opportunities": {k: sum(e["opportunities"][k] for e in events) for k in events[0]["opportunities"]},
            "terminal_W": terminal["W"], "terminal_heat": terminal["heat"],
            "terminal_bond_potential": sum(len(o["bits"]) - 1 for o in terminal["objects"].values()),
            "terminal_nutrients": len(terminal["nutrients"]), "terminal_waste_atoms": len(terminal["waste"])}


def simulate(seed, work):
    initial, draws = genesis(seed, work)
    arms = []
    for mode in ARMS:
        engine = Engine(initial, mode)
        for tick, draw in enumerate(draws):
            engine.step(tick, draw)
        receipt = {"mode": mode, "initial": initial, "events": engine.events, "terminal": engine.s}
        receipt["statistics"] = statistics(receipt)
        arms.append(receipt)
    return {"schema": "turnover01-record-v1", "seed": seed, "initial_work": work, "draws": draws, "arms": arms}


def summarize(records, revision):
    rows = {}
    for work in (96, 0):
        selected = [r for r in records if r["initial_work"] == work]
        totals = {}
        for mode in ARMS:
            stats = [next(a for a in r["arms"] if a["mode"] == mode)["statistics"] for r in selected]
            totals[mode] = {k: sum(s[k] for s in stats) for k in stats[0] if isinstance(stats[0][k], int)}
            totals[mode]["opportunity_worlds"] = sum(s["qualifying_uses"] > 0 for s in stats)
            totals[mode]["opportunities"] = {k: sum(s["opportunities"][k] for s in stats) for k in stats[0]["opportunities"]}
        paired = []
        for r in selected:
            active = next(a["statistics"] for a in r["arms"] if a["mode"] == "active")
            ghost = next(a["statistics"] for a in r["arms"] if a["mode"] == "ghost_reclaim")
            paired.append({"seed": r["seed"], "active_uses": active["qualifying_uses"],
                           "conversion_difference": active["conversions"] - ghost["conversions"],
                           "terminal_W_difference": active["terminal_W"] - ghost["terminal_W"]})
        rows[str(work)] = {"arms": totals, "active_vs_ghost_reclaim": paired}
    funded = rows["96"]
    admitted = (funded["arms"]["active"]["opportunity_worlds"] >= 4 and
                sum(p["conversion_difference"] > 0 for p in funded["active_vs_ghost_reclaim"]) >= 4 and
                sum(p["conversion_difference"] for p in funded["active_vs_ghost_reclaim"]) > 0)
    return {"schema": "turnover01-summary-v1", "source_revision": revision,
            "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in FILES},
            "independent_initializations": 16, "paired_seed_regime_records": len(records),
            "arm_histories": sum(len(r["arms"]) for r in records), "events": sum(len(a["events"]) for r in records for a in r["arms"]),
            "regimes": rows, "admission_screen_passed": admitted,
            "decision": "propose_separate_causal_protocol" if admitted else "close_negative_opportunity_pilot",
            "claim_limit": "installed-law opportunity; no self-maintenance, evolution or inheritance"}


def run(output, revision):
    if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("Exact source revision required")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    records = [simulate(seed, work) for seed in range(112, 128) for work in (96, 0)]
    raw = "".join(encode(r) + "\n" for r in records).encode()
    (output / "run-records.jsonl").write_bytes(raw)
    summary = summarize(records, revision)
    summary["records_sha256"] = hashlib.sha256(raw).hexdigest()
    (output / "summary.json").write_bytes((encode(summary) + "\n").encode())
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    run(args.output_dir, args.source_revision)
