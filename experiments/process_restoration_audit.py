"""Measurement-only receipt evaluator; never executes token payloads."""
import argparse
import hashlib
import json
from pathlib import Path

CONTRACT = "closure03-measurement-v1"


def integer(value):
    if type(value) is not int or value < 0:
        raise ValueError("invalid nonnegative integer")
    return value


def genome(value):
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError("invalid genome")
    if any(integer(x) > 3 for x in value):
        raise ValueError("invalid genome")
    return tuple(value)


def audit(receipt):
    if receipt.get("contract") != CONTRACT:
        raise ValueError("contract mismatch")
    law = receipt.get("law")
    if law not in ("splice-v1", "fixed-graph-v1"):
        return {"contract": CONTRACT, "status": "indeterminate", "restored": False}
    target, prerequisite = genome(receipt["target"]), genome(receipt["prerequisite"])
    if target == prerequisite:
        raise ValueError("distinct signatures required")
    initial, events = receipt["initial_tokens"], receipt["events"]
    if len(initial) > 64 or len(events) > 4096:
        raise ValueError("receipt bound exceeded")
    live, seen = {}, set()
    precursor, fuel = integer(receipt["precursor"]), integer(receipt["fuel"])
    waste = 0
    damage_step = None
    eligible = False
    productive_parents = {}

    def add(token, step, external):
        ident = token["id"]
        if not isinstance(ident, str) or not ident or len(ident) > 128 or ident in seen:
            raise ValueError("invalid or reused ID")
        live[ident] = (genome(token["genome"]), step, external)
        seen.add(ident)
        if len(live) > 128:
            raise ValueError("live token bound exceeded")

    for token in initial:
        add(token, -1, False)
    total = 4 * len(live) + precursor
    rules = {}
    for rule in receipt.get("rules", []):
        key = (genome(rule["a"]), genome(rule["b"]))
        if key in rules:
            raise ValueError("duplicate fixed rule")
        rules[key] = genome(rule["product"])
    for step, event in enumerate(events):
        if type(event["seq"]) is not int or event["seq"] != step:
            raise ValueError("event sequence mismatch")
        kind = event["kind"]
        if kind == "damage":
            if damage_step is not None:
                raise ValueError("multiple damage events")
            signatures = {item[0] for item in live.values()}
            eligible = target in signatures and prerequisite in signatures
            removed = sorted(k for k, v in live.items() if v[0] in (target, prerequisite))
            if event["removed_ids"] != removed:
                raise ValueError("incomplete damage")
            for ident in removed:
                del live[ident]
            waste += 4 * len(removed)
            damage_step = step
        elif kind == "decay":
            del live[event["id"]]
            waste += 4
        elif kind in ("collision", "rescue"):
            if fuel < 1:
                raise ValueError("insufficient fuel")
            fuel -= 1
            if kind == "rescue":
                if precursor < 4 or event["product"] is None:
                    raise ValueError("invalid rescue")
                precursor -= 4
                add(event["product"], step, True)
            else:
                a_id, b_id = event["a"], event["b"]
                if a_id == b_id:
                    raise ValueError("distinct parents required")
                a, b = live[a_id], live[b_id]
                if law == "splice-v1":
                    product = (a[0][1], b[0][1], a[0][2], b[0][2]) if a[0][0] == b[0][3] else None
                else:
                    product = rules.get((a[0], b[0]))
                if precursor < 4:
                    product = None
                recorded = event["product"]
                if (product is None) != (recorded is None):
                    raise ValueError("product presence mismatch")
                if product is not None:
                    if genome(recorded["genome"]) != product:
                        raise ValueError("product law mismatch")
                    precursor -= 4
                    add(recorded, step, a[2] or b[2])
                    # Preserve parent birth provenance even if a parent later decays.
                    productive_parents[recorded["id"]] = (a, b)
        else:
            raise ValueError("unknown event")
        state = {"live_ids": sorted(live), "precursor": precursor, "fuel": fuel, "waste": waste}
        declared = event["state"]
        for key in ("precursor", "fuel", "waste"):
            integer(declared[key])
        if declared != state or 4 * len(live) + precursor + waste != total:
            raise ValueError("ledger mismatch")
    if damage_step is None:
        raise ValueError("missing damage")
    def rebuilt(item, signature):
        return item[0] == signature and item[1] > damage_step and not item[2]
    has_prerequisite = any(rebuilt(v, prerequisite) for v in live.values())
    causal_target = any(
        rebuilt(v, target) and any(rebuilt(p, prerequisite) for p in productive_parents.get(k, ()))
        for k, v in live.items()
    )
    restored = eligible and has_prerequisite and causal_target
    return {"contract": CONTRACT, "status": "verified", "law": law,
            "eligible": eligible, "restored": restored,
            "constructive_payload_restoration": restored and law == "splice-v1",
            "material_total": total, "fuel_remaining": fuel,
            "events": len(events), "scientific_evidence": False}


def audit_file(source, output, expected_sha256):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output == source.parent or source.parent in output.parents or output.exists():
        raise ValueError("output must be a new directory outside input directory")
    if source.stat().st_size > 1024 * 1024:
        raise ValueError("input size bound exceeded")
    raw = source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise ValueError("input digest mismatch")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    result = audit(json.loads(raw, object_pairs_hook=unique))
    result["input_sha256"] = digest
    output.mkdir(parents=True)
    (output / "audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--expected-sha256", required=True)
    args = parser.parse_args()
    try:
        audit_file(args.input, args.output, args.expected_sha256)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(2, f"invalid receipt: {exc}\n")
