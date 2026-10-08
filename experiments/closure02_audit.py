"""CLOSURE-02: independent read-only archive audit of the frozen functional shell trial.

No simulator execution, no chemistry revisions, no 'alive' classifier.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from experiments import closure_spatial as physics
from experiments import closure02_functional as simulator
import argparse
import hashlib
import json
from pathlib import Path

from experiments.closure02_functional import ARMS, ORIGINS, canonical

FROZEN = {
    "worlds.jsonl": "e75376cd6e711a6ae3a20d8dd277ae203486982b91046f56e92117122c45ec33",
    "traces.jsonl": "fcbb04f897fe6f0ac5de2db6494f56a691340b8b008d61064a9dceb374960fd4",
}


def audit(source: Path, dest: Path, *, first_run: bool = True,
          expected_revision: str | None = None) -> dict:
    # The analyzer must never write into or above its input archive.
    src, out = source.resolve(), dest.resolve()
    if src == out or src in out.parents or out in src.parents:
        raise ValueError("Audit output must be separate from immutable input")
    originals = {name: (source/name).read_bytes() for name in FROZEN}
    sha = {key: hashlib.sha256(data).hexdigest() for key,data in originals.items()}
    summary = json.loads((source/"summary.json").read_bytes())
    if (sha["worlds.jsonl"] != summary.get("worlds_sha256") or
        sha["traces.jsonl"] != summary.get("traces_sha256")):
        raise ValueError("Source files fail their own summary SHA256 manifest")
    if first_run and sha != FROZEN:
        raise ValueError("Fresh run disagrees with original CLOSURE-02 raw SHA256")
    if expected_revision is not None and summary.get("source_revision") != expected_revision:
        raise ValueError("Execution revision mismatch")
    for field, module in (
        ("source_sha256", simulator),
        ("original_model_source_sha256", physics),
    ):
        if summary.get(field) != hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest():
            raise ValueError("Execution source checksum mismatch")
    params = summary.get("parameters", {})
    if first_run and params != asdict(physics.Protocol()):
        raise ValueError("Frozen protocol parameters differ")
    p = physics.Protocol(**params)
    worlds = [json.loads(line) for line in originals["worlds.jsonl"].splitlines()
              if line.strip()]
    ids = [(r["seed"],r["origin"],r["arm"]) for r in worlds]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate seed+origin+arm record")
    mapping = {key:row for key,row in zip(ids,worlds)}
    seeds = sorted({seed for seed,_,_ in ids})
    want = {(seed,origin,arm) for seed in seeds for origin in ORIGINS for arm in ARMS}
    if set(mapping)!=want:
        raise ValueError("Incomplete or extra treatment identities")
    if first_run and seeds != list(range(6400,6464)):
        raise ValueError("Unexpected frozen study seed panel")
    if summary.get("seed_list") != seeds:
        raise ValueError("Manifest seed panel inconsistent")
    if summary["total_treatments"] != len(worlds):
        raise ValueError("Summary world count inconsistent")
    count_by_world=defaultdict(int)
    chain_by_world={k:hashlib.sha256() for k in mapping}
    last_row={}
    core_streaks=defaultdict(int)
    independently_recovered=defaultdict(bool)
    first_recovery={}
    for key, record in mapping.items():
        before = record["pre_damage_region"]
        eligible = (before["core_a"] >= p.min_pre_a and
                    before["core_r"] >= p.min_pre_r and
                    before["ring_coverage"] >= p.min_pre_ring)
        if record["eligible"] is not eligible:
            raise ValueError("Predamage eligibility contradicts counts")
        if type(record["target"]) is not int or not 0 <= record["target"] < 81:
            raise ValueError("Invalid fixed target")
    for raw_line in originals["traces.jsonl"].splitlines():
        if not raw_line.strip():continue
        row=json.loads(raw_line)
        key=(row["seed"],row["origin"],row["arm"])
        if key not in mapping:
            raise ValueError("Trace refers to unrecorded treatment")
        count_by_world[key]+=1
        if row["t"] != count_by_world[key]:
            raise ValueError("Missing, reordered, or duplicate timeline step")
        record = mapping[key]
        before = record["pre_damage_region"]
        core_ok = bool(record["eligible"] and
                       row["core_a"] >= p.core_recovery_fraction * before["core_a"] and
                       row["core_r"] >= p.core_recovery_fraction * before["core_r"])
        if row["core_ok"] is not core_ok:
            raise ValueError("Core threshold flag contradicts raw counts")
        if row["eligible"] is not record["eligible"] or row["target"] != record["target"]:
            raise ValueError("Trace target or eligibility changed")
        counts = row["counts"]
        if set(counts) != {"s", "a", "r", "m", "w"} or any(
            type(v) is not int or v < 0 for v in counts.values()
        ):
            raise ValueError("Invalid trace particle counts")
        expected_inflow = (p.warmup_steps + row["t"]) * p.added_s_per_step
        if row["inflow"] != expected_inflow or sum(counts.values()) != (
            p.initial_s_per_site * 81 + expected_inflow
        ):
            raise ValueError("Raw particle ledger does not balance")
        if row["mass_residual"]:
            raise ValueError("Particle-conservation violation in stored trace")
        accepted=row["cumulative_flow"]
        if any(type(v) is not int or v < 0 for v in accepted.values()):
            raise ValueError("Invalid reaction or movement counter")
        if accepted["catalytic_s_consumed"] != sum(
            accepted[k] for k in ("new_a", "new_r", "new_m", "ghost_w")
        ):
            raise ValueError("Raw reaction debit does not balance")
        arm = key[2]
        if arm in ("ghost_effect", "ghost_inert", "no_shell") and accepted["new_m"]:
            raise ValueError("Forbidden M synthesis")
        if arm in ("shell_effect", "shell_inert", "no_shell") and accepted["ghost_w"]:
            raise ValueError("Forbidden ghost synthesis")
        for direction in ("inward","outward"):
            if accepted[f"{direction}_moves"] > accepted[f"{direction}_proposals"]:
                raise ValueError("Impossible accepted boundary hops")
        previous=last_row.get(key)
        if previous:
            for field,value in accepted.items():
                if value<previous["cumulative_flow"][field]:
                    raise ValueError("Nonmonotonic cumulative reaction/hop counter")
        chain_by_world[key].update((canonical(row)+"\n").encode("utf-8"))
        core_streaks[key]=core_streaks[key]+1 if core_ok else 0
        if core_streaks[key]>=p.recovery_streak:
            independently_recovered[key]=True
            first_recovery.setdefault(key, row["t"] - p.recovery_streak + 1)
        last_row[key]=row
    results=[]
    for key,row in sorted(mapping.items()):
        if count_by_world[key]!=p.followup_steps:
            raise ValueError("Treatment missing 60 postdamage events")
        if row["trace_sha256"]!=chain_by_world[key].hexdigest():
            raise ValueError("Per-world event-chain SHA256 mismatch")
        final=last_row[key]
        if final["counts"] != row["final_global_counts"]:
            raise ValueError("Final global state disagrees with time-series")
        if final["cumulative_flow"] != row["flow"]:
            raise ValueError("Final cumulative flux disagrees with record")
        if bool(row["eligible"])!=bool(final["eligible"]):
            raise ValueError("Eligibility changed after intervention")
        independently_expected=bool(independently_recovered[key]) if row["eligible"] else None
        if row["first_core_recovery"] != first_recovery.get(key):
            raise ValueError("First recovery time contradicts raw counts")
        for direction, field in (("outward", "outward_acceptance_rate"),
                                 ("inward", "inward_acceptance_rate")):
            proposed = row["flow"][direction + "_proposals"]
            rate = row["flow"][direction + "_moves"] / proposed if proposed else None
            if row[field] != rate:
                raise ValueError("Acceptance rate contradicts movement ledger")
        if row["core_recovered"] is not independently_expected:
            raise ValueError("Core-recovery certificate contradicts raw three-step sequence")
        if row["max_mass_residual"]:
            raise ValueError("World records declare invalid conservation")
        grid=row["final_grid"]
        if set(grid)!={"s","a","r","m","w"}:
            raise ValueError("Incomplete final grid")
        for species,values in grid.items():
            if len(values)!=81 or any(not isinstance(n,int) or n<0 for n in values):
                raise ValueError("Invalid final grid geometry or particle count")
            if sum(values)!=row["final_global_counts"][species]:
                raise ValueError("Final grid contradicts species totals")
        core = (row["target"],) + physics.NEIGH8[row["target"]]
        for species in ("a", "r"):
            actual = sum(grid[species][i] for i in core)
            if actual != row["final_core_" + species] or actual != final["core_" + species]:
                raise ValueError("Final core contradicts lattice counts")
        results.append({
            "seed":key[0],"origin":key[1],"arm":key[2],
            "eligible":row["eligible"],
            "core_recovered":row["core_recovered"],
            "time_steps":count_by_world[key],
            "trace_sha256":chain_by_world[key].hexdigest(),
        })
    for seed in seeds:
        for origin in ORIGINS:
            cohort=[mapping[seed,origin,arm] for arm in ARMS]
            if len({row["checkpoint_sha256"] for row in cohort})!=1:
                raise ValueError("Forked treatments have different original checkpoints")
            if len({row["eligible"] for row in cohort})!=1:
                raise ValueError("Treatment eligibility differs")
            if len({canonical(row["post_damage_region"]) for row in cohort})!=1:
                raise ValueError("Forked core damage differs")
    eligible=sum(mapping[seed,origin,ARMS[0]]["eligible"]
                 for seed in seeds for origin in ORIGINS)
    if eligible!=summary["eligible_core_worlds"]:
        raise ValueError("Analysis denominator inconsistent")
    for arm in ARMS:
        observed=sum(r["core_recovered"] is True for r in worlds
                     if r["arm"]==arm and r["eligible"])
        expected=summary["combined_eligible_results"][arm]["core_recovered"]
        if observed!=expected:
            raise ValueError("Summary recovery count doesn't match treatment records")
    recovered = {
        arm: sum(r["core_recovered"] is True for r in worlds if r["arm"] == arm)
        for arm in ARMS
    }
    flows = {
        arm: {
            field: sum(r["flow"][field] for r in worlds
                       if r["arm"] == arm and r["eligible"])
            for field in ("outward_moves", "outward_proposals",
                          "inward_moves", "inward_proposals", "new_a", "new_r",
                          "new_m", "ghost_w", "catalytic_s_consumed")
        } for arm in ARMS
    }
    for arm in ARMS:
        for field, summary_field in (
            ("outward_moves", "outward_hops"), ("outward_proposals", "outward_proposals"),
            ("inward_moves", "inward_hops"), ("inward_proposals", "inward_proposals"),
        ):
            if flows[arm][field] != summary["combined_eligible_results"][arm][summary_field]:
                raise ValueError("Summary flux contradicts raw counters")
    result={
        "status":"read_only_archive_verification_not_biological_life",
        "worlds":len(worlds),
        "verified_steps":len(originals["traces.jsonl"].splitlines()),
        "eligible":eligible,
        "independently_derived_core_recovery":recovered,
        "eligible_flow_totals":flows,
        "recovery_derived_from_counts":True,
        "source_checksums_verified":True,
        "file_sha256":sha,
        "match_original_run":first_run and sha==FROZEN,
        "all_world_event_chains_valid":True,
        "zero_particle_ledger_discrepancies":True,
        "source_claim_limit":"checks recording consistency, not independent physical causal mechanisms",
    }
    dest.mkdir(parents=True,exist_ok=True)
    rows_text="".join(canonical(x)+"\n" for x in results)
    (dest/"verified-worlds.jsonl").write_text(rows_text,encoding="utf-8")
    result["verified_world_rows_sha256"]=hashlib.sha256(rows_text.encode()).hexdigest()
    (dest/"audit-summary.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    return result


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input-dir",type=Path,required=True)
    ap.add_argument("--output-dir",type=Path,required=True)
    ap.add_argument("--dev-only",action="store_true")
    ap.add_argument("--expected-revision",required=True)
    args=ap.parse_args()
    result=audit(args.input_dir,args.output_dir,first_run=not args.dev_only,
                 expected_revision=args.expected_revision)
    print(canonical(result))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
