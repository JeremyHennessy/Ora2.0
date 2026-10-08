# CLOSURE-02 — precommitted bounded boundary-function protocol

**2026-10-08; frozen proposal stage; unexecuted.** This protocol is to be committed before implementation and before any held-out world is opened. Review is required before local execution. No result, organismhood or physically validated membrane claim is made.

## Decision and source anchors

CLOSURE-01 reported 37/93 intact core recoveries versus 79/93 with M synthesis suppressed, and 27/93 dual recoveries in both intact and permeability-null arms. Suppression changes substrate allocation as well as material production. That result motivates a cost-controlled falsification test, not tuning until shells succeed.

Base source: Ora2.0 `205e0030de07986ef4244f38f01890bdf62d5a10`. Reference modules and historical output must remain unchanged. AI-Research inspected at `63914404809d799923832f83b0b2dc0ae6cb8bc3`; its pass-8 rubric separates boundary origin, resource accounting, blind function, shortcuts and generalization. This is an authored toy transport law, not a reproduction of a specific physical protocell paper. Literature analogies confer no physical validity or implementation license.

## Frozen scope and panel

- New module only: planned `experiments/closure_cost_control.py`, with separate tests and analyzer. No modifications to legacy Ora or previous experiment modules/data.
- Dev-only seeds 7000..7007. Held-out seeds **7200..7235**, 36 independent seed groups. Do not run held-out seeds during development.
- Three origins: clustered, dispersed, nutrient_only. Nutrient-only retains the authored basal activation channel.
- Use all exact CLOSURE-01 Protocol defaults from the base revision: 9x9 torus; 60 warmup and 60 post-damage steps; 8 S inflow per step; two weighted attempts per site; all rates, damage fractions and recovery thresholds unchanged.
- Warmup, target selection (densest 3x3, row-major tie break) and damage use the base law. Select the target once before treatment. Eligibility for C02 uses **pre-damage A >=4 and R >=4 only**; M coverage is descriptive and cannot determine eligibility.
- Apply 55% integer-floor A/R damage in the core and 65% integer-floor M damage on its eight neighbors. Branch all arms from the same post-damage state and PRNG state. Preserve a canonical checkpoint hash.
- Separate starting-M control: each checkpoint additionally produces a permutation stratum. After damage, uniformly Fisher-Yates shuffle the 81 M counts using independent PRNG seed `seed*100+origin_index+20261008`; preserve total M and every other species. All arms in that stratum share the same permutation and original simulation PRNG state. Report native and shuffled strata separately; the native stratum is primary.
- Primary panel: 36*3*2*5 = **1080 arm runs**, **64800** post-step traces. No extra seeds to replace failures or ineligible worlds.

## Five interventions

| Arm | Shell channel product | S debit per executed shell event | M-dependent A/R transport |
| --- | --- | --- | --- |
| shell_effect | M at sampled neighbor | 1 | enabled |
| shell_null | M at sampled neighbor | 1 | disabled |
| ghost_effect | inert W at sampled neighbor | 1 | enabled for remaining initial M |
| ghost_null | inert W at sampled neighbor | 1 | disabled |
| no_shell_no_cost | channels disabled | 0 | disabled |

Ghost reactions preserve channel weights, catalyst, neighbor draw and one-S-to-one-product conservation. W is inert, immobile and has no transport effect. Ghost formation has its own counter and must not increment M synthesis. Initial M decays normally in both ghost arms. No inserted free shell or host repair.

**Matching limit:** shell and ghost have the same cost per executed event and the same initial reaction opportunities. Their trajectories may diverge, so cumulative costs are not guaranteed equal. Record actual costs; do not call the five-arm comparison an exactly equal-total-cost intervention. No post hoc cost matching, successful-world selection or conditioning on endpoint cost.

## Flux and cost counters

Instrument every synchronous A/R transport attempt against the fixed core perimeter. An opportunity is a molecule whose sampled neighbor lies across the perimeter **before acceptance**. Count outward and inward opportunities separately, and accepted crossings separately for A and R. No within-core moves enter a crossing denominator; do not substitute all moves.

For each attempted crossing also sum the two analytic acceptance probabilities on that **same source/target M snapshot**: effect-on `0.24/(1+0.8*(M_source+M_target))` and effect-off `0.24`. This standardized kernel diagnostic isolates the installed law at identical opportunities; it is not independent evidence of emergent membrane function and does not modify the world or consume PRNG draws.

Per step record:
- outward/inward A/R opportunities, accepted crossings, probability sums;
- S consumption by basal, A/R synthesis and M/ghost channels separately;
- new A, new R, M, ghost W, decay, external inflow and damage;
- full mass ledger, local core A/R and fixed-region thresholds.

Aggregate accepted outward/opportunities and inward/opportunities over 60 steps. Net outward flux = outward accepted minus inward accepted; retain raw units and denominators. Zero denominator means **undefined**, never zero escape. Work yield = (new catalytic A + R, excluding basal births)/(all S consumed in post-damage reactions including basal and shell/ghost); zero S means undefined. Report local and global catalyst synthesis separately; primary yield is global.

