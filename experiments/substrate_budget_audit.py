"""Independent fixture/transition reconstruction; imports no calibration engine."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ("docs/SUBSTRATE-01-BUDGET-PROTOCOL.md", "experiments/substrate_budget.py",
         "experiments/substrate_budget_audit.py")


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def expected_rows():
    fixtures = (
        ("productive", 3, 0, 8, 12, ("build", "contact", "contact", "contact"), ("contact",) * 4),
        ("material_starved", 3, 0, 0, 12, ("build", "contact", "contact"), ("contact",) * 3),
        ("work_starved", 3, 0, 8, 0, ("build", "contact"), ("contact", "foreign", "contact")),
        ("resource_starved", 0, 0, 8, 12, ("build", "contact", "contact"), ("contact",) * 3),
        ("renewal", 1, 1, 8, 12, ("build", "contact", "renew", "contact"), ("contact", "renew", "contact", "contact")),
        ("erase_rebuild", 2, 0, 8, 12, ("build", "contact", "erase", "build", "contact"), ("contact", "erase", "contact", "contact")),
        ("foreign_withdrawal", 2, 0, 8, 12, ("foreign", "contact", "withdraw", "contact"), ("foreign", "contact", "withdraw", "contact")))
    rows = []
    for name, nutrient, reserve, material, work, i_script, t_script in fixtures:
        for candidate, script in (("interface", i_script), ("trace", t_script)):
            for arm in ("active", "ghost", "fixed", "no_field") + (("external_flux",) if candidate == "interface" else ()):
                s = {"free_material": material, "work": work, "sites": [nutrient, 0],
                     "reserve": reserve, "waste": 0, "heat": 0, "carriers": [None, None]}
                events = []
                total_material, total_potential = material + nutrient + reserve, work + 8 * (nutrient + reserve)

                def emit(kind, **values):
                    count = s["reserve"] + sum(s["sites"])
                    assert s["free_material"] + count + s["waste"] + 4 * sum(x is not None for x in s["carriers"]) == total_material
                    assert s["work"] + 8 * count + s["heat"] == total_potential
                    assert all(s[key] >= 0 for key in ("free_material", "work", "reserve", "waste", "heat"))
                    events.append({"seq": len(events), "kind": kind, "site": 0, **values, "state": json.loads(encode(s))})

                def create(origin):
                    unavailable = None
                    if arm == "no_field":
                        unavailable = "disabled"
                    elif s["carriers"][0] is not None:
                        unavailable = "occupied"
                    elif s["free_material"] < 4:
                        unavailable = "material"
                    elif s["work"] < 2:
                        unavailable = "work"
                    if unavailable:
                        emit("construct_unavailable", reason=unavailable, origin=origin)
                    else:
                        s["free_material"] -= 4
                        s["work"] -= 2
                        s["heat"] += 2
                        s["carriers"][0] = {"functional": arm in ("active", "fixed"), "origin": origin}
                        emit("construct", origin=origin)

                for action in script:
                    if action in ("build", "foreign"):
                        create("external" if action == "foreign" else "internal")
                    elif action in ("renew", "withdraw"):
                        moved = int(s["reserve"] > 0) if action == "renew" else s["sites"][0]
                        sign = 1 if action == "renew" else -1
                        s["sites"][0] += sign * moved
                        s["reserve"] -= sign * moved
                        emit(action, moved=moved, source="external_intervention")
                    elif action == "erase":
                        if s["work"] == 0:
                            emit("erase_unaffordable")
                        else:
                            s["work"] -= 1
                            s["heat"] += 1
                            removed = s["carriers"][0] is not None
                            s["waste"] += 4 * removed
                            s["carriers"][0] = None
                            emit("erase", removed=removed)
                    else:
                        if s["work"] == 0:
                            emit("read_unaffordable")
                            continue
                        s["work"] -= 1
                        s["heat"] += 1
                        emit("read")
                        c = s["carriers"][0]
                        if candidate == "trace" and c is not None and c["functional"]:
                            emit("skip", accessible_nutrient=s["sites"][0])
                            continue
                        if s["work"] == 0:
                            emit("processing_unaffordable")
                            continue
                        s["work"] -= 1
                        s["heat"] += 1
                        emit("process")
                        open_source = candidate == "trace" or (c is not None and (c["functional"] or arm == "external_flux"))
                        if s["sites"][0] == 0 or not open_source:
                            emit("conversion_unavailable", reason="empty" if s["sites"][0] == 0 else "no_function")
                            continue
                        s["sites"][0] -= 1
                        s["waste"] += 1
                        s["work"] += 3
                        s["heat"] += 5
                        source = "external_flux" if arm == "external_flux" else "external_carrier" if c is not None and c["origin"] == "external" else "local"
                        emit("convert", source=source)
                        if candidate == "trace" and c is None:
                            create("internal")
                rows.append({"case": name, "candidate": candidate, "arm": arm, "authored_fixture": True,
                             "script": list(script), "initial_material": total_material,
                             "initial_potential": total_potential, "events": events, "terminal": s,
                             "material_residual": 0, "potential_residual": 0})
    return rows


def normalize(receipt, flux=False):
    copied = json.loads(encode(receipt))
    del copied["arm"]
    if flux:
        for event in copied["events"]:
            if event["kind"] == "convert":
                event.pop("source")
        for state in [copied["terminal"]] + [e["state"] for e in copied["events"]]:
            for carrier in state["carriers"]:
                if carrier:
                    carrier["functional"] = False
    return copied


def audit_calibration(source, output, revision):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError("New audit output required")
    raw = (source / "calibrations.jsonl").read_bytes()
    if len(raw) > 4 * 1024**2:
        raise ValueError("Oversized calibration")
    expected = expected_rows()
    if raw != "".join(encode(r) + "\n" for r in expected).encode():
        raise ValueError("Independent event/fixture reconstruction differs")
    manifest = json.loads((source / "manifest.json").read_bytes())
    correct = {"study": "substrate01-budget-v1", "source_revision": revision,
               "new_scientific_seed_worlds": 0, "authored_receipts": 63, "reserved_seeds_executed": False,
               "raw_sha256": hashlib.sha256(raw).hexdigest(),
               "source_hashes": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}}
    if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision) or manifest != correct:
        raise ValueError("Source/revision mismatch")
    index = {(r["case"], r["candidate"], r["arm"]): r for r in expected}
    checks = []
    for candidate in ("interface", "trace"):
        for name in dict.fromkeys(r["case"] for r in expected):
            active = index[name, candidate, "active"]
            if normalize(active) != normalize(index[name, candidate, "fixed"]):
                raise ValueError("Strongest-null divergence")
            if candidate == "interface" and normalize(active, True) != normalize(index[name, candidate, "external_flux"], True):
                raise ValueError("Authored flux/state/cost mismatch")
            checks.append({"case": name, "candidate": candidate, "fixed_history_equal": True,
                           "external_flux_state_cost_equal": True if candidate == "interface" else None})
    rows = []
    for r in expected:
        rows.append({"case": r["case"], "candidate": r["candidate"], "arm": r["arm"],
                     "conversions": sum(e["kind"] == "convert" for e in r["events"]),
                     "constructed": sum(e["kind"] == "construct" for e in r["events"]),
                     "skipped_accessible_contacts": sum(e["kind"] == "skip" and e["accessible_nutrient"] > 0 for e in r["events"]),
                     "terminal_work": r["terminal"]["work"], "terminal_free_material": r["terminal"]["free_material"],
                     "terminal_nutrient": sum(r["terminal"]["sites"]) + r["terminal"]["reserve"]})
    report = {"verified": True, "authored_receipts": 63, "new_scientific_seed_worlds": 0,
              "source_revision": revision, "raw_sha256": correct["raw_sha256"],
              "all_event_ledgers_conserved": True, "checks": checks, "cases": rows}
    output.mkdir(parents=True)
    (output / "audit.json").write_text(encode(report) + "\n", encoding="utf-8", newline="\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--expected-revision", required=True)
    args = parser.parse_args()
    audit_calibration(args.input_dir, args.output_dir, args.expected_revision)
