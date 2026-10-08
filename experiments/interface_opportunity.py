"""Frozen finite local substrate opportunity pilot; no actor or genome."""
import argparse
import hashlib
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
FILES = ("docs/INTERFACE-01-OPPORTUNITY-PROTOCOL.md", "experiments/interface_opportunity.py",
         "experiments/interface_opportunity_audit.py")
SEEDS = tuple(range(80, 96))
ARMS = ("active", "ghost", "fixed", "no_assembly", "external_yoked")


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def setup(seed):
    rng = random.Random(seed)
    sites = [0] * 8
    for _ in range(16):
        sites[rng.randrange(8)] += 1
    draws = [[rng.randrange(8), rng.randrange(4), rng.randrange(32)] for _ in range(64)]
    return sites, draws


def simulate(seed, material, arm, schedule=()):
    if type(seed) is not int or seed not in SEEDS or type(material) is not int or material not in (32, 0) or arm not in ARMS:
        raise ValueError("Frozen development panel only")
    if arm != "external_yoked" and schedule:
        raise ValueError("Only external comparator accepts a source schedule")
    sites, draws = setup(seed)
    initial_sites = sites.copy()
    s = {"free_material": material, "work": 64, "sites": sites, "carriers": [None] * 8, "heat": 0, "waste": 0}
    events, ticks, serial = [], [], 0
    scheduled = set(tuple(x) for x in schedule)

    def emit(kind, tick, site, **details):
        total_material = s["free_material"] + 4 * sum(c is not None for c in s["carriers"]) + sum(s["sites"]) + s["waste"]
        total_potential = s["work"] + 8 * sum(s["sites"]) + s["heat"]
        if total_material != material + 16 or total_potential != 192 or min(s["free_material"], s["work"], s["heat"], s["waste"], *s["sites"]) < 0:
            raise ValueError("Invalid ledger")
        events.append({"seq": len(events), "tick": tick, "site": site, "kind": kind, **details,
                       "state": json.loads(encode(s))})

    for tick, (site, choice, decay) in enumerate(draws):
        start = len(events)
        carrier = s["carriers"][site]
        contact = choice != 0
        physical_contact = contact and carrier is not None and s["sites"][site] > 0
        opportunity = {"vacant": carrier is None,
                       "funded_build": not contact and carrier is None and s["free_material"] >= 4 and s["work"] >= 2,
                       "carrier_contact": physical_contact,
                       "funded_carrier_contact": physical_contact and s["work"] >= 2}
        if not contact:
            reason = ("disabled" if arm == "no_assembly" else "occupied" if carrier is not None else
                      "material" if s["free_material"] < 4 else "work" if s["work"] < 2 else None)
            if reason:
                emit("construct_unavailable", tick, site, reason=reason)
            else:
                s["free_material"] -= 4
                s["work"] -= 2
                s["heat"] += 2
                s["carriers"][site] = {"id": f"c{serial}", "functional": arm in ("active", "fixed"), "source": "local_proposal"}
                serial += 1
                emit("construct", tick, site, carrier_id=s["carriers"][site]["id"])
        elif s["work"] < 1:
            emit("read_unaffordable", tick, site)
        else:
            s["work"] -= 1
            s["heat"] += 1
            emit("read", tick, site)
            if s["work"] < 1:
                emit("processing_unaffordable", tick, site)
            else:
                s["work"] -= 1
                s["heat"] += 1
                emit("process", tick, site)
                functional = bool(carrier and carrier["functional"])
                allowed = {False: False, True: True}[functional] if arm == "fixed" else functional
                if arm == "external_yoked":
                    allowed = (tick, site) in scheduled
                if not s["sites"][site] or not allowed:
                    if (tick, site) in scheduled:
                        raise ValueError("Unavailable external conversion")
                    emit("conversion_unavailable", tick, site, reason="empty" if not s["sites"][site] else "no_function")
                else:
                    s["sites"][site] -= 1
                    s["waste"] += 1
                    s["work"] += 3
                    s["heat"] += 5
                    emit("convert", tick, site, source="external" if arm == "external_yoked" else "local",
                         carrier_id=carrier["id"] if carrier else None)
        if decay == 0 and s["carriers"][site] is not None:
            removed = s["carriers"][site]["id"]
            s["carriers"][site] = None
            s["waste"] += 4
            emit("decay", tick, site, carrier_id=removed)
        ticks.append({"tick": tick, "draws": [site, choice, decay], "event_start": start,
                      "event_end": len(events), "opportunities": opportunity})
    actual = {(e["tick"], e["site"]) for e in events if e["kind"] == "convert"}
    if arm == "external_yoked" and actual != scheduled:
        raise ValueError("External schedule not fully exercised")
    return {"arm": arm, "initial_sites": initial_sites,
            "initial_material": material + 16, "initial_potential": 192, "events": events,
            "ticks": ticks, "terminal": s, "source_schedule": [list(x) for x in sorted(scheduled)]}


def run_world(seed, material):
    active = simulate(seed, material, "active")
    schedule = [(e["tick"], e["site"]) for e in active["events"] if e["kind"] == "convert"]
    arms = [active] + [simulate(seed, material, arm, schedule if arm == "external_yoked" else ()) for arm in ARMS[1:]]
    return {"seed": seed, "material_regime": material, "development": True,
            "external_yoke_retrospective": True, "arms": arms}


def run_study(output, revision):
    output = Path(output)
    if output.exists() or len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("New output and exact source revision required")
    lines = [encode(run_world(seed, material)) + "\n" for seed in SEEDS for material in (32, 0)]
    raw = "".join(lines).encode()
    if any(len(line.encode()) > 1024**2 for line in lines) or len(raw) > 128 * 1024**2:
        raise ValueError("Archive bound exceeded")
    manifest = {"study": "interface01-opportunity-v1", "source_revision": revision,
                "independent_initializations": 16, "seed_regime_records": 32, "arm_receipts": 160,
                "heldout_executed": False, "raw_sha256": hashlib.sha256(raw).hexdigest(),
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
    run_study(args.output_dir, args.source_revision)
