# AL07-TRACE v1 — Frozen read-only causal-genealogy audit

**Registered:** 2026-10-08, before running this independent audit on AL02 held-out data. **Status:** analytic protocol, not a living-organism experiment, new world, or general causal proof.

## Why and scientific input

[AI-Research](https://github.com/JeremyHennessy/AI-Research) main commit `a9bed3c57d915c04d07bb1fc4a1391c62e3e5823` passed offline CI in run `37784626413`. Its [Outlier/Hg causal-lineage review](https://github.com/JeremyHennessy/AI-Research/blob/a9bed3c57d915c04d07bb1fc4a1391c62e3e5823/docs/artificial-life/21-outlier-causal-selfhood-2026.md) and [ten independent tests](https://github.com/JeremyHennessy/AI-Research/blob/a9bed3c57d915c04d07bb1fc4a1391c62e3e5823/docs/artificial-life/23-unified-organism-evidence-standard.md) stress that repeated patterns, branching causal reproduction, functional heredity, endogenous maintenance, and open-ended evolution **must not be conflated**.

This is a new *read-only* audit of the previous separately designed AL02 virtual program ecology. Do not import past Ora project code, phase structures, benchmarks or troubleshooting history. Do not change AL01 or AL02 physics, parameters, event records, or prior summary. Prior reviewed original AL02 experiment: execution SHA `1322657ee5189c483aa12f04f14fc54c55100502`, [run 37783308992](https://github.com/JeremyHennessy/Ora2.0/actions/runs/37783308992), artifact `11553740402`; deterministic replay [run 37783986289](https://github.com/JeremyHennessy/Ora2.0/actions/runs/37783986289). All fields in the data remain source claims until independently cross-checked.

## Units, data, input identity

The unit is an AL02 simulated **world** (seed, variant), not a correlated frame/offspring. Inputs are the archived complete `worlds.jsonl`, `births.jsonl`, `events.jsonl` for all **64 seeds × 4 arms**. Do not select "successful" worlds. Confirm contents SHA256 against the fixed hashes in `docs/AL02-COPY-RESULTS.md`; abort if mismatched (or absent/extra worlds, births, events). Processing should not execute an organism or mutate any input. Comparators from the research library inform tests only, not a model rebuild.

## One-pass, time-indexed causal and material ledger

For each world, independently replay **only the logged evidence**, not the simulator code:
1. Require single `GENESIS` with matching founder tape and unique material-unit IDs.
2. Require event IDs contiguous from zero, ticks nondecreasing, and source/world ID pairs unambiguous.
3. `COPY_WRITE` requires a parent **alive at that event**, with current tape byte and material unit matching the reported source and author-supplied genetic hash, matching consecutive nursery index, recorded mutation flag and energy payment. No occupied material unit may be allocated again until actually released.
4. `BIRTH` requires exactly the **complete previously-written ordered nursery** of that parent (every byte unique and currently reserved), correct offspring tape hash, authentic parent ID and generation, unique child ID, and four transferred energy units. Only on this event may already-written nursery material become child tape material.
5. `DEATH` releases the deceased's tape and unfinished nursery material. Material reuse **after** death is legitimate; simultaneous tape/nursery reuse is a breach.
6. Every `COPY_WRITE` and `BIRTH` must correspond to the executing parent's `EXEC` opcode and outcome in the **same virtual tick**, and cannot occur after a parent has died.
7. Every reported `births.jsonl` certificate must match one and only one `BIRTH` event in `events.jsonl`; the independent audit must not trust the original embedded `audit` flag, a child's appearance, or a parent reference alone.
8. Cross-check per-world `birth_count`, `copy_events`, extinction/death counts and source-ledger residuals. World manifests remain immutable; this read-only analysis reports violations, rather than attempting repairs.

**Scope warning:** this tests internal consistency of a **trusted simulator's own event stream**, not a fully independent physical causal experiment. Event provenance can detect many forged/unrecorded births but cannot rule out all correlated simulator bugs. It is weaker than counterfactual necessary-cause tracing in spatial cellular automata.

## Frozen outcomes (no cherry-picked screen)

Primary: proportion of recorded births whose time-ordered, unique-material, byte-causal chain is valid; count invalid births, invalid worlds and reasons, across **all** variants. If the event stream is irreconcilable, mark `INVALID_EVALUATION` and show the discrepancy; never silently skip it.

Secondary, by arm and by world: complete generation-depth distributions, born-descendant fertility (individual with at least one verified child), parent with >=2 individually written sibling tapes, branching across >=2 *fertile* siblings, same-opcode transmitted mutation to grandchildren, extinct/persisting at horizon, survival time to death, and material reuse **only after release**. 64 identical deterministic control outcomes do not count as 64 statistical replications.

Separate graph-related categories:
- **mechanical descent:** parent-executed writes, valid new daughter tapes;
- **branching family:** parent with >=2 certified children;
- **multi-generation descent:** certified daughter itself produces a certified child;
- **independent siblings:** not claimed by this test, since offspring compete for material, energy and execution schedule and therefore may causally influence each other;
- **life/autopoiesis, self-produced body, adaptive intelligence and OEE:** not assessable from these logs.

No composite life score or science-first novelty badge.

## Negative and adversarial controls (development fixtures, not altered source data)

Build small fixtures from AL02 **development-only** world seeds (0–7) and inject:
- `BIRTH` event without authentic prior COPY receipts;
- swapped `parent_id` (even when genome strings match);
- alive parent resurrected after DEATH or child created before parent exists;
- duplicate child ID, duplicated active `material_unit`, or copy index out of order;
- use of a released material unit (legal) versus reuse before release (invalid);
- deleted/duplicated/nonmonotonic event ID;
- `COPY_WRITE` followed by non-COPY `EXEC`, and a BIRTH followed by non-DIVIDE `EXEC`;
- false depth, missing old source tape, and fabricated `births.jsonl` row.

Auditor must reject invalid structures with a specific error code; legal release/reuse must not be rejected. Do not modify AL02 simulator to make tests pass.

## Reproducibility and validation

Implement new standard-library-only `experiments/causal_genealogy_audit.py` and new unit tests, reading CSV/JSONL as inert data; no source-code execution of input, no mutation of simulator, no external network, no database. Run on a restricted workflow using the fixed source, with a **separately generated replay** of the previously frozen AL02 protocol if direct artifact reuse is impractical; compare raw hashes against archived first-run receipts **before** the analytic step. Archive raw audit output + counterexample test results, all hashes and source commit. Full sets rather than cherry-picked positives.

**Authorizations:** The experimental project Ora2.0 is authorized for sandboxed research work. The separately managed AI-Research library remains research-only and MUST NOT be modified by this work.

## Stop rules

If archived hashes disagree or material conservation / birth causality cannot be reconciled, **do not declare success or change the old AL02 run**. Record the exact first discrepancy and require a bounded follow-up. Only after a valid audit should a new preregistered AL03 ecological mechanism be considered. New papers after this date can inform *new* protocols but cannot change these predeclared rules.
