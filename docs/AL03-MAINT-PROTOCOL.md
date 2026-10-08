# AL03-MAINT — Frozen maintenance-cost stress test (2026-10-08)

**Status at initial commit:** preregistered before any AL03-MAINT held-out run. This is a new counterfactual study, **not** an alteration or correction of AL03-NICHE's approved code/results. No claim of digital life, endogenous self-maintenance, intelligence or scientific priority.

## Why this study exists

The already verified AL03-NICHE study showed transient multi-generation B-resource use, but **every one of its 192 externally fed worlds ended at the engine's population cap of 40**. Read-only, **post-hoc** analysis of the full `al03-niche-complete` original `traces.jsonl` showed that the cap was occupied for approximately 71.0% (sink), 75.9% (heritable), 72.7% (mutation disabled), and 74.6% (nonheritable) of observed steps. All 48 no-inflow worlds were extinct. This is descriptive evidence that a full population and programmed supply may masquerade as stable ecology.

The original AL03 physics debits energy only when a creature is scheduled to act, so a crowd of idle entities can hold stored energy until each receives a turn. The following test asks how *that specific survival result* changes when independently priced **idle maintenance** is imposed, without rewriting the source module.

## Literature boundary and scientific baseline

At design checkpoint, `AI-Research` last **confirmed green** at `b3a6180f16c34f022d3501e22da0f25e9e8bb8da` (GitHub Actions `37789602577`) and introduced original technical comparisons of Stringmol, Physis and maintenance/selection failure mechanisms. A later source revision `1b8301238c4ead2197e10f7f11580aa6317368cc` was **in-progress** when observed and must not automatically be called verified. No code or experimental design from the original Ora/AgentTest is used.

This protocol investigates a **simulation measurement confound**, not a replication of any research paper. A continual maintenance debit is also a *designer-assigned law*, not a life-like metabolic process.

## Retained physics and one independent intervention

Keep the original `experiments/niche_selection.py` interpreter, P/C roles, reaction potentials, scheduler, reproduction threshold, exact birth/role mutation probabilities, population limit 40, starting A=18, original energy and 480 tick horizon **unchanged**. Use the same source file via import. Absolutely **do not change** the earlier module, data artifacts, prior protocols or visual presentation.

**New rule (only in new module):** after each complete original ecology tick, at fixed calendar intervals `k` (k=8, 4, or 1), **every currently living entity**, including newborns created that tick, pays exactly 1 unit of its internal energy as heat. If this reduces its energy to 0, it dies immediately under the original material release semantics. A virtual world at time 480 does not gain credit for being alive merely because a human stopped simulation; record exact observed time. A dead world receives no new resources/actions afterwards, as in the original. This maintenance rule has no ability to execute host programs and no birth/rescue function.

At each charge event:
- Process living entities in ascending numeric ID order; one `UPKEEP` event per paid energy unit with entity, tick, before/after energy and amount 1. This is fully auditable even for idle entities.
- If an entity dies, record its normal `DEATH` (energy already 0), release material, and do **not** secretly reuse state.
- Apply energy conservation check: `20*A + 8*B + Σliving.energy + heat = (20*initial_A + founder_energy) + 20*cumulative_A_supply`, unchanged.
- Apply mass conservation check: `A+B+W = initial_A + cumulative_A_supply`.
- Verify that the step trace reports the *post-upkeep* population, heat and energy residual—not the pre-upkeep count.
- No copying of the original AL03 source or new behavior intended to maximize survival.

**Scientific qualification:** because external A input supplies only 20 units every 3 ticks, high upkeep rates can be energetically unsustainable for a 40-entity population *by construction*. A negative result is therefore evidence of **the baseline's sensitivity to idle costs**, not a discovery of a universal biological maintenance threshold.

## Frozen arms and sample

**Held-out network-free world seeds:** exactly 48 new seeds `8500..8547`, one deterministic simulation for each seed and arm; all outcomes retained.

Five arms:
1. `baseline`: **unaltered AL03 heritable ecology** (no idle energy costs; every third tick adds A).
2. `upkeep_8`: heritable ecology plus maintenance 1 energy per entity each 8th tick, external A supply unchanged.
3. `upkeep_4`: same maintenance every 4th tick.
4. `upkeep_1`: same maintenance every tick.
5. `upkeep_8_no_inflow`: every 8th tick cost, **no periodic A supply**.

Treatments begin from identical genesis for each seed and use same initial PRNG stream, although intervention effects subsequently change the use of that stream and population.

**Development-only** tests use seeds 0..7 and may test conservation, no-op control and formatting; they must not modify k schedules, study seeds, thresholds or horizon on the basis of their outcomes.

## Precommitted outcomes

**Primary diagnostic:** fraction of each 48-world arm with `population > 0` at tick 480; paired difference vs baseline for upkeep arms. A world that became extinct before tick 480 counts as **not persistent**. Report paired discordance and **4,000 fixed-seed (20261008) paired-world bootstrap resamples** with 95% percentile intervals. Some treatments may be deterministic across these 48 seeds, so do not overclaim statistical independence.

**Secondary (separate, not a composite life score):**
- Mean and median final population, count at the 40-unit cap, mean share of total observed ticks with exactly 40 entities, cap time across all worlds, and first saturation step.
- Exact energy spent on upkeep, number of distinct entities dying as a direct consequence, total deaths, births, temporary B-resource lineages and any role dependence.
- Food A supplied/consumed and B generated/consumed, initial/final potential and heat; mass and energy residuals must be 0 for **every trace event**.
- Extinction tick/horizon censoring and material slot ownership, no silent retry.
- Report all 240 treatment worlds and complete step/event traces with source hashes, not a selection of surviving worlds.

**Invalid study:** incorrect ledger, duplication of material slot, error in old and new trace alignment, incomplete arms/seeds, or inconsistent event/step count. Abort on an invalid world, retain the failure and do not claim ecological evidence.

**Negative science is useful:** if even small upkeep destroys persistent populations, quantify fragility; if moderately priced maintenance allows persistence, document dependency on continual external resources and 40-slot cap. Neither proves self-maintenance.

## Execution / preservation

Write only a **new** `experiments/maintenance_stress.py` with independent tests and workflow. Use Python standard library; no LLMs, API keys, GPU, external runtime, local computer or network privileges. Use an isolated branch from approved Ora2.0 main `3f0483db08ada43d06f032811e8f2fa52060ade2`.

After tests and before interpretation, run

```bash
python -W error::ResourceWarning -m unittest discover -s tests -v
python -W error::ResourceWarning -m experiments.maintenance_stress --seeds 8500:8548 --output-dir runs/al03-maint --source-revision <exact_sha>
```

Compare results with precommitted outcomes, explicitly retain all failed/successful worlds, archive source revision and full JSONL/summary SHA-256 receipts. No observed positive outcome upgrades this research program to a "living digital organism" claim.
