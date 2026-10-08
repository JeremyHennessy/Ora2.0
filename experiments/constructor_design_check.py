"""Read-only finite design analysis. No random worlds, ancestry or runtime."""
import argparse
from collections import deque
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAW = ROOT / "data/constructor01-law-v1.json"
SPECIES = ("P", "S", "A", "C", "I", "D", "waste", "W", "heat")
MASS = (1, 1, 4, 4, 4, 4, 1, 0, 0)
POTENTIAL = (0, 8, 0, 0, 0, 0, 0, 1, 1)
DEPENDENCIES = {"A": "C", "C": "A", "I": "C", "D": "C"}
PRICES = {"passive_work_cost": 0, "construction_material": 4,
          "construction_work": 2, "contact_read_work": 1,
          "contact_process_work": 1, "contact_return_work": 3,
          "contact_release_heat": 5, "impairment_work": 1}


def totals(state):
    return tuple(sum(a * b for a, b in zip(state, weights)) for weights in (MASS, POTENTIAL))


def vector(**entries):
    return [entries.get(s, 0) for s in SPECIES]


def expected_reactions():
    # Constraint oracle from the committed prose, independent of any simulator.
    rows = {}
    for product, catalyst in DEPENDENCIES.items():
        rows["make_" + product] = (catalyst, product, 2, vector(P=-4, W=-2, heat=2, **{product: 1}))
    rows.update({"convert": ("I", None, 2, vector(S=-1, waste=1, W=1, heat=7)),
                 "read_only": (None, None, 1, vector(W=-1, heat=1)),
                 "failed_contact": (None, None, 2, vector(W=-2, heat=2))})
    for species in DEPENDENCIES:
        rows["decay_" + species] = (species, None, 0, vector(waste=4, **{species: -1}))
    return rows


def check_state(state):
    if len(state) != 9 or any(type(n) is not int or n < 0 for n in state) or any(state[i] > 1 for i in range(2, 6)):
        raise ValueError("Invalid bounded state")


def validate(law):
    keys = {"schema", "species", "material_weights", "potential_weights", "slots", "reactions", "authored_envelopes"} | set(PRICES)
    if set(law) != keys or law["schema"] != "constructor01-design-v1":
        raise ValueError("Unknown contract field/schema")
    if tuple(law["species"]) != SPECIES or tuple(law["material_weights"]) != MASS or tuple(law["potential_weights"]) != POTENTIAL or law["slots"] != ["A", "C", "I", "D"]:
        raise ValueError("Incorrect species/ledger/slots")
    if any(type(law[k]) is not int or law[k] != v for k, v in PRICES.items()):
        raise ValueError("Unregistered price or maintenance assumption")
    expected = expected_reactions()
    rows = law["reactions"]
    if len(rows) != len(expected) or {r["name"] for r in rows} != set(expected):
        raise ValueError("Missing, duplicate or extra reaction")
    for r in rows:
        if set(r) != {"name", "catalyst", "product", "minimum_W", "delta"}:
            raise ValueError("Unknown reaction field")
        if len(r["delta"]) != 9 or any(type(n) is not int for n in r["delta"]) or type(r["minimum_W"]) is not int:
            raise ValueError("Noninteger reaction")
        if totals(r["delta"]) != (0, 0):
            raise ValueError("Nonconserving reaction")
        if (r["catalyst"], r["product"], r["minimum_W"], r["delta"]) != expected[r["name"]]:
            raise ValueError("Reaction violates paid dependency/contact contract")
    cases = law["authored_envelopes"]
    if len(cases) != 9 or len({c["name"] for c in cases}) != len(cases):
        raise ValueError("Nine distinct authored envelopes required")
    for c in cases:
        if set(c) != {"name", "state", "conversion_reachable"} or type(c["conversion_reachable"]) is not bool:
            raise ValueError("Invalid authored envelope")
        check_state(c["state"])


