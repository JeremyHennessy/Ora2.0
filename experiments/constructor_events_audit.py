"""Independent semantic audit of paid constructor component histories."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ("data/constructor01-law-v1.json", "docs/CONSTRUCTOR-01-MEASUREMENT-CONTRACT.md",
         "experiments/constructor_events_audit.py", "experiments/constructor_event_fixtures.py")
DEPENDENCIES = {"A": "C", "C": "A", "I": "C", "D": "C"}
MODES = ("active", "fixed", "ghost", "direct", "external_source")


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()


def equal(a, b, message):
    if encode(a) != encode(b):
        raise ValueError(message)


def validate_state(state, mode, genesis=False):
    if set(state) != {"P", "W", "S", "waste", "heat", "objects"}:
        raise ValueError("State schema")
    if not isinstance(state["S"], list) or not 1 <= len(state["S"]) <= 8:
        raise ValueError("Site schema")
    for number in [state[k] for k in ("P", "W", "waste", "heat")] + state["S"]:
        if type(number) is not int or number < 0:
            raise ValueError("Negative/noninteger state")
    if not isinstance(state["objects"], dict):
        raise ValueError("Object map")
    slots = set()
    for cid, obj in state["objects"].items():
        if not isinstance(cid, str) or not cid or set(obj) != {"role", "site", "origin", "producer_id", "roots", "functional"}:
            raise ValueError("Object schema")
        if obj["role"] not in DEPENDENCIES or type(obj["site"]) is not int or not 0 <= obj["site"] < len(state["S"]):
            raise ValueError("Role/site")
        slot = (obj["site"], obj["role"])
        if slot in slots:
            raise ValueError("Occupied slot duplicated")
        slots.add(slot)
        function = obj["role"] in ("A", "C") or obj["role"] == "I" and mode not in ("ghost", "external_source")
        if type(obj["functional"]) is not bool or obj["functional"] != function:
            raise ValueError("Mode/function mismatch")
        if not isinstance(obj["roots"], list) or not obj["roots"] or any(not isinstance(x, str) or not x for x in obj["roots"]) or obj["roots"] != sorted(set(obj["roots"])):
            raise ValueError("Invalid roots")
        if genesis and (obj["origin"] != "genesis" or obj["producer_id"] is not None or obj["roots"] != [cid]):
            raise ValueError("Invented genesis ancestry")


def totals(state):
    return (state["P"] + sum(state["S"]) + state["waste"] + 4 * len(state["objects"]),
            state["W"] + 8 * sum(state["S"]) + state["heat"])


def find(state, site, role):
    return next((cid for cid, obj in state["objects"].items() if obj["site"] == site and obj["role"] == role), None)


def opportunities(state, request):
    site, role = request["site"], request["role"]
    building = request["action"] in ("build", "external_build", "direct_build")
    vacant = building and find(state, site, role) is None
    catalyst = building and find(state, site, DEPENDENCIES[role]) is not None
    interface = find(state, site, "I")
    enabled = interface is not None and state["objects"][interface]["functional"]
    return {"vacant_product": bool(vacant), "catalyst_present": bool(catalyst),
            "funded_internal_build": bool(vacant and catalyst and state["P"] >= 4 and state["W"] >= 2),
            "funded_bypass_build": bool(vacant and state["P"] >= 4 and state["W"] >= 2),
            "interface_present": interface is not None, "nutrient_present": state["S"][site] > 0,
            "funded_local_contact": bool(enabled and state["S"][site] and state["W"] >= 2),
            "funded_external_contact": bool(state["S"][site] and state["W"] >= 2)}


def transition(state, request, mode, seen):
    if set(request) != {"action", "site", "role", "new_id"}:
        raise ValueError("Request schema")
    action, site, role, cid = (request[k] for k in ("action", "site", "role", "new_id"))
    if type(site) is not int or not 0 <= site < len(state["S"]):
        raise ValueError("Request site")
    building = action in ("build", "external_build", "direct_build")
    if action not in ("build", "external_build", "direct_build", "contact", "decay", "impair"):
        raise ValueError("Unknown action")
    if action == "contact":
        if role is not None or cid is not None:
            raise ValueError("Contact identity")
    elif role not in DEPENDENCIES:
        raise ValueError("Request role")
    if building:
        if not isinstance(cid, str) or not cid or cid in seen:
            raise ValueError("Reused/invalid birth ID")
    elif cid is not None:
        raise ValueError("Unexpected birth ID")
    if action == "direct_build" and mode != "direct":
        raise ValueError("Unregistered direct construction")
    available = opportunities(state, request)
    after = copy.deepcopy(state)
    result = {"outcome": "unavailable", "reason": None, "object_id": None,
              "producer_id": None, "origin": None, "source": None, "roots": [],
              "charged_P": 0, "charged_W": 0, "read_W": 0, "process_W": 0, "retired_id": None}

    def pay(amount):
        after["W"] -= amount
        after["heat"] += amount
        result["charged_W"] += amount

    if building:
        producer = find(state, site, DEPENDENCIES[role]) if action == "build" else None
        reason = ("occupied" if not available["vacant_product"] else "catalyst" if action == "build" and producer is None else
                  "material" if state["P"] < 4 else "work" if state["W"] < 2 else None)
        if reason:
            result["reason"] = reason
        else:
            pay(2)
            after["P"] -= 4
            origin = "internal" if action == "build" else "external" if action == "external_build" else "engine_direct"
            roots = state["objects"][producer]["roots"].copy() if producer else [cid]
            functional = role in ("A", "C") or role == "I" and mode not in ("ghost", "external_source")
            after["objects"][cid] = {"role": role, "site": site, "origin": origin, "producer_id": producer, "roots": roots, "functional": functional}
            result.update(outcome="birth", object_id=cid, producer_id=producer, origin=origin, roots=roots, charged_P=4)
    elif action == "contact":
        if after["W"] == 0:
            result["reason"] = "read_work"
        else:
            pay(1)
            result["read_W"] = 1
            if after["W"] == 0:
                result["reason"] = "process_work"
            else:
                pay(1)
                result["process_W"] = 1
                interface = find(state, site, "I")
                external = mode == "external_source"
                enabled = external or interface is not None and state["objects"][interface]["functional"]
                if not after["S"][site] or not enabled:
                    result["reason"] = "empty" if not after["S"][site] else "no_function"
                else:
                    after["S"][site] -= 1
                    after["waste"] += 1
                    after["W"] += 3
                    after["heat"] += 5
                    result.update(outcome="convert", source="external" if external else "local", object_id=None if external else interface)
    else:
        target = find(state, site, role)
        reason = "absent" if target is None else "work" if action == "impair" and state["W"] == 0 else None
        if reason:
            result["reason"] = reason
        else:
            if action == "impair":
                pay(1)
            del after["objects"][target]
            after["waste"] += 4
            result.update(outcome="retire", retired_id=target)
    validate_state(after, mode)
    if totals(after) != totals(state):
        raise ValueError("Independent transition conservation")
    return after, result, available


def audit_receipt(row):
    if set(row) != {"schema", "case", "mode", "initial", "events", "terminal"} or row["schema"] != "constructor01-events-v1" or row["mode"] not in MODES or not isinstance(row["case"], str) or not row["case"]:
        raise ValueError("Receipt schema/mode")
    if not isinstance(row["events"], list) or len(row["events"]) > 4096:
        raise ValueError("Event limit/schema")
    mode = row["mode"]
    state = copy.deepcopy(row["initial"])
    validate_state(state, mode, genesis=True)
    baseline = totals(state)
    history = {cid: {**copy.deepcopy(obj), "born": -1, "retired": None} for cid, obj in state["objects"].items()}
    chain = digest(state)
    summary = {"case": row["case"], "mode": mode, "events": len(row["events"]), "internal_C_births": 0,
               "external_or_direct_births": 0, "local_conversions": 0, "external_conversions": 0,
               "supplied_I_conversions": 0, "internal_I_conversions": 0, "unavailable_attempts": 0,
               "renewed_chain_conversions": 0, "renewed_chain_interface_ids": [], "renewed_chain_external_roots": []}
    renewed_ids, roots = set(), set()

    def renewed(interface_id):
        i = history[interface_id]
        sequence = [i]
        for expected_role in ("C", "A", "C"):
            parent = history.get(sequence[-1]["producer_id"])
            if parent is None or parent["role"] != expected_role or parent["origin"] != "internal":
                return False
            sequence.append(parent)
        # I4, C3, A2, C1 all internal; C1 must itself have a logged A0.
        if i["origin"] != "internal":
            return False
        a0 = history.get(sequence[-1]["producer_id"])
        if a0 is None or a0["role"] != "A":
            return False
        _, c3, a2, c1 = sequence
        return (a0["retired"] is not None and a0["retired"] < a2["born"] and
                c1["retired"] is not None and c1["retired"] < c3["born"])

    for seq, event in enumerate(row["events"]):
        if set(event) != {"seq", "request", "result", "opportunities", "before_sha256", "after", "previous_sha256", "sha256"} or type(event["seq"]) is not int or event["seq"] != seq:
            raise ValueError("Event schema/sequence")
        if event["previous_sha256"] != chain or event["before_sha256"] != digest(state):
            raise ValueError("Broken state/hash chain")
        computed_hash = digest({k: v for k, v in event.items() if k != "sha256"})
        if computed_hash != event["sha256"]:
            raise ValueError("Bad event hash")
        after, result, available = transition(state, event["request"], mode, history)
        equal(event["result"], result, "Forged outcome/identity/cost")
        equal(event["opportunities"], available, "Forged availability")
        equal(event["after"], after, "Forged poststate")
        if result["outcome"] == "birth":
            cid = result["object_id"]
            history[cid] = {**copy.deepcopy(after["objects"][cid]), "born": seq, "retired": None}
            summary["internal_C_births"] += result["origin"] == "internal" and event["request"]["role"] == "C"
            summary["external_or_direct_births"] += result["origin"] != "internal"
        elif result["outcome"] == "retire":
            history[result["retired_id"]]["retired"] = seq
        elif result["outcome"] == "convert":
            external = result["source"] == "external"
            summary["external_conversions" if external else "local_conversions"] += 1
            if not external:
                interface_id = result["object_id"]
                obj = history[interface_id]
                summary["internal_I_conversions" if obj["origin"] == "internal" else "supplied_I_conversions"] += 1
                if renewed(interface_id):
                    summary["renewed_chain_conversions"] += 1
                    renewed_ids.add(interface_id)
                    roots.update(obj["roots"])
        else:
            summary["unavailable_attempts"] += 1
        state, chain = after, computed_hash
        if totals(state) != baseline:
            raise ValueError("History ledger mismatch")
    equal(row["terminal"], state, "Forged terminal")
    summary["renewed_chain_interface_ids"] = sorted(renewed_ids)
    summary["renewed_chain_external_roots"] = sorted(roots)
    summary["material_residual"] = totals(state)[0] - baseline[0]
    summary["potential_residual"] = totals(state)[1] - baseline[1]
    return summary


def audit(input_dir, output_dir, revision):
    source, output = Path(input_dir), Path(output_dir)
    if output.exists() or len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("New output and exact source required")
    raw = (source / "receipts.jsonl").read_bytes()
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    expected_hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}
    equal(manifest, {"study": "constructor01-authored-measure-v1", "source_revision": revision,
                     "raw_sha256": hashlib.sha256(raw).hexdigest(), "authored_receipts": 16,
                     "new_scientific_initializations": 0, "source_hashes": expected_hashes}, "Manifest/source identity")
    rows = [json.loads(line) for line in raw.decode().splitlines()]
    if len(rows) != 16 or len({r["case"] for r in rows}) != 16:
        raise ValueError("Authored receipt count/duplicates")
    reports = [audit_receipt(row) for row in rows]
    renewed_cases = [r["case"] for r in reports if r["renewed_chain_conversions"]]
    equal(sorted(renewed_cases), ["fixed_renewed", "renewed"], "Authored endpoint expectation")
    result = {"study": "constructor01-authored-measure-v1", "source_revision": revision,
              "new_scientific_initializations": 0, "validated_authored_receipts": len(reports),
              "renewed_chain_fixture_cases": renewed_cases, "receipts": reports,
              "limitation": "Authored externally rooted histories, not natural formation, maintained closure or life."}
    output.mkdir(parents=True)
    (output / "audit.json").write_text(encode(result) + "\n", encoding="utf-8", newline="\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--expected-revision", required=True)
    args = parser.parse_args()
    audit(args.input_dir, args.output_dir, args.expected_revision)
