"""Frozen finite neutral constructor encounter pilot, not an organism runtime."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
ARMS = ("active", "fixed", "ghost", "direct", "external_C", "external_source")
ROLES = ("A", "C", "I", "D")
FILES = ("docs/CONSTRUCTOR-01-OPPORTUNITY-PROTOCOL.md", "data/constructor01-law-v1.json",
         "experiments/constructor_opportunity.py", "experiments/constructor_opportunity_audit.py",
         "experiments/constructor_events_audit.py")


def encode(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"))


def digest(x):
    return hashlib.sha256(encode(x).encode()).hexdigest()


def genesis(seed, material):
    rng = random.Random(seed)
    objects = {}
    for site in range(8):
        for role in ("A", "C", "D"):
            if rng.randrange(4) == 0:
                cid = f"g{site}{role}"
                objects[cid] = {"role": role, "site": site, "origin": "genesis", "producer_id": None,
                                "roots": [cid], "functional": role != "D"}
    sites = [0] * 8
    for _ in range(16):
        sites[rng.randrange(8)] += 1
    draws = [[rng.randrange(8), rng.randrange(8), rng.randrange(32), rng.randrange(4)] for _ in range(64)]
    return {"P": material, "W": 64, "S": sites, "waste": 0, "heat": 0, "objects": objects}, draws


class Engine:
    def __init__(self, initial, mode):
        self.initial = copy.deepcopy(initial)
        self.s = copy.deepcopy(initial)
        self.mode = mode
        self.events = []
        self.chain = digest(initial)
        self.used = set(initial["objects"])
        self.balances = self.totals()

    def totals(self):
        s = self.s
        return (s["P"] + sum(s["S"]) + s["waste"] + 4 * len(s["objects"]), s["W"] + s["heat"] + 8 * sum(s["S"]))

    def find(self, site, role):
        return next((cid for cid, o in self.s["objects"].items() if o["site"] == site and o["role"] == role), None)

    def step(self, action, site, role=None, new_id=None):
        s = self.s
        request = {"action": action, "site": site, "role": role, "new_id": new_id}
        building = action in ("build", "external_build", "direct_build")
        parent_role = {"A": "C", "C": "A", "I": "C", "D": "C"}.get(role)
        producer = self.find(site, parent_role) if building else None
        if self.mode == "fixed" and building:
            # Deliberate fixed relation table counterpart; same physical law.
            pairs = {(a, b) for a, b in (("C", "A"), ("A", "C"), ("C", "I"), ("C", "D"))}
            producer = next((cid for cid, o in s["objects"].items() if o["site"] == site and (o["role"], role) in pairs), None)
        vacant = building and self.find(site, role) is None
        interface = self.find(site, "I")
        enabled = interface is not None and s["objects"][interface]["functional"]
        opp = {"vacant_product": bool(vacant), "catalyst_present": producer is not None,
               "funded_internal_build": bool(vacant and producer is not None and s["P"] >= 4 and s["W"] >= 2),
               "funded_bypass_build": bool(vacant and s["P"] >= 4 and s["W"] >= 2),
               "interface_present": interface is not None, "nutrient_present": s["S"][site] > 0,
               "funded_local_contact": bool(enabled and s["S"][site] and s["W"] >= 2),
               "funded_external_contact": bool(s["S"][site] and s["W"] >= 2)}
        before = digest(s)
        out = {"outcome": "unavailable", "reason": None, "object_id": None, "producer_id": None,
               "origin": None, "source": None, "roots": [], "charged_P": 0, "charged_W": 0,
               "read_W": 0, "process_W": 0, "retired_id": None}

        def pay(n):
            s["W"] -= n
            s["heat"] += n
            out["charged_W"] += n

        if building:
            if new_id in self.used:
                raise ValueError("ID reused")
            failure = "occupied" if not vacant else "catalyst" if action == "build" and producer is None else "material" if s["P"] < 4 else "work" if s["W"] < 2 else None
            if failure:
                out["reason"] = failure
            else:
                pay(2)
                s["P"] -= 4
                origin = "internal" if action == "build" else "external" if action == "external_build" else "engine_direct"
                parent = producer if action == "build" else None
                roots = s["objects"][parent]["roots"].copy() if parent else [new_id]
                s["objects"][new_id] = {"role": role, "site": site, "origin": origin, "producer_id": parent,
                                         "roots": roots, "functional": role in ("A", "C") or role == "I" and self.mode not in ("ghost", "external_source")}
                self.used.add(new_id)
                out.update(outcome="birth", object_id=new_id, producer_id=parent, origin=origin, roots=roots, charged_P=4)
        elif action == "contact":
            if s["W"] == 0:
                out["reason"] = "read_work"
            else:
                pay(1)
                out["read_W"] = 1
                if s["W"] == 0:
                    out["reason"] = "process_work"
                else:
                    pay(1)
                    out["process_W"] = 1
                    if not s["S"][site] or not (enabled or self.mode == "external_source"):
                        out["reason"] = "empty" if not s["S"][site] else "no_function"
                    else:
                        s["S"][site] -= 1
                        s["waste"] += 1
                        s["W"] += 3
                        s["heat"] += 5
                        out.update(outcome="convert", source="external" if self.mode == "external_source" else "local",
                                   object_id=None if self.mode == "external_source" else interface)
        elif action in ("decay", "impair"):
            cid = self.find(site, role)
            if cid is None:
                out["reason"] = "absent"
            elif action == "impair" and s["W"] == 0:
                out["reason"] = "work"
            else:
                if action == "impair":
                    pay(1)
                del s["objects"][cid]
                s["waste"] += 4
                out.update(outcome="retire", retired_id=cid)
        else:
            raise ValueError("Unknown action")
        if self.totals() != self.balances or min(s["P"], s["W"], s["heat"], s["waste"], *s["S"]) < 0:
            raise ValueError("Simulation ledger failed")
        e = {"seq": len(self.events), "request": request, "result": out, "opportunities": opp,
             "before_sha256": before, "after": copy.deepcopy(s), "previous_sha256": self.chain}
        e["sha256"] = digest(e)
        self.chain = e["sha256"]
        self.events.append(e)
        return out


def simulate(seed, material, arm, branch=None):
    initial, draws = genesis(seed, material)
    mode = "active" if arm == "external_C" else arm
    engine = Engine(initial, mode)
    ticks = []
    selector = {"tick": None, "event_end": None, "C_id": None, "D_id": None, "eligible": False, "reason": "no_birth"}
    for tick, (site, action, decay, slot) in enumerate(draws):
        start = len(engine.events)
        if action < 4:
            role = ROLES[action]
            op = "direct_build" if arm == "direct" else "external_build" if arm == "external_C" and role == "C" else "build"
            result = engine.step(op, site, role, f"b{tick}")
        else:
            result = engine.step("contact", site)
        if arm == "active" and selector["tick"] is None and result["outcome"] == "birth" and action == 1:
            match = engine.find(site, "D")
            eligible = match is not None and engine.s["W"] >= 1
            selector = {"tick": tick, "event_end": len(engine.events), "C_id": result["object_id"], "D_id": match,
                        "eligible": eligible, "reason": None if eligible else "missing_D" if match is None else "work"}
            if eligible and branch:
                engine.step("impair", site, branch)
        if decay == 0:
            engine.step("decay", site, ROLES[slot])
        ticks.append({"tick": tick, "draws": [site, action, decay, slot], "start": start, "end": len(engine.events)})
    case = f"seed{seed}-P{material}-{arm}-{branch or 'intact'}"
    return {"receipt": {"schema": "constructor01-events-v1", "case": case, "mode": mode, "initial": initial,
                        "events": engine.events, "terminal": engine.s}, "ticks": ticks, "selector": selector}


def world(seed, material):
    arms = {arm: simulate(seed, material, arm) for arm in ARMS}
    active = arms["active"]
    branches = {role: simulate(seed, material, "active", role) for role in ("C", "D")} if active["selector"]["eligible"] else {}
    return {"seed": seed, "material": material, "arms": arms, "branches": branches}


def run(output, revision):
    output = Path(output)
    if output.exists() or len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("New output and exact revision required")
    rows = [world(seed, material) for seed in range(96, 112) for material in (32, 0)]
    raw = ("".join(encode(row) + "\n" for row in rows)).encode()
    manifest = {"study": "constructor01-opportunity-v1", "source_revision": revision,
                "independent_initializations": 16, "seed_regime_records": 32, "baseline_receipts": 192,
                "additional_branch_receipts": sum(len(r["branches"]) for r in rows),
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "source_hashes": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}}
    output.mkdir(parents=True)
    (output / "worlds.jsonl").write_bytes(raw)
    (output / "manifest.json").write_text(encode(manifest) + "\n", encoding="utf-8", newline="\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    run(args.output_dir, args.source_revision)
