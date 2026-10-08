"""Independent regeneration of local opportunities and retrospective source yokes."""
import argparse
import hashlib
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
FILES = ("docs/INTERFACE-01-OPPORTUNITY-PROTOCOL.md", "experiments/interface_opportunity.py",
         "experiments/interface_opportunity_audit.py")


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def initial(seed):
    randomizer = random.Random(seed)
    placements = [randomizer.randrange(8) for _ in range(16)]
    stock = [placements.count(site) for site in range(8)]
    stream = [(randomizer.randrange(8), randomizer.randrange(4), randomizer.randrange(32)) for _ in range(64)]
    return stock, stream


def expected_arm(seed, material, arm, schedule=()):
    stock, stream = initial(seed)
    s = {"free_material": material, "work": 64, "sites": stock.copy(), "carriers": [None for _ in range(8)], "heat": 0, "waste": 0}
    events, ticks, next_id = [], [], 0
    expected_source = set(schedule)

    def save(kind, tick, site, **details):
        matter = s["free_material"] + s["waste"] + sum(s["sites"]) + sum(4 for c in s["carriers"] if c is not None)
        potential = s["heat"] + s["work"] + sum(8 * n for n in s["sites"])
        if matter != material + 16 or potential != 192 or min(*s["sites"], s["work"], s["free_material"], s["waste"], s["heat"]) < 0:
            raise ValueError("Independent ledger violated")
        events.append({"seq": len(events), "tick": tick, "site": site, "kind": kind, **details, "state": json.loads(encode(s))})

    for tick, (site, action, dissolve) in enumerate(stream):
        start = len(events)
        c = s["carriers"][site]
        opportunities = {"vacant": c is None, "funded_build": action == 0 and c is None and s["free_material"] >= 4 and s["work"] >= 2,
                         "carrier_contact": action > 0 and c is not None and s["sites"][site] > 0,
                         "funded_carrier_contact": action > 0 and c is not None and s["sites"][site] > 0 and s["work"] >= 2}
        if action == 0:
            unavailable = None
            if arm == "no_assembly":
                unavailable = "disabled"
            elif c is not None:
                unavailable = "occupied"
            elif s["free_material"] < 4:
                unavailable = "material"
            elif s["work"] < 2:
                unavailable = "work"
            if unavailable:
                save("construct_unavailable", tick, site, reason=unavailable)
            else:
                cid = "c" + str(next_id)
                next_id += 1
                s["carriers"][site] = {"id": cid, "functional": arm in ("active", "fixed"), "source": "local_proposal"}
                s["free_material"] -= 4
                s["heat"] += 2
                s["work"] -= 2
                save("construct", tick, site, carrier_id=cid)
        else:
            if s["work"] == 0:
                save("read_unaffordable", tick, site)
            else:
                s["heat"] += 1
                s["work"] -= 1
                save("read", tick, site)
                if s["work"] == 0:
                    save("processing_unaffordable", tick, site)
                else:
                    s["heat"] += 1
                    s["work"] -= 1
                    save("process", tick, site)
                    enabled = c is not None and arm in ("active", "fixed")
                    if arm == "external_yoked":
                        enabled = (tick, site) in expected_source
                    if not s["sites"][site] or not enabled:
                        save("conversion_unavailable", tick, site, reason="empty" if not s["sites"][site] else "no_function")
                    else:
                        s["sites"][site] -= 1
                        s["work"] += 3
                        s["heat"] += 5
                        s["waste"] += 1
                        save("convert", tick, site, source="external" if arm == "external_yoked" else "local", carrier_id=c["id"] if c is not None else None)
        if dissolve == 0 and s["carriers"][site] is not None:
            cid = s["carriers"][site]["id"]
            s["waste"] += 4
            s["carriers"][site] = None
            save("decay", tick, site, carrier_id=cid)
        ticks.append({"tick": tick, "draws": [site, action, dissolve], "event_start": start,
                      "event_end": len(events), "opportunities": opportunities})
    return {"arm": arm, "initial_sites": stock, "initial_material": material + 16, "initial_potential": 192,
            "events": events, "ticks": ticks, "terminal": s, "source_schedule": [list(x) for x in sorted(expected_source)]}


def expected_world(seed, material):
    active = expected_arm(seed, material, "active")
    schedule = [(e["tick"], e["site"]) for e in active["events"] if e["kind"] == "convert"]
    return {"seed": seed, "material_regime": material, "development": True, "external_yoke_retrospective": True,
            "arms": [active] + [expected_arm(seed, material, arm, schedule if arm == "external_yoked" else ())
                               for arm in ("ghost", "fixed", "no_assembly", "external_yoked")]}


def normalize(receipt, yoke=False):
    result = json.loads(encode(receipt))
    result.pop("arm")
    if yoke:
        result.pop("source_schedule")
        for event in result["events"]:
            if event["kind"] == "convert":
                event.pop("source")
        for state in [result["terminal"]] + [e["state"] for e in result["events"]]:
            for carrier in state["carriers"]:
                if carrier is not None:
                    carrier["functional"] = False
    return result


