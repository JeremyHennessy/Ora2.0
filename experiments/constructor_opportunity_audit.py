"""Independent full-stream regeneration and semantic constructor opportunity audit."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
from experiments import constructor_events_audit as history

ROOT = Path(__file__).resolve().parents[1]
ARMS = ("active", "fixed", "ghost", "direct", "external_C", "external_source")
FILES = ("docs/CONSTRUCTOR-01-OPPORTUNITY-PROTOCOL.md", "data/constructor01-law-v1.json",
         "experiments/constructor_opportunity.py", "experiments/constructor_opportunity_audit.py",
         "experiments/constructor_events_audit.py")


def expected(seed, material, arm, branch=None):
    r = random.Random(seed)
    objects = {}
    for position in range(24):
        site, role = position // 3, ("A", "C", "D")[position % 3]
        if r.randint(0, 3) == 0:
            cid = f"g{site}{role}"
            objects[cid] = {"role": role, "site": site, "origin": "genesis", "producer_id": None,
                            "roots": [cid], "functional": role != "D"}
    placements = [r.choice(range(8)) for _ in range(16)]
    draws = [[r.choice(range(8)), r.choice(range(8)), r.choice(range(32)), r.choice(range(4))] for _ in range(64)]
    state = {"P": material, "W": 64, "S": [placements.count(site) for site in range(8)], "waste": 0, "heat": 0, "objects": objects}
    initial = copy.deepcopy(state)
    mode = "active" if arm == "external_C" else arm
    seen, events, ticks, chain = set(objects), [], [], history.digest(state)
    selector = {"tick": None, "event_end": None, "C_id": None, "D_id": None, "eligible": False, "reason": "no_birth"}

    def append(request):
        nonlocal state, chain
        after, result, opportunity = history.transition(state, request, mode, seen)
        event = {"seq": len(events), "request": request, "result": result, "opportunities": opportunity,
                 "before_sha256": history.digest(state), "after": after, "previous_sha256": chain}
        event["sha256"] = history.digest(event)
        chain, state = event["sha256"], after
        events.append(event)
        if result["outcome"] == "birth":
            seen.add(result["object_id"])
        return result

    for tick, draw in enumerate(draws):
        site, action, decay, slot = draw
        start = len(events)
        birth = action <= 3
        role = ("A", "C", "I", "D")[action] if birth else None
        operation = "contact" if not birth else "direct_build" if arm == "direct" else "external_build" if arm == "external_C" and role == "C" else "build"
        result = append({"action": operation, "site": site, "role": role, "new_id": f"b{tick}" if birth else None})
        if arm == "active" and selector["tick"] is None and birth and role == "C" and result["outcome"] == "birth":
            match = history.find(state, site, "D")
            eligible = match is not None and state["W"] >= 1
            selector = {"tick": tick, "event_end": len(events), "C_id": result["object_id"], "D_id": match,
                        "eligible": eligible, "reason": None if eligible else "missing_D" if match is None else "work"}
            if eligible and branch:
                append({"action": "impair", "site": site, "role": branch, "new_id": None})
        if decay == 0:
            append({"action": "decay", "site": site, "role": ("A", "C", "I", "D")[slot], "new_id": None})
        ticks.append({"tick": tick, "draws": draw, "start": start, "end": len(events)})
    return {"receipt": {"schema": "constructor01-events-v1", "case": f"seed{seed}-P{material}-{arm}-{branch or 'intact'}",
                        "mode": mode, "initial": initial, "events": events, "terminal": state}, "ticks": ticks, "selector": selector}


def verify_world(row):
    if set(row) != {"seed", "material", "arms", "branches"} or type(row["seed"]) is not int or row["seed"] not in range(96,112) or type(row["material"]) is not int or row["material"] not in (32,0) or set(row["arms"]) != set(ARMS):
        raise ValueError("World panel/schema")
    summaries = {}
    for arm in ARMS:
        value = row["arms"][arm]
        history.equal(value, expected(row["seed"], row["material"], arm), "Registered full-stream mismatch: " + arm)
        summaries[arm] = history.audit_receipt(value["receipt"])
    active = row["arms"]["active"]
    required = {"C", "D"} if active["selector"]["eligible"] else set()
    if set(row["branches"]) != required:
        raise ValueError("Missing/extra matched branch")
    for role in required:
        branch = row["branches"][role]
        history.equal(branch, expected(row["seed"], row["material"], "active", role), "Wrong selector/noise/branch order")
        summaries["cut_" + role] = history.audit_receipt(branch["receipt"])
    for key in ("initial", "events", "terminal"):
        history.equal(active["receipt"][key], row["arms"]["fixed"]["receipt"][key], "Fixed counterpart mismatch")
    return summaries


def summarize(rows):
    output = {}
    for material in (32, 0):
        group = [row for row in rows if row["material"] == material]
        counters = {}
        for arm in ARMS:
            values = [history.audit_receipt(row["arms"][arm]["receipt"]) for row in group]
            events = [event for row in group for event in row["arms"][arm]["receipt"]["events"]]
            primary = [row["arms"][arm]["receipt"]["events"][tick["start"]] for row in group for tick in row["arms"][arm]["ticks"]]
            counters[arm] = {key: sum(v[key] for v in values) for key in ("internal_C_births", "external_or_direct_births", "local_conversions", "external_conversions", "unavailable_attempts", "renewed_chain_conversions")}
            counters[arm].update(worlds_with_C_birth=sum(v["internal_C_births"] > 0 for v in values),
                                 worlds_with_renewed_use=sum(v["renewed_chain_conversions"] > 0 for v in values),
                                 distinct_renewed_interfaces=sum(len(v["renewed_chain_interface_ids"]) for v in values),
                                 funded_internal_build_proposals=sum(e["opportunities"]["funded_internal_build"] for e in primary),
                                 funded_local_contact_proposals=sum(e["request"]["action"] == "contact" and e["opportunities"]["funded_local_contact"] for e in primary),
                                 paid_births=sum(e["result"]["outcome"] == "birth" for e in events),
                                 charged_work=sum(e["result"]["charged_W"] for e in events),
                                 terminal_work_zero=sum(row["arms"][arm]["receipt"]["terminal"]["W"] == 0 for row in group),
                                 terminal_P=sum(row["arms"][arm]["receipt"]["terminal"]["P"] for row in group))
        pairs = []
        for row in group:
            if not row["branches"]:
                continue
            start = row["arms"]["active"]["selector"]["event_end"]
            pair = {"seed": row["seed"], "trigger": row["arms"]["active"]["selector"], "post_trigger_conversions": {}, "renewed_chain_uses": {}}
            for name, value in [("intact", row["arms"]["active"])] + list(row["branches"].items()):
                pair["post_trigger_conversions"][name] = sum(e["result"]["outcome"] == "convert" for e in value["receipt"]["events"][start:])
                pair["renewed_chain_uses"][name] = history.audit_receipt(value["receipt"])["renewed_chain_conversions"]
            pairs.append(pair)
        reasons = {reason: sum(row["arms"]["active"]["selector"]["reason"] == reason for row in group) for reason in ("no_birth", "missing_D", "work", None)}
        output[str(material)] = {"independent_seeds": 16, "arms": counters, "eligible_pairs": len(pairs),
                                 "trigger_reasons": {str(k): v for k,v in reasons.items()}, "pairs": pairs}
    output["admit_confirmation_proposal"] = output["32"]["arms"]["active"]["worlds_with_renewed_use"] >= 4 and output["32"]["eligible_pairs"] >= 4
    return output


def audit(input_dir, output_dir, revision):
    source, output = Path(input_dir), Path(output_dir)
    if output.exists() or len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("New output/exact source required")
    raw = (source / "worlds.jsonl").read_bytes()
    rows = [json.loads(line) for line in raw.decode().splitlines()]
    if len(rows) != 32 or {(r["seed"],r["material"]) for r in rows} != {(s,m) for s in range(96,112) for m in (32,0)}:
        raise ValueError("Missing/duplicate panel")
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    expected_manifest = {"study": "constructor01-opportunity-v1", "source_revision": revision,
                         "independent_initializations": 16, "seed_regime_records": 32, "baseline_receipts": 192,
                         "additional_branch_receipts": sum(len(r["branches"]) for r in rows),
                         "raw_sha256": hashlib.sha256(raw).hexdigest(),
                         "source_hashes": {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in FILES}}
    history.equal(manifest, expected_manifest, "Source/raw manifest mismatch")
    for row in rows:
        verify_world(row)
    result = {"source_revision": revision, "validated_records": 32, "baseline_receipts": 192,
              "additional_branches": expected_manifest["additional_branch_receipts"], "fixed_matches": 32,
              "metrics": summarize(rows), "claim": "Finite installed-law opportunity pilot; not de-novo origin, maintenance or evolution."}
    output.mkdir(parents=True)
    (output / "audit.json").write_text(history.encode(result) + "\n", encoding="utf-8", newline="\n")
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--expected-revision", required=True)
    a = p.parse_args()
    audit(a.input_dir, a.output_dir, a.expected_revision)
