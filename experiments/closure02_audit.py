"""CLOSURE-02: independent read-only archive audit of the frozen functional shell trial.

No simulator execution, no chemistry revisions, no 'alive' classifier.
"""
from __future__ import annotations

from collections import defaultdict
import argparse
import hashlib
import json
from pathlib import Path

from experiments.closure02_functional import ARMS, ORIGINS, canonical

FROZEN = {
    "worlds.jsonl": "e75376cd6e711a6ae3a20d8dd277ae203486982b91046f56e92117122c45ec33",
    "traces.jsonl": "fcbb04f897fe6f0ac5de2db6494f56a691340b8b008d61064a9dceb374960fd4",
}


def audit(source: Path, dest: Path, *, first_run: bool = True) -> dict:
    originals = {name: (source/name).read_bytes() for name in FROZEN}
    sha = {key: hashlib.sha256(data).hexdigest() for key,data in originals.items()}
    summary = json.loads((source/"summary.json").read_bytes())
    if (sha["worlds.jsonl"] != summary.get("worlds_sha256") or
        sha["traces.jsonl"] != summary.get("traces_sha256")):
        raise ValueError("Source files fail their own summary SHA256 manifest")
    if first_run and sha != FROZEN:
        raise ValueError("Fresh run disagrees with original CLOSURE-02 raw SHA256")
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
    if summary["total_treatments"] != len(worlds):
        raise ValueError("Summary world count inconsistent")
    count_by_world=defaultdict(int)
    chain_by_world={k:hashlib.sha256() for k in mapping}
    last_row={}
    core_streaks=defaultdict(int)
    independently_recovered=defaultdict(bool)
    for raw_line in originals["traces.jsonl"].splitlines():
        if not raw_line.strip():continue
        row=json.loads(raw_line)
        key=(row["seed"],row["origin"],row["arm"])
        if key not in mapping:
            raise ValueError("Trace refers to unrecorded treatment")
        count_by_world[key]+=1
        if row["t"] != count_by_world[key]:
            raise ValueError("Missing, reordered, or duplicate timeline step")
        if row["mass_residual"]:
            raise ValueError("Particle-conservation violation in stored trace")
        accepted=row["cumulative_flow"]
        for direction in ("inward","outward"):
            if accepted[f"{direction}_moves"] > accepted[f"{direction}_proposals"]:
                raise ValueError("Impossible accepted boundary hops")
        previous=last_row.get(key)
        if previous:
            for field,value in accepted.items():
                if value<previous["cumulative_flow"][field]:
                    raise ValueError("Nonmonotonic cumulative reaction/hop counter")
        chain_by_world[key].update((canonical(row)+"\n").encode("utf-8"))
        core_streaks[key]=core_streaks[key]+1 if row["core_ok"] else 0
        if core_streaks[key]>=3:
            independently_recovered[key]=True
        last_row[key]=row
    results=[]
    for key,row in sorted(mapping.items()):
        if count_by_world[key]!=60:
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
    result={
        "status":"read_only_archive_verification_not_biological_life",
        "worlds":len(worlds),
        "verified_steps":len(originals["traces.jsonl"].splitlines()),
        "eligible":eligible,
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
    args=ap.parse_args()
    result=audit(args.input_dir,args.output_dir,first_run=not args.dev_only)
    print(canonical(result))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