def metrics(receipt):
    events, ticks, terminal = receipt["events"], receipt["ticks"], receipt["terminal"]
    return {"constructed": sum(e["kind"] == "construct" for e in events),
            "converted": sum(e["kind"] == "convert" for e in events),
            "external_converted": sum(e["kind"] == "convert" and e["source"] == "external" for e in events),
            "decayed": sum(e["kind"] == "decay" for e in events),
            "build_proposals": sum(t["draws"][1] == 0 for t in ticks),
            "contact_proposals": sum(t["draws"][1] != 0 for t in ticks),
            **{key: sum(t["opportunities"][key] for t in ticks) for key in ("vacant", "funded_build", "carrier_contact", "funded_carrier_contact")},
            "read_unaffordable": sum(e["kind"] == "read_unaffordable" for e in events),
            "processing_unaffordable": sum(e["kind"] == "processing_unaffordable" for e in events),
            "build_unavailable": {reason: sum(e["kind"] == "construct_unavailable" and e["reason"] == reason for e in events)
                                  for reason in ("disabled", "occupied", "material", "work")},
            "terminal_work": terminal["work"], "terminal_nutrient": sum(terminal["sites"]),
            "terminal_free_material": terminal["free_material"], "terminal_carriers": sum(c is not None for c in terminal["carriers"]),
            "terminal_heat": terminal["heat"], "terminal_waste": terminal["waste"]}


def audit_study(source, output, revision):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError("New audit output required")
    raw = (source / "worlds.jsonl").read_bytes()
    lines = raw.splitlines()
    if len(raw) > 128 * 1024**2 or len(lines) != 32 or any(len(line) > 1024**2 for line in lines):
        raise ValueError("Panel/archive bounds violated")
    worlds, rows = [], []
    for line, (seed, material) in zip(lines, ((s, m) for s in range(80, 96) for m in (32, 0))):
        world = expected_world(seed, material)
        if line != encode(world).encode():
            raise ValueError(f"Independent local history/opportunity reconstruction differs at {seed}/{material}")
        active, _, fixed, _, yoked = world["arms"]
        if normalize(active) != normalize(fixed) or normalize(active, True) != normalize(yoked, True):
            raise ValueError("Fixed/yoked parity failed")
        worlds.append(world)
        rows.extend({"seed": seed, "material_regime": material, "arm": r["arm"], **metrics(r)} for r in world["arms"])
    if raw != b"\n".join(lines) + b"\n":
        raise ValueError("Noncanonical archive")
    manifest = json.loads((source / "manifest.json").read_bytes())
    correct = {"study": "interface01-opportunity-v1", "source_revision": revision,
               "independent_initializations": 16, "seed_regime_records": 32, "arm_receipts": 160,
               "heldout_executed": False, "raw_sha256": hashlib.sha256(raw).hexdigest(),
               "source_hashes": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}}
    if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision) or manifest != correct:
        raise ValueError("Source/revision mismatch")
    report = {"verified": True, "source_revision": revision, "raw_sha256": correct["raw_sha256"],
              "independent_initializations": 16, "seed_regime_records": 32, "arm_receipts": 160,
              "fixed_history_matches": 32, "yoked_state_cost_matches": 32, "all_event_ledgers_conserved": True,
              "panels": [], "paired_conversion_differences": []}
    for material in (32, 0):
        for arm in ("active", "ghost", "fixed", "no_assembly", "external_yoked"):
            selected = [r for r in rows if r["material_regime"] == material and r["arm"] == arm]
            report["panels"].append({"material_regime": material, "arm": arm, "total": 16,
                "with_construction": sum(r["constructed"] > 0 for r in selected),
                "with_funded_carrier_contact": sum(r["funded_carrier_contact"] > 0 for r in selected),
                "with_conversion": sum(r["converted"] > 0 for r in selected),
                "work_exhausted_at_endpoint": sum(r["terminal_work"] == 0 for r in selected),
                **{key: sum(r[key] for r in selected) for key in ("constructed", "converted", "external_converted", "decayed",
                   "build_proposals", "contact_proposals", "funded_build", "carrier_contact", "funded_carrier_contact",
                   "read_unaffordable", "processing_unaffordable", "terminal_work", "terminal_nutrient", "terminal_free_material", "terminal_carriers")}})
        active = [r for r in rows if r["material_regime"] == material and r["arm"] == "active"]
        ghost = [r for r in rows if r["material_regime"] == material and r["arm"] == "ghost"]
        differences = [a["converted"] - g["converted"] for a, g in zip(active, ghost)]
        report["paired_conversion_differences"].append({"material_regime": material, "descriptive_only": True, "all_16_differences": differences})
    output.mkdir(parents=True)
    (output / "world-metrics.jsonl").write_text("".join(encode(r) + "\n" for r in rows), encoding="utf-8", newline="\n")
    (output / "audit.json").write_text(encode(report) + "\n", encoding="utf-8", newline="\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--expected-revision", required=True)
    args = parser.parse_args()
    audit_study(args.input_dir, args.output_dir, args.expected_revision)
