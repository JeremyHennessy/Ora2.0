"""Independent full-stream, material, energy and ancestry audit; no simulator import."""
import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
ARMS = ("active", "fixed", "ghost_reclaim", "ghost_capture", "local_stock", "shared_stock", "direct_access")
FILES = ("data/turnover01-law-v1.json", "docs/TURNOVER-01-PROTOCOL.md",
         "experiments/material_turnover.py", "experiments/material_turnover_audit.py")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def sha(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def regenerate(seed, work):
    generator = random.Random(seed)
    atoms, objects, nutrients = {}, {}, {}
    for i in range(32):
        atom = "a" + str(i)
        bit = str(generator.randrange(2))
        atoms[atom] = dict(bit=bit, origin="genesis_monomer", polymer_reclaims=0, last_polymer_reclaim_tick=None)
        objects["g" + str(i)] = dict(site=i // 4, bits=bit, atoms=[atom], born_tick=-1, parents=[], origin="genesis")
    for i in range(32):
        site = generator.randrange(8)
        atom = "a" + str(i + 32)
        atoms[atom] = dict(bit=str(generator.randrange(2)), origin="genesis_nutrient", polymer_reclaims=0, last_polymer_reclaim_tick=None)
        nutrients["n" + str(i)] = dict(site=site, atom=atom)
    draws = []
    for _ in range(128):
        draws.append([generator.randrange(bound) for bound in (8, 8, 65536, 65536, 65536)])
    return dict(W=work, heat=0, atoms=atoms, objects=objects, waste={}, nutrients=nutrients), draws


def ledger(state):
    if type(state["W"]) is not int or type(state["heat"]) is not int or min(state["W"], state["heat"]) < 0:
        raise ValueError("Negative/noninteger energy")
    locations = []
    bond = 0
    for obj in state["objects"].values():
        ids = obj["atoms"]
        if not 1 <= len(ids) <= 6 or obj["bits"] != "".join(state["atoms"][a]["bit"] for a in ids):
            raise ValueError("Sequence/atom mismatch")
        locations.extend(ids)
        bond += len(ids) - 1
    locations.extend(state["waste"])
    locations.extend(n["atom"] for n in state["nutrients"].values())
    if len(locations) != 64 or len(set(locations)) != 64 or set(locations) != set(state["atoms"]):
        raise ValueError("Duplicated/lost/invented atom")
    counts = tuple(sum(state["atoms"][a]["bit"] == bit for a in locations) for bit in ("0", "1"))
    return (*counts, state["W"] + state["heat"] + bond + 8 * len(state["nutrients"]))


def transition(old, mode, tick, draw):
    state = copy.deepcopy(old)
    site, action, selector, partner, resource = draw
    eligible = sorted(k for k, v in old["objects"].items() if v["site"] == site or (action < 2 and mode == "shared_stock"))
    target = eligible[selector % len(eligible)] if eligible else None
    alternatives = [k for k in eligible if k != target]
    other = alternatives[partner % len(alternatives)] if alternatives else None
    waste_pool = sorted(k for k, v in old["waste"].items() if v["site"] == site)
    atom = waste_pool[selector % len(waste_pool)] if waste_pool else None
    food_pool = sorted(k for k, v in old["nutrients"].items() if v["site"] == site)
    food = food_pool[resource % len(food_pool)] if food_pool else None
    binds = bool(target and food and len(old["objects"][target]["atoms"]) > 1 and
                 int(old["objects"][target]["bits"][-1]) + int(old["atoms"][old["nutrients"][food]["atom"]]["bit"]) == 1)
    structural = other is not None and len(old["objects"][target]["atoms"]) + len(old["objects"][other]["atoms"]) <= 6
    opportunities = dict(ligation_structural=action < 2 and structural,
                         ligation_funded=action < 2 and structural and old["W"] >= 2,
                         reclaim_structural=action == 2 and atom is not None,
                         reclaim_funded=action == 2 and atom is not None and old["W"] > 0,
                         contact_binding=action == 3 and binds,
                         contact_funded=action == 3 and binds and old["W"] >= 2,
                         direct_contact_funded=action == 3 and food is not None and old["W"] >= 2)
    outcome, reason, targets, product = "unavailable", None, [], None
    charge, returned, heat = 0, 0, 0
    source, primary, polymer_reclaim = None, False, False
    if action < 2:
        targets = [k for k in (target, other) if k is not None]
        if not structural:
            reason = "no_pair_or_length"
        elif old["W"] < 2:
            reason = "no_work"
        else:
            product = "b" + str(tick)
            left, right = old["objects"][target], old["objects"][other]
            del state["objects"][target]
            del state["objects"][other]
            state["objects"][product] = dict(site=site, bits=left["bits"] + right["bits"], atoms=left["atoms"] + right["atoms"],
                                               born_tick=tick, parents=targets[:], origin="ligation")
            outcome, charge, heat = "ligated", 2, 1
    elif action == 2:
        targets = [] if atom is None else [atom]
        if mode in {"local_stock", "shared_stock"}:
            reason = "reclaim_disabled"
        elif atom is None or old["W"] < 1:
            reason = "no_waste_or_work"
        elif mode == "ghost_reclaim":
            outcome, charge, heat = "paid_ghost", 1, 1
        else:
            discarded = state["waste"].pop(atom)
            polymer_reclaim = discarded["retired_length"] > 1
            if polymer_reclaim:
                state["atoms"][atom]["polymer_reclaims"] += 1
                state["atoms"][atom]["last_polymer_reclaim_tick"] = tick
            product = "r" + str(tick)
            state["objects"][product] = dict(site=site, bits=state["atoms"][atom]["bit"], atoms=[atom], born_tick=tick,
                                               parents=[] if discarded["retired_id"] is None else [discarded["retired_id"]], origin="reclaim")
            outcome, charge, heat = "reclaimed", 1, 1
    elif action == 3:
        targets = [k for k in (target, food) if k is not None]
        if old["W"] == 0:
            reason = "no_work"
        else:
            charge = min(2, old["W"])
            heat = charge
            outcome = "contact_partial" if charge == 1 else "contact_spent"
            effective = food is not None and (mode == "direct_access" or binds and mode != "ghost_capture")
            if charge == 2 and effective:
                if mode != "direct_access":
                    obj = old["objects"][target]
                    qualified_atoms = [old["atoms"][a] for a in obj["atoms"]]
                    primary = obj["origin"] == "ligation" and any(a["polymer_reclaims"] > 0 and a["last_polymer_reclaim_tick"] < obj["born_tick"] for a in qualified_atoms)
                consumed = state["nutrients"].pop(food)["atom"]
                state["waste"][consumed] = dict(site=site, retired_id=None, retired_length=0, retired_tick=tick)
                outcome, returned, heat = "converted", 3, 7
                source = "engine_direct" if mode == "direct_access" else "binding"
    elif action == 4:
        targets = [] if target is None else [target]
        if target is None:
            reason = "no_object"
        else:
            former = state["objects"].pop(target)
            for consumed in former["atoms"]:
                state["waste"][consumed] = dict(site=site, retired_id=target, retired_length=len(former["atoms"]), retired_tick=tick)
            outcome, heat = "decayed", len(former["atoms"]) - 1
    elif action == 5:
        targets = [] if target is None else [target]
        if target is None:
            reason = "no_object"
        else:
            state["objects"][target]["site"] = (site - 1 + 2 * (partner % 2)) % 8
            outcome = "moved"
    else:
        outcome = "idle"
    state["W"] += returned - charge
    state["heat"] += heat
    result = dict(outcome=outcome, reason=reason, targets=targets, product_id=product, charged_W=charge,
                  returned_W=returned, heat_delta=heat, binding_match=binds if action == 3 else False,
                  source=source, qualifying_turnover=primary, polymer_origin_reclaim=polymer_reclaim)
    return state, opportunities, result


def measure(initial, events, terminal):
    rs = [e["result"] for e in events]
    sequences = {k: v["bits"] for k, v in initial["objects"].items()}
    births = {}
    for e in events:
        result = e["result"]
        if result["outcome"] == "ligated":
            seq = sequences[result["targets"][0]] + sequences[result["targets"][1]]
            sequences[result["product_id"]] = seq
            births[seq] = births.get(seq, 0) + 1
        if result["outcome"] == "reclaimed":
            sequences[result["product_id"]] = terminal["atoms"][result["targets"][0]]["bit"]
    qualifying = [r for r in rs if r["qualifying_turnover"]]
    return dict(births=sum(births.values()), birth_sequences=births,
                reclaims=sum(r["outcome"] == "reclaimed" for r in rs),
                polymer_origin_reclaims=sum(r["polymer_origin_reclaim"] for r in rs),
                decays=sum(r["outcome"] == "decayed" for r in rs), conversions=sum(r["outcome"] == "converted" for r in rs),
                binding_conversions=sum(r["source"] == "binding" for r in rs), qualifying_uses=len(qualifying),
                distinct_qualifying_polymers=len({r["targets"][0] for r in qualifying}),
                charged_W=sum(r["charged_W"] for r in rs), returned_W=sum(r["returned_W"] for r in rs),
                unavailable_events=sum(r["outcome"] == "unavailable" for r in rs),
                partial_contacts=sum(r["outcome"] == "contact_partial" for r in rs),
                exhausted_events=sum(e["work_before"] == 0 for e in events),
                opportunities={k: sum(e["opportunities"][k] for e in events) for k in events[0]["opportunities"]},
                terminal_W=terminal["W"], terminal_heat=terminal["heat"],
                terminal_bond_potential=sum(len(v["atoms"]) - 1 for v in terminal["objects"].values()),
                terminal_nutrients=len(terminal["nutrients"]), terminal_waste_atoms=len(terminal["waste"]))


def verify_record(record, seed, work):
    initial, draws = regenerate(seed, work)
    if set(record) != {"schema", "seed", "initial_work", "draws", "arms"} or record["schema"] != "turnover01-record-v1" or canonical([record["seed"], record["initial_work"], record["draws"]]) != canonical([seed, work, draws]):
        raise ValueError("Wrong seed/budget/generator stream")
    if len(record["arms"]) != len(ARMS):
        raise ValueError("Missing/extra arms")
    checks = []
    for mode, arm in zip(ARMS, record["arms"]):
        if set(arm) != {"mode", "initial", "events", "terminal", "statistics"} or arm["mode"] != mode or canonical(arm["initial"]) != canonical(initial) or len(arm["events"]) != 128:
            raise ValueError("Altered founder/arm/event count")
        state, chain, budget = copy.deepcopy(initial), sha(initial), ledger(initial)
        used = set(initial["objects"])
        for tick, draw in enumerate(draws):
            old = state
            state, opportunities, result = transition(old, mode, tick, draw)
            product = result["product_id"]
            if product:
                if product in used:
                    raise ValueError("Object ID reused")
                used.add(product)
            if ledger(state) != budget:
                raise ValueError("Bit material/energy divergence")
            event = dict(tick=tick, draw=draw, work_before=old["W"], opportunities=opportunities, result=result,
                         before_sha256=sha(old), after_sha256=sha(state), previous_sha256=chain)
            event["event_sha256"] = sha(event)
            if canonical(arm["events"][tick]) != canonical(event):
                raise ValueError(f"Forged request/state/cost/ancestry at{seed}/{work}/{mode}/{tick}")
            chain = event["event_sha256"]
        if canonical(arm["terminal"]) != canonical(state) or canonical(arm["statistics"]) != canonical(measure(initial, arm["events"], state)):
            raise ValueError("Forged terminal or statistics")
        checks.append(arm)
    if canonical({k: v for k, v in checks[0].items() if k != "mode"}) != canonical({k: v for k, v in checks[1].items() if k != "mode"}):
        raise ValueError("Fixed physical law failed exact match")


def static_grammar():
    # This is a frozen v1 interpreter, not an editable reaction configuration.
    # Reject a law document that no longer describes the validated semantics.
    expected_law = dict(schema="turnover01-law-v1", alphabet="01", sites=8, max_chain_length=6,
                        atom_mass=1, bond_potential=1, nutrient_potential=8,
                        ligation_work=2, ligation_heat=1, reclaim_work=1, reclaim_heat=1,
                        contact_read_work=1, contact_process_work=1, contact_return_work=3, contact_release_heat=5,
                        binding_rule="length_at_least_two_and_terminal_bit_complements_nutrient",
                        decay_rule="all_atoms_to_local_waste_and_all_bond_potential_to_heat", passive_upkeep_work=0,
                        pilot=dict(seeds=[112, 128], ticks=128, monomers_per_site=4, nutrients=32,
                                   work_regimes=[96, 0], arms=list(ARMS)))
    actual_law = json.loads((ROOT / FILES[0]).read_bytes())
    if canonical(actual_law) != canonical(expected_law):
        raise ValueError("Frozen v1 law document changed")
    chains = ["".join(bits) for n in range(1, 7) for bits in itertools.product("01", repeat=n)]
    checks, legal_joins = 0, 0
    def totals(parts, work, heat, nutrients=()):
        text = "".join(parts) + "".join(nutrients)
        return (text.count("0"), text.count("1"), work + heat + sum(len(x) - 1 for x in parts) + 8 * len(nutrients))
    for x in chains:
        for y in chains:
            if len(x + y) > 6:
                continue
            legal_joins += 1
            for work in range(4):
                if work >= 2 and totals([x, y], work, 0) != totals([x + y], work - 2, 1):
                    raise ValueError("Ligation static ledger")
                checks += 1
        for work in range(4):
            # Waste atoms carry no bond potential; paid recovery also heats.
            if totals([x], work, 0) != totals(list(x), work, len(x) - 1):
                raise ValueError("Decay static ledger")
            checks += 1
        for bit in "01":
            for work in range(4):
                charge = min(work, 2)
                enabled = len(x) > 1 and int(x[-1]) + int(bit) == 1 and charge == 2
                before = totals([x], work, 0, [bit])
                after = totals([x, bit], work + 1, 7) if enabled else totals([x], work - charge, charge, [bit])
                if before != after:
                    raise ValueError("Capture static ledger")
                checks += 1
    for bit in "01":
        for work in range(4):
            if work >= 1 and totals([bit], work, 0) != totals([bit], work - 1, 1):
                raise ValueError("Reclaim static ledger")
            checks += 1
    return {"chains": len(chains), "length_permitted_ligations": legal_joins, "bounded_reaction_cases": checks,
            "bit_and_energy_residuals_zero": True}


def independent_summary(records, revision):
    regimes = {}
    for work in (96, 0):
        panel = [r for r in records if r["initial_work"] == work]
        totals = {}
        for mode in ARMS:
            values = [next(a["statistics"] for a in r["arms"] if a["mode"] == mode) for r in panel]
            totals[mode] = {k: sum(v[k] for v in values) for k in values[0] if type(values[0][k]) is int}
            totals[mode]["opportunity_worlds"] = sum(v["qualifying_uses"] > 0 for v in values)
            totals[mode]["opportunities"] = {k: sum(v["opportunities"][k] for v in values) for k in values[0]["opportunities"]}
        contrasts = []
        for record in panel:
            lookup = {a["mode"]: a["statistics"] for a in record["arms"]}
            contrasts.append(dict(seed=record["seed"], active_uses=lookup["active"]["qualifying_uses"],
                                  conversion_difference=lookup["active"]["conversions"] - lookup["ghost_reclaim"]["conversions"],
                                  terminal_W_difference=lookup["active"]["terminal_W"] - lookup["ghost_reclaim"]["terminal_W"]))
        regimes[str(work)] = dict(arms=totals, active_vs_ghost_reclaim=contrasts)
    funded = regimes["96"]
    admitted = funded["arms"]["active"]["opportunity_worlds"] >= 4 and sum(c["conversion_difference"] > 0 for c in funded["active_vs_ghost_reclaim"]) >= 4 and sum(c["conversion_difference"] for c in funded["active_vs_ghost_reclaim"]) > 0
    return dict(schema="turnover01-summary-v1", source_revision=revision,
                source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in FILES},
                independent_initializations=16, paired_seed_regime_records=32, arm_histories=224, events=28672,
                regimes=regimes, admission_screen_passed=admitted,
                decision="propose_separate_causal_protocol" if admitted else "close_negative_opportunity_pilot",
                claim_limit="installed-law opportunity; no self-maintenance, evolution or inheritance")


def audit(output, revision):
    if not isinstance(revision, str) or len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("Exact source revision required")
    output = Path(output)
    with (output / "run-records.jsonl").open("rb") as stream:
        raw = stream.read(100 * 1024 * 1024 + 1)
    if len(raw) > 100 * 1024 * 1024 or not raw.endswith(b"\n"):
        raise ValueError("Incomplete/oversized stream")
    records = [json.loads(line, object_pairs_hook=no_duplicates) for line in raw.splitlines()]
    if len(records) != 32:
        raise ValueError("All independent and paired denominators required")
    for record, (seed, work) in zip(records, itertools.product(range(112, 128), (96, 0))):
        verify_record(record, seed, work)
    expected = independent_summary(records, revision)
    expected["records_sha256"] = hashlib.sha256(raw).hexdigest()
    observed = json.loads((output / "summary.json").read_bytes(), object_pairs_hook=no_duplicates)
    if canonical(expected) != canonical(observed):
        raise ValueError("Summary/source mismatch")
    return {"verified_revision": revision, "independent_initializations": 16, "paired_records": 32,
            "verified_histories": 224, "verified_events": 28672, "exact_fixed_matches": 32,
            "per_bit_material_and_energy_conserved": True, "admission_screen_passed": expected["admission_screen_passed"],
            "records_sha256": expected["records_sha256"], "static_grammar": static_grammar(), "no_organism_claim": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.input_dir, args.source_revision), sort_keys=True, indent=2))
