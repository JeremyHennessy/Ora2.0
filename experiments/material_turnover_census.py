"""Post-hoc read-only birth/use/cost census. Never changes frozen endpoints."""
import argparse
import hashlib
import json
from pathlib import Path

from experiments import material_turnover_audit as verifier


def census(output, revision):
    # Verify complete source-bound histories before deriving extra diagnostics.
    acceptance = verifier.audit(output, revision)
    raw = (Path(output) / "run-records.jsonl").read_bytes()
    records = [json.loads(line) for line in raw.splitlines()]
    rows = []
    for record in records:
        if record["initial_work"] != 96:
            continue
        arm = next(a for a in record["arms"] if a["mode"] == "active")
        state = arm["initial"]
        born = {}
        for event in arm["events"]:
            state, _, result = verifier.transition(state, "active", event["tick"], event["draw"])
            if result["outcome"] == "ligated":
                oid = result["product_id"]
                obj = state["objects"][oid]
                recycled = any(state["atoms"][a]["polymer_reclaims"] > 0 and
                               state["atoms"][a]["last_polymer_reclaim_tick"] < obj["born_tick"] for a in obj["atoms"])
                compatible = any(n["site"] == obj["site"] and state["atoms"][n["atom"]]["bit"] != obj["bits"][-1]
                                 for n in state["nutrients"].values())
                born[oid] = dict(polymer_recycled_material=recycled, compatible_nutrient_at_birth=compatible,
                                 funded_compatible_at_birth=compatible and state["W"] >= 2,
                                 conversions=0, contact_charge=0, contact_return=0,
                                 own_contact_work_minus_assembly=-result["charged_W"])
            if event["draw"][1] == 3 and result["targets"] and result["targets"][0] in born:
                target = born[result["targets"][0]]
                target["contact_charge"] += result["charged_W"]
                target["contact_return"] += result["returned_W"]
                target["own_contact_work_minus_assembly"] += result["returned_W"] - result["charged_W"]
                target["conversions"] += result["outcome"] == "converted"
        recycled = [b for b in born.values() if b["polymer_recycled_material"]]
        row = dict(seed=record["seed"], internally_ligated_polymers=len(born),
                   recycled_material_polymers=len(recycled),
                   recycled_with_compatible_nutrient_at_birth=sum(b["compatible_nutrient_at_birth"] for b in recycled),
                   recycled_with_funded_compatible_at_birth=sum(b["funded_compatible_at_birth"] for b in recycled),
                   recycled_with_actual_conversion=sum(b["conversions"] > 0 for b in recycled),
                   recycled_conversion_events=sum(b["conversions"] for b in recycled),
                   all_polymers_with_conversion=sum(b["conversions"] > 0 for b in born.values()),
                   all_positive_direct_work_margins=sum(b["own_contact_work_minus_assembly"] > 0 for b in born.values()),
                   recycled_positive_direct_work_margins=sum(b["own_contact_work_minus_assembly"] > 0 for b in recycled),
                   total_direct_work_margin=sum(b["own_contact_work_minus_assembly"] for b in born.values()))
        if row["internally_ligated_polymers"] != arm["statistics"]["births"] or row["recycled_conversion_events"] != arm["statistics"]["qualifying_uses"]:
            raise ValueError("Diagnostic disagrees with frozen birth/endpoint counts")
        rows.append(row)
    return dict(schema="turnover01-posthoc-census-v1", input_revision=revision,
                input_records_sha256=acceptance["records_sha256"],
                census_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                post_hoc=True, new_worlds_executed=0, independent_initializations_reused=16,
                totals={k: sum(r[k] for r in rows) for k in rows[0] if k != "seed"}, rows=rows,
                limit="Direct margins omit precursor/reclaim/ancestor and environmental costs; not lineage fitness or a causal mediation test")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    print(json.dumps(census(args.input_dir, args.source_revision), sort_keys=True, indent=2))
