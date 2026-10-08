"""Authored measurement fixtures only; never a natural opportunity simulator."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ("data/constructor01-law-v1.json", "docs/CONSTRUCTOR-01-MEASUREMENT-CONTRACT.md",
         "experiments/constructor_events_audit.py", "experiments/constructor_event_fixtures.py")


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def sha(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()


def make_object(role, site, origin, producer, roots, mode):
    return {"role": role, "site": site, "origin": origin, "producer_id": producer,
            "roots": roots.copy(), "functional": role in ("A", "C") or role == "I" and mode not in ("ghost", "external_source")}


class Authored:
    def __init__(self, name, mode="active", seeds=(("A0", "A", 0),), material=16, work=10, stock=(1,)):
        self.name, self.mode = name, mode
        self.state = {"P": material, "W": work, "S": list(stock), "waste": 0, "heat": 0,
                      "objects": {cid: make_object(role, site, "genesis", None, [cid], mode) for cid, role, site in seeds}}
        self.initial = copy.deepcopy(self.state)
        self.events = []
        self.chain = sha(self.initial)

    def locate(self, role, site):
        return next((cid for cid, obj in self.state["objects"].items() if obj["role"] == role and obj["site"] == site), None)

    def step(self, action, role=None, cid=None, site=0):
        s = self.state
        before = sha(s)
        request = {"action": action, "role": role, "new_id": cid, "site": site}
        birth = action in ("build", "external_build", "direct_build")
        parent_role = {"A": "C", "C": "A", "I": "C", "D": "C"}.get(role)
        producer = self.locate(parent_role, site) if birth else None
        empty = birth and self.locate(role, site) is None
        i_id = self.locate("I", site)
        func = i_id is not None and s["objects"][i_id]["functional"]
        opportunity = {"vacant_product": bool(empty), "catalyst_present": producer is not None,
                       "funded_internal_build": bool(empty and producer is not None and s["P"] >= 4 and s["W"] >= 2),
                       "funded_bypass_build": bool(empty and s["P"] >= 4 and s["W"] >= 2),
                       "interface_present": i_id is not None, "nutrient_present": s["S"][site] > 0,
                       "funded_local_contact": bool(func and s["S"][site] and s["W"] >= 2),
                       "funded_external_contact": bool(s["S"][site] and s["W"] >= 2)}
        result = {"outcome": "unavailable", "reason": None, "object_id": None, "producer_id": None,
                  "origin": None, "source": None, "roots": [], "charged_P": 0, "charged_W": 0,
                  "read_W": 0, "process_W": 0, "retired_id": None}

        def charge(amount):
            s["W"] -= amount
            s["heat"] += amount
            result["charged_W"] += amount

        if birth:
            reason = "occupied" if not empty else "catalyst" if action == "build" and producer is None else "material" if s["P"] < 4 else "work" if s["W"] < 2 else None
            if reason:
                result["reason"] = reason
            else:
                charge(2)
                s["P"] -= 4
                if action == "build":
                    origin, roots, parent = "internal", s["objects"][producer]["roots"].copy(), producer
                else:
                    origin, roots, parent = ("external" if action == "external_build" else "engine_direct"), [cid], None
                s["objects"][cid] = make_object(role, site, origin, parent, roots, self.mode)
                result.update(outcome="birth", object_id=cid, producer_id=parent, origin=origin, roots=roots, charged_P=4)
        elif action == "contact":
            if s["W"] < 1:
                result["reason"] = "read_work"
            else:
                charge(1)
                result["read_W"] = 1
                if s["W"] < 1:
                    result["reason"] = "process_work"
                else:
                    charge(1)
                    result["process_W"] = 1
                    if not s["S"][site]:
                        result["reason"] = "empty"
                    elif not func and self.mode != "external_source":
                        result["reason"] = "no_function"
                    else:
                        s["S"][site] -= 1
                        s["waste"] += 1
                        s["W"] += 3
                        s["heat"] += 5
                        result.update(outcome="convert", source="external" if self.mode == "external_source" else "local",
                                      object_id=None if self.mode == "external_source" else i_id)
        elif action in ("decay", "impair"):
            target = self.locate(role, site)
            if target is None:
                result["reason"] = "absent"
            elif action == "impair" and s["W"] < 1:
                result["reason"] = "work"
            else:
                if action == "impair":
                    charge(1)
                del s["objects"][target]
                s["waste"] += 4
                result.update(outcome="retire", retired_id=target)
        else:
            raise ValueError("Unknown authored request")
        matter = s["P"] + s["waste"] + sum(s["S"]) + 4 * len(s["objects"])
        energy = s["W"] + s["heat"] + 8 * sum(s["S"])
        initial_matter = self.initial["P"] + sum(self.initial["S"]) + 4 * len(self.initial["objects"])
        if matter != initial_matter or energy != self.initial["W"] + 8 * sum(self.initial["S"]):
            raise ValueError("Fixture ledger failed")
        event = {"seq": len(self.events), "request": request, "result": result, "opportunities": opportunity,
                 "before_sha256": before, "after": copy.deepcopy(s), "previous_sha256": self.chain}
        event["sha256"] = sha(event)
        self.chain = event["sha256"]
        self.events.append(event)

    def receipt(self):
        return {"schema": "constructor01-events-v1", "case": self.name, "mode": self.mode,
                "initial": self.initial, "events": self.events, "terminal": copy.deepcopy(self.state)}


def renewed(name, mode="active", rescue=False):
    f = Authored(name, mode)
    for action, role, cid in (("build", "C", "C1"), ("decay", "A", None),
                              ("build", "A", "A2"), ("decay", "C", None),
                              ("external_build" if rescue else "build", "C", "C3"),
                              ("build", "I", "I4"), ("contact", None, None)):
        f.step(action, role, cid)
    return f.receipt()


def fixtures():
    rows = [Authored("passive").receipt()]
    f = Authored("supplied_I", seeds=(("I0", "I", 0),), material=0, work=2)
    f.step("contact")
    rows.append(f.receipt())
    f = Authored("one_C", material=8, work=6)
    f.step("build", "C", "C1")
    f.step("build", "I", "I2")
    f.step("contact")
    rows.extend([f.receipt(), renewed("renewed")])
    f = Authored("supplied_C", seeds=(("C0", "C", 0),), material=4, work=4)
    f.step("build", "I", "I1")
    f.step("contact")
    rows.extend([f.receipt(), renewed("external_rescue", rescue=True)])
    f = Authored("direct", "direct", seeds=(), material=8, work=6)
    f.step("direct_build", "C", "C1")
    f.step("direct_build", "I", "I2")
    f.step("contact")
    rows.extend([f.receipt(), renewed("ghost_renewed", "ghost"), renewed("fixed_renewed", "fixed"), renewed("external_source", "external_source")])
    for name, material, work in (("P0", 0, 10), ("work4", 8, 4)):
        f = Authored(name, material=material, work=work)
        f.step("build", "C", "C1")
        f.step("build", "I", "I2")
        f.step("contact")
        rows.append(f.receipt())
    f = Authored("work1", seeds=(("I0", "I", 0),), material=0, work=1)
    f.step("contact")
    rows.append(f.receipt())
    for target in ("C", "D"):
        f = Authored("impair_" + target, seeds=(("A0", "A", 0), ("C0", "C", 0), ("D0", "D", 0)), material=8, work=4)
        f.step("impair", target)
        f.step("build", "I", "I1")
        f.step("contact")
        rows.append(f.receipt())
    f = Authored("cross_site", stock=(1, 1), material=8, work=6)
    f.step("build", "C", "C1")
    f.step("build", "I", "I2", site=1)
    f.step("contact", site=1)
    rows.append(f.receipt())
    return rows


def write(output, revision):
    output = Path(output)
    if output.exists() or len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("New output and exact source required")
    rows = fixtures()
    raw = ("".join(encode(r) + "\n" for r in rows)).encode()
    manifest = {"study": "constructor01-authored-measure-v1", "source_revision": revision,
                "raw_sha256": hashlib.sha256(raw).hexdigest(), "authored_receipts": len(rows),
                "new_scientific_initializations": 0,
                "source_hashes": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}}
    output.mkdir(parents=True)
    (output / "receipts.jsonl").write_bytes(raw)
    (output / "manifest.json").write_text(encode(manifest) + "\n", encoding="utf-8", newline="\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    write(args.output_dir, args.source_revision)