## Endpoints and prespecified analysis

Core recovery uses >=70% of pre-damage A and R for >=3 consecutive post-damage steps, independently of M or shell appearance. Retain raw recovery and require at least one post-damage catalytic A synthesis **and** one R synthesis for the active-repair classification. This is an activity guard, not evidence of life.

Primary native-stratum contrasts:
1. shell_effect minus shell_null in active-repair recovery rate;
2. shell_null minus shell_effect in outward escape probability (benefit positive).

Secondary: shell_effect vs ghost_effect in recovery and work yield; ghost_effect vs ghost_null to isolate retained initial M; shell_null vs ghost_null; no_shell_no_cost as an unmatched-cost reference. Report inward flux, net flux and realized cost differences alongside outward escape. Shuffled-M stratum is a prespecified robustness test, not a replacement primary analysis.

Unit of uncertainty is the **36 source seeds**, keeping origins and all arms/strata together. Compute per-seed mean paired differences over eligible origins. For escape use only paired defined rates and report excluded denominators explicitly. Bootstrap 4000 draws of seed groups with replacement, random seed 20261008; report sorted draw indices floor(0.025*(3999)) and floor(0.975*(3999)). Report per-origin counts and effects as well as pooled estimates. Frames are not independent replicates.

Interpretation order:
1. **Invalid simulation:** any nonzero mass residual, negative count, missing/duplicate record, unequal branch/damage identity, checksum failure, unexplained event debit or engine-created repair. Stop; retain artifacts. No scientific verdict.
2. **Insufficient evidence:** fewer than 24 independent eligible seed groups for recovery or fewer than 24 paired-defined groups for escape. Retain all worlds; no reruns to top up.
3. **Positive bounded function:** both primary benefit intervals have lower bounds strictly above zero, and shuffled-stratum point estimates have the same signs. This supports useful function of the installed transport law at fixed per-event costs only. Differences in actual total cost must be disclosed.
4. **Negative:** either primary interval has upper bound strictly below zero. The current law is harmful on that endpoint under tested conditions.
5. **Null/inconclusive:** all other valid outcomes, including contradictory or stratum-dependent effects. Retire this law from the next organism candidate; do not tune it on these seeds. A new substrate or materially new law requires a new protocol and seed panel.

Exactly equal-total-resource causal benefit remains **unestablished** by this panel. Any follow-up budget-yoked design requires a separate precommit; normalization alone cannot establish it. Identity, lineage, heredity, selection and repair-of-repair remain unmeasured.

## Adversarial acceptance before held-out execution

Dev seeds and deterministic hand fixtures only:
- A one-molecule crossing fixture verifies both perimeter directions, zero denominators and periodic edges.
- A forced shell-channel fixture proves equal S debit and neighbor placement in M/W variants, with identical random draw consumption for that event.
- Permeability-null fixture verifies probability 0.24 regardless of M, and standardized effect-on probability uses both endpoints.
- Passive M pocket with no catalytic birth cannot receive active-repair success even if raw counts meet threshold. A passive boundary can reduce leakage; leakage alone is not a positive verdict.
- Externally healed fixture is rejected by the mass/event ledger even if endpoint thresholds pass.
- Disabling M production and catalytic channels on a passive M-lattice fixture is an explicitly supplied-compartment diagnostic, outside primary worlds; never pool it as endogenous repair.
- Paired post-damage state and PRNG identity, M-permutation conservation, event debits, complete grids, finite horizon and no live parameter mutation are checked.
- Analyzer rejects duplicate/missing combinations, unequal provenance, truncated traces and checksum corruption.
- Dev repeat execution is byte-identical on the same pinned Python/source; prior regression suite passes with original source bytes unchanged.

## Manual local handoff and preservation

After operator review, implement and test on a separate source branch. Commit simulator, tests and analyzer before opening held-out seeds. Record this protocol's commit/blob hash, exact execution revision, Python version, parameters, seeds and per-file SHA256 in the run manifest. A protocol change before execution requires a dated amendment; after execution it defines a new study.

Use the existing local Python environment and manual laboratory safeguards. Keep source snapshots and runs on D:, in a fresh run directory that rejects existing output. Apply the existing lock, minimum free-space check and per-command 300-second timeout. If the complete panel exceeds that limit, retain the failed attempt and amend a deterministic chunking/merge plan **before** any further held-out execution; never silently widen the budget.

Preserve all eligible/ineligible/extinct/failed worlds, step traces, analyzer output, stderr, exit codes and immutable source identity. Verify exact dev replay, then complete the held-out panel once; independently verify manifest and archive restoration on a test copy. Same-drive restoration is not off-drive backup.

No continuous runtime, checkpoint integration, scheduled worker, new Actions workflow, self-hosted runner, paid compute or external API. Source retrieval is manual; incoming commits are never automatically executed. This stage freezes the study; implementation and scientific results remain pending.
