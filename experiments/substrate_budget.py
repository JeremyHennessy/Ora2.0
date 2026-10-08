"""Authored local-mechanism ledger calibration; no organisms or random worlds."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ("docs/SUBSTRATE-01-BUDGET-PROTOCOL.md", "experiments/substrate_budget.py",
         "experiments/substrate_budget_audit.py")
ARMS = ("active", "ghost", "fixed", "no_field")


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def cases():
    specifications = (
        ("productive", [3, 0], 0, 8, 12, ["build", "contact", "contact", "contact"], ["contact"] * 4),
        ("material_starved", [3, 0], 0, 0, 12, ["build", "contact", "contact"], ["contact"] * 3),
        ("work_starved", [3, 0], 0, 8, 0, ["build", "contact"], ["contact", "foreign", "contact"]),
        ("resource_starved", [0, 0], 0, 8, 12, ["build", "contact", "contact"], ["contact"] * 3),
        ("renewal", [1, 0], 1, 8, 12, ["build", "contact", "renew", "contact"], ["contact", "renew", "contact", "contact"]),
        ("erase_rebuild", [2, 0], 0, 8, 12, ["build", "contact", "erase", "build", "contact"], ["contact", "erase", "contact", "contact"]),
        ("foreign_withdrawal", [2, 0], 0, 8, 12, ["foreign", "contact", "withdraw", "contact"], ["foreign", "contact", "withdraw", "contact"]))
    for name, sites, reserve, material, work, interface, trace in specifications:
        yield {"name": name, "sites": sites, "reserve": reserve, "free_material": material,
               "work": work, "scripts": {"interface": interface, "trace": trace}}


class Ledger:
    def __init__(self, case, candidate, arm):
        self.candidate, self.arm = candidate, arm
        self.state = {"free_material": case["free_material"], "work": case["work"],
                      "sites": case["sites"].copy(), "reserve": case["reserve"], "waste": 0,
                      "heat": 0, "carriers": [None, None]}
        self.initial_material, self.initial_potential = self.totals()
        self.events = []

    def totals(self):
        s = self.state
        nutrient = sum(s["sites"]) + s["reserve"]
        return (s["free_material"] + 4 * sum(c is not None for c in s["carriers"]) + nutrient + s["waste"],
                s["work"] + 8 * nutrient + s["heat"])

    def record(self, kind, **details):
        if self.totals() != (self.initial_material, self.initial_potential):
            raise ValueError("Ledger conservation failed")
        if min(self.state[k] for k in ("free_material", "work", "reserve", "waste", "heat")) < 0 or min(self.state["sites"]) < 0:
            raise ValueError("Negative budget")
        self.events.append({"seq": len(self.events), "kind": kind, "site": 0, **details,
                            "state": json.loads(encode(self.state))})

    def pay(self, amount):
        if self.state["work"] < amount:
            return False
        self.state["work"] -= amount
        self.state["heat"] += amount
        return True

    def construct(self, origin):
        s = self.state
        reason = ("disabled" if self.arm == "no_field" else "occupied" if s["carriers"][0] else
                  "material" if s["free_material"] < 4 else "work" if s["work"] < 2 else None)
        if reason:
            self.record("construct_unavailable", reason=reason, origin=origin)
            return
        self.pay(2)
        s["free_material"] -= 4
        s["carriers"][0] = {"functional": self.arm in ("active", "fixed"), "origin": origin}
        self.record("construct", origin=origin)

    def contact(self):
        s = self.state
        if not self.pay(1):
            self.record("read_unaffordable")
            return
        self.record("read")
        carrier = s["carriers"][0]
        functional = bool(carrier and carrier["functional"])
        if self.arm == "fixed":
            proceed = {("trace", False): True, ("trace", True): False,
                       ("interface", False): False, ("interface", True): True}[(self.candidate, functional)]
        else:
            proceed = not functional if self.candidate == "trace" else functional
        if self.candidate == "trace" and not proceed:
            self.record("skip", accessible_nutrient=s["sites"][0])
            return
        if not self.pay(1):
            self.record("processing_unaffordable")
            return
        self.record("process")
        allowed = proceed or (self.arm == "external_flux" and carrier is not None)
        if s["sites"][0] == 0 or not allowed:
            self.record("conversion_unavailable", reason="empty" if s["sites"][0] == 0 else "no_function")
            return
        s["sites"][0] -= 1
        s["waste"] += 1
        s["work"] += 3
        s["heat"] += 5
        origin = "external_flux" if self.arm == "external_flux" else "external_carrier" if carrier and carrier["origin"] == "external" else "local"
        self.record("convert", source=origin)
        if self.candidate == "trace" and carrier is None:
            self.construct("internal")

    def step(self, action):
        s = self.state
        if action == "build":
            self.construct("internal")
        elif action == "foreign":
            self.construct("external")
        elif action == "contact":
            self.contact()
        elif action == "renew":
            moved = min(1, s["reserve"])
            s["reserve"] -= moved
            s["sites"][0] += moved
            self.record("renew", moved=moved, source="external_intervention")
        elif action == "withdraw":
            moved = s["sites"][0]
            s["sites"][0] = 0
            s["reserve"] += moved
            self.record("withdraw", moved=moved, source="external_intervention")
        elif action == "erase":
            if not self.pay(1):
                self.record("erase_unaffordable")
                return
            removed = s["carriers"][0] is not None
            if removed:
                s["carriers"][0] = None
                s["waste"] += 4
            self.record("erase", removed=removed)
        else:
            raise ValueError("Unknown authored action")


def run_case(case, candidate, arm):
    if candidate not in ("interface", "trace") or arm not in ARMS + (("external_flux",) if candidate == "interface" else ()):
        raise ValueError("Unknown calibration candidate/arm")
    ledger = Ledger(case, candidate, arm)
    for action in case["scripts"][candidate]:
        ledger.step(action)
    return {"case": case["name"], "candidate": candidate, "arm": arm, "authored_fixture": True,
            "script": case["scripts"][candidate], "initial_material": ledger.initial_material,
            "initial_potential": ledger.initial_potential, "events": ledger.events,
            "terminal": ledger.state, "material_residual": ledger.totals()[0] - ledger.initial_material,
            "potential_residual": ledger.totals()[1] - ledger.initial_potential}


def calibrate(output, revision):
    output = Path(output)
    if output.exists() or len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("New output and exact revision required")
    rows = [run_case(case, candidate, arm) for case in cases() for candidate in ("interface", "trace")
            for arm in ARMS + (("external_flux",) if candidate == "interface" else ())]
    raw = ("".join(encode(r) + "\n" for r in rows)).encode()
    manifest = {"study": "substrate01-budget-v1", "source_revision": revision,
                "new_scientific_seed_worlds": 0, "authored_receipts": 63, "reserved_seeds_executed": False,
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "source_hashes": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}}
    output.mkdir(parents=True)
    (output / "calibrations.jsonl").write_bytes(raw)
    (output / "manifest.json").write_text(encode(manifest) + "\n", encoding="utf-8", newline="\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    calibrate(args.output_dir, args.source_revision)
