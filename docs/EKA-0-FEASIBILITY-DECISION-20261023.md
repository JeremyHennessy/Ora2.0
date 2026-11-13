# EKA-0: native evolutionary learning feasibility

**23 October 2026 — UNKNOWN for the present substrate; NO-GO for a new EKA population now.**

This is the source/evidence leg of [Ora issue #313](https://github.com/JeremyHennessy/Ora2.0/issues/313), paired with the [independent AI-Research assessment](https://github.com/JeremyHennessy/AI-Research/blob/research/eka0-independent-audit-20261023/docs/artificial-life/EKA-0-INDEPENDENT-CRITIQUE-20261023.md). It follows the merged [strategy](ENDOGENOUS-LEARNING-EVOLUTION-STRATEGY-20261023.md). No VM, founder, mutation rule, ecology, seed bank, runtime or scientific acceptance changed. No new World or seed query ran.

The primitives are accessible: naturally generated offspring in the closed Pressure71 histories actually executed feedback, memory and SELFWRITE instructions. But neither a viable route to **useful** inherited information processing nor its fully paid advantage is established. That missing argument does not prove the VM incapable. Do not spend a new population bank, insert a successful genotype, enlarge a horizon or build a supplied learner to conceal it.

## Exact scope and evidence

Reviewed current remote main `3a3c7e8` and ongoing implementation branches, rather than integrating the divergent local main. The mechanism audit uses the retained Pressure71 scientific export at `61cd33d252a79d0d8769a11c4340be7e99c85c29`, source manifest `acda4eab060265e78addb70f4aa2d3390fc81fa0d9580799e4c79c2d12dd328d`. Exact source and closed input hashes accompany the [machine-readable audit](../data/eka0-feasibility-audit-20261023.json). Relevant current-main mechanism ASTs agree with those historical files; byte differences from checkout line endings are not represented as exact byte identity.

| Closed evidence | What it established | What remains absent |
| --- | --- | --- |
| Longitudinal01, interpretation v2 | Two supplied, mutation-disabled histories; 35 paid births and eight generations each; descendants continue after founder expiry. | Natural selection improving information use. |
| Pressure71, complete independent interpretation | All 40 populations and registered family comparisons retained; no replicated functional/selection or pressure-alleviation acceptance. One changed child's extra food did not establish replicated selection. | A mutation-origin information strategy with inherited competitive benefit. |
| Learning81, independent closed interpretation | Supplied machinery uses personally acquired cues; registered choice acceptance passes. | Retained energy superiority: 480 loses to compact references at 664/661. No births in that assay. |
| Inheritance83, closed negative interpretation | Paid capacity-header variation, births and some changed functional descendants. | Beneficial selection fails its registered tests; only capacity 2/4/8 was inherited, not an invented learner. |
| Context90, crossed primary interpretation | Supplied q8 machinery passes its own-old-history retrieval criterion. | q2/q4 functional flags and every nominal/operating/formation-inclusive paid advantage fail; no evolved updater. |

Local receipts read: `reports/longitudinal01-engineering-v2-interpretation-v2.json`, `pressure71-independent-interpretation-v1.json`, `learning81-independent-closed-v1.json`, `inheritance83-closed-negative-interpretation-v1.json`, and `context90-crossed-primary-interpretation-v1-20261017.md`. This review does not change their criteria or rescore them. All unexposed, dead and incomplete outcomes remain in their original denominators. Context90's 684 originals include 252 deaths; q8's functional result is not permission to select q8 founders for EKA.

## Mechanisms, reachability and costs

| Mechanism | Source-backed affordance/bound | Scientific limitation |
| --- | --- | --- |
| Program | Mobile54 supplied ancestor has nine instruction triples, 27 words. COPY preserves length; ordinary mutation substitutes values, never inserts/deletes words. | The generic validator permits other lengths, but that does not make them reachable from this founder. |
| Mutation | Pressure71 COPY changes each selected word by a nonzero offset modulo 32 at dose 1 or 8. Each complete child requires 27 paid writes. | Hash draws are deterministic; dispatches, partial nurseries and dead mutants are not successful variant births. |
| Feedback and private state | Opcodes 1/2/3 read feedback/read memory/write memory; eight 4-bit cells and two 4-bit registers. Every dispatch costs one energy unit. | READ/WRITE addresses are instruction immediates modulo 8, not free register-indexed tables. Feedback also conflates empty-site attempts with failure. |
| SELFWRITE | Opcode 9 writes a register value to a fixed code address. Registers are 0–15, so it cannot directly write all 32 possible code-word values. | Rewriting an opcode is not learning. A write must precede the relevant COPY; copying was already paid when a nursery word was made. |
| Inheritance | COPY takes the parent's current source word at that copy time. Division creates blank memory/registers/feedback/inbox and PC 0, with 12 energy. | Private experience does not automatically transfer. Acquired code content, inherited learning code and fixed genetic adaptation are different claims. |
| Reproduction | At least nine COPY dispatches, 27 extra copy-energy units, one division dispatch and 30 extra division-energy units: 67 parent energy units, of which 55 become heat and 12 transfer to the child. | This excludes foraging, sensing, movement, waiting and failed attempts. Starting from 12 requires at least 55 net energy input before other costs. Three 20-unit captures are a lower bound only without incoming neighbour transfers; transfers must be charged to donors and cannot be silently treated as free food. Cap heat can increase the requirement. |
| Material/time | Each mature fixed-length body uses 27+16=43 material units; 512 units permit at most 11 such bodies before nursery reservations. Expiry is 256 own turns. | Configured population cap 32 is not 32 affordable bodies. Global time, personal turns and informative encounters differ. |

There are 837 syntactic one-word substitutions from the ancestor (27×31). Thirty-six substitute one of the nine opcodes with feedback/READ/WRITE/SELFWRITE. This establishes direct instruction accessibility, not survival or useful data flow. No viable adaptive genotype or viable sequence of neutral intermediates has been supplied by this audit.

Under an explicitly hypothetical uniform, independent 64-bit hash model, the chance of **one particular specified replacement and no other changes** is approximately 0.000248 at dose 1 and 0.000295 at dose 8. Two specified replacements with no other changes give approximately 8.09×10^-8 and 8.28×10^-7. These are route-specific calculations, not probabilities of any useful phenotype or future statistical power. Alternate genotypes, neutral paths, selection and deterministic seed correlations prevent that inference. Higher mutation supply also disrupts the reproductive program; it is not a free improvement.

## New read-only check of closed histories

The [reader](../tools/eka0_closed_census.py) imports only standard-library data/arithmetic code. It reads all 16 natural `mutating/parent_copy` populations in the already-closed Pressure71 cohort, authenticates raw receipts/source/configuration hashes, hashes the duplicate export, checks native closure, and reconciles births, deaths, copy words and mutations with the prior complete interpretation. It invokes no producer, VM, referee, sampler or scientific endpoint.

| All eight closed populations per dose | Dose 1 | Dose 8 |
| --- | ---: | ---: |
| Paid births | 176 | 188 |
| Paid copy words, including unfinished nurseries | 6,633 | 6,861 |
| Mutated copy words | 56 | 556 |
| Newborns encoding an information opcode | 3 | 27 |
| Newborns executing one | 3 | 26 |
| Newborns executing feedback / memory READ / memory WRITE / SELFWRITE | 0 / 0 / 3 / 0 | 8 / 6 / 12 / 10 |
| Effective value-changing SELFWRITE dispatches | 0 | 37 |
| Actors with a later birth after SELFWRITE | 0 | 4 |
| Paid newborns carrying an exact copied, previously self-written word | 0 | 0 |

No actor or seed was selected for inclusion based on these outcomes. The cohort contains 364 births plus 16 supplied founders, not 380 independent samples. The information-opcode actor sets overlap. Some writers reproduce, but the trace predicate found no self-written word carried into a paid newborn: copying order matters. A same-value write or an opcode occurrence is not personally acquired knowledge. Temporal co-occurrence is not causal usefulness. Zero observed chains does not prove no future chain is possible. The previous frozen selection failure remains unchanged.

## Smallest useful question and fair alternatives

Ask whether a mutation-origin, feedback-dependent port routine can save enough failed attempts to cover its own instructions and copying costs, survive ordinary reproduction, and give blank-state descendants useful reacquisition ability on unseen site assignments. Do not initially demand simultaneous culture, self-rewrite and open-ended learning.

The present ecology has hidden site/port assignments and a change at global tick 2048. A candidate information-lifetime contrast is revisiting a site after another site's feedback has overwritten the last-feedback channel. Different earlier site experience could then recommend different ports despite the same present location and last feedback. **A pair of legal, affordable, reachable histories before expiry has not yet been established.** Do not treat that verbal example as a qualified task.

References must include the actual blind alternating ancestor, both unselected fixed-port strategies, and the cheapest legal last-feedback/one-bit finite-state strategy. Pay their real dispatch/material/copy costs. A posthoc best fixed policy is not a fair competitor; a target-knowing oracle is only an upper ceiling. A single additional successful capture can nominally offer 20 units, but the 64-energy cap and reproduction timing determine retained benefit. No positive retained-benefit lower bound has been shown for an accessible learner. Learning81/Context90 prohibit assuming one from decision accuracy.

An EKA-1 proposal is therefore **conditional and unadmitted**, not frozen for execution. It would require a source-qualified viable path, informative paired histories, fully paid reference/candidate bounds and independently justified sample/effect/budget choices first. Then freeze mutation versus no-mutation, cost-matched inherited versus blocked, intact versus erased personal information, and mechanism-specific effective SELFWRITE/sham lesions if that mechanism is claimed. A lesion that also destroys reproduction or changes resources is not a clean learning test. Include every birth, death, unexposed and incomplete copy. Separate fixed inherited answers from inherited ability to acquire new answers; require independent origins and reserved-context causal tests without transplanting learned state.

## Decision, substrate alternatives and next action

**UNKNOWN**, because instruction accessibility is demonstrated but viable mutational paths, sufficient information opportunity and positive paid descendant value are not bounded. **NO-GO for population execution now.** A known absence of information or an upper benefit bound below unavoidable costs would justify a narrower candidate NO-GO; current evidence does not justify rejecting the whole VM.

Do not replace the substrate yet. If the nine-slot genome or literal-addressing bottleneck is proved decisive, compare one minimal alternative (for example, a smaller compositional opcode set or separately priced variable-length genome) under matched information and resource budgets. Each would change mutational neighbourhood, formation and copying costs and require a new contract. A neural substrate, larger memory or Flow-Lenia is not automatically a better answer.

The highest-value next action is a separately reviewed **zero-World feasibility certificate** for one cheapest feedback-dependent strategy: exact legal history contrast, viable mutation path including intermediates, complete cost accounting and strong cheap references. It must be a possibility witness only, never seeded into a scientific population or described as evolved. If that certificate cannot be obtained within a prospectively bounded source-analysis budget, publish the narrow NO-GO/UNKNOWN rather than launching a search.

PILOT74 remains separate: v3 completed 25 roles and all 34,816 VM steps, then failed publication's legacy lock-body check. All 29 process identities closed and partial archive/restore matched. Publisher correction `16a9090` passed independent review and focused Windows CI (14 tests, 70 pins), but has not run a new qualification. Full publication qualification, the native exception/natural-hour deadline custody panel, five production gates and a fresh reviewed production-owner route remain held. Ora's local assistant keeps running; neither its uptime nor approved memory is evolved organism intelligence.

No stage is promoted by this review: substrate and paid reproduction are implemented/tested; finite lineage continuity is observed; scoped supplied within-life learning has prior evidence; beneficial evolved hereditary learning, a running persistent scientific world, cumulative culture and emergent intelligence are **not yet proven**.