def advance(state, reaction):
    name = reaction["name"]
    if state[7] < reaction["minimum_W"]:
        return None
    catalyst, product = reaction["catalyst"], reaction["product"]
    if catalyst and not state[SPECIES.index(catalyst)]:
        return None
    if product and state[SPECIES.index(product)]:
        return None
    # A complete failed contact cannot also be a successful contact. Partial
    # readout is the actual W=1 trap, not a freely selectable cheap action.
    if name == "read_only" and state[7] != 1:
        return None
    if name == "failed_contact" and state[4] and state[1]:
        return None
    updated = tuple(a + b for a, b in zip(state, reaction["delta"]))
    if min(updated) < 0:
        return None
    check_state(updated)
    if totals(updated) != totals(state):
        raise ValueError("Transition ledger mismatch")
    return updated


def paid_impairment(state, slot):
    i = SPECIES.index(slot)
    if not state[i] or state[7] < 1:
        return None
    result = list(state)
    result[i] = 0
    result[6] += 4
    result[7] -= 1
    result[8] += 1
    check_state(result)
    if totals(result) != totals(state):
        raise ValueError("Impairment ledger mismatch")
    return tuple(result)


def envelope(case, reactions):
    initial = tuple(case["state"])
    distance = {initial: 0}
    queue = deque([initial])
    shortest_conversion = None
    constructor_birth = False
    edges = 0
    while queue:
        state = queue.popleft()
        for r in reactions:
            dest = advance(state, r)
            if dest is None:
                continue
            edges += 1
            constructor_birth |= r["name"] == "make_C"
            if r["name"] == "convert":
                length = distance[state] + 1
                shortest_conversion = length if shortest_conversion is None else min(length, shortest_conversion)
            if dest not in distance:
                if len(distance) >= 100000:
                    raise ValueError("Authored envelope exceeded finite analysis cap")
                distance[dest] = distance[state] + 1
                queue.append(dest)
    possible = shortest_conversion is not None
    if possible != case["conversion_reachable"]:
        raise ValueError("Authored envelope expectation failed: " + case["name"])
    return {"name": case["name"], "reachable_states": len(distance), "legal_edges": edges,
            "conversion_reachable": possible, "shortest_conversion_events": shortest_conversion,
            "constructor_birth_reachable": constructor_birth}


def analyze(law):
    validate(law)
    one_event_inputs = accepted = impairments = 0
    for slots in itertools.product(range(2), repeat=4):
        for p, w, s in itertools.product(range(13), range(9), range(3)):
            state = (p, s, *slots, 0, w, 0)
            one_event_inputs += 1
            for r in law["reactions"]:
                accepted += advance(state, r) is not None
            c_damage = paid_impairment(state, "C")
            d_damage = paid_impairment(state, "D")
            for slot in law["slots"]:
                impairments += paid_impairment(state, slot) is not None
            if c_damage and d_damage:
                # Matching mass, work, heat and other budgets; roles differ.
                for i in (0, 1, 6, 7, 8):
                    if c_damage[i] != d_damage[i]:
                        raise ValueError("Unmatched impairment price")
    return {"study": "constructor01-static-design-v1", "stochastic_worlds": 0,
            "independent_scientific_populations": 0, "one_event_input_states": one_event_inputs,
            "legal_one_event_transitions": accepted, "legal_paid_impairments": impairments,
            "reaction_vectors_conserve": len(law["reactions"]),
            "authored_envelopes": [envelope(c, law["reactions"]) for c in law["authored_envelopes"]],
            "contact_net_work": 1, "contact_start_buffer": 2,
            "A_to_C_I_construction_work": 4, "A_to_C_I_minimum_initial_work": 6,
            "claim": "Ideal finite feasibility only; no stochastic exposure, ID ancestry, maintained network or life evidence."}


def report(output, revision):
    target = Path(output)
    if target.exists() or len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("New output and exact source revision required")
    result = analyze(json.loads(LAW.read_text(encoding="utf-8")))
    files = ("data/constructor01-law-v1.json", "docs/CONSTRUCTOR-01-DESIGN-CONTRACT.md", "experiments/constructor_design_check.py")
    result["source_revision"] = revision
    result["source_hashes"] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}
    target.mkdir(parents=True)
    (target / "design-check.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    report(args.output_dir, args.source_revision)
