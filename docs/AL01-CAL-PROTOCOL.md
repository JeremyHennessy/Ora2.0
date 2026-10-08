# AL01-CAL — Frozen preregistration for chemical feedback measurement calibration

**Status:** preregistered design before outcome evaluation, 2026-10-08. **Not** an artificial organism experiment, research replication, or discovery of spontaneous metabolism. The protocol is defined in this standalone Ora2.0 project, not inherited from any earlier Ora architecture.

## Question / mechanistic hypothesis

Can our test harness correctly detect that persistence/recovery of vulnerable constituents depends on an **internally executed reaction route** and availability of an external chemical-like feedstock, rather than hidden simulator respawn?

This is an **engineering-calibration positive control**, not evidence that the chemistry evolved, assembled spontaneously, or has a living boundary.

## Specified toy substrate

A closed, well-mixed reactor with integer molecules: nutrient S, two functional constituents A and B, inert waste W.

Reactions (designed in advance):
- S + A → A + B (A catalyzes production of B).
- S + B → B + A (B catalyzes production of A).
- A → W and B → W (independent spontaneous constituent decay).

Each reaction conserves molecule count inside the reactor. A nonphysical externally supplied nutrient flow adds 4 S per step in fed variants. There is **no genome**, cell membrane, agent, task reward, neural network, mutation, intentional behavior, or externally protected lifespan.

Reaction Monte Carlo: at each step, add nutrient, then make 6 reaction-encounter attempts. In each attempt with S>0 assign weights 1 (no reaction), 0.08*A for the A→B catalytic route and 0.08*B for B→A. Draw proportionally and immediately update the species counters. After reaction attempts, visit each A and B molecule once; decay independently with probability 0.10, converting it to W. The explicitly authored finite update rule is not meant to be chemical realism; no claim of physical kinetics or free-energy accounting.

Initial counts S=35, A=10, B=10, W=0. No spontaneous origin of this catalytic arrangement is being tested.

## Matched paired design

1. Use Python standard-library deterministic PRNG per world seed.
2. Run 40 pre-intervention steps with **both** reactions enabled, 4 S supplied per step.
3. Clone **the same state and the same PRNG state** into all variants.
4. Intervene just once: convert floor(0.75*A) units of A and floor(0.35*B) units of B to W, identically in all variants (no scripted replenishment or respawn).
5. Run 60 post-intervention steps with conditions:
   - **intact**: both catalysts active, 4 S supplied.
   - **feedback-knockout**: B→A reaction disabled, A→B enabled, 4 S supplied.
   - **inert**: both catalytic reactions disabled, 4 S supplied.
   - **starved**: both catalysts enabled, 0 S supplied, and transfer remaining S to W at intervention (resource denial).
6. The same base world seed and initial-state random stream are held across conditions; conditions may naturally diverge in later random consumption.

## Outcomes specified before evaluation

**Primary:** *sustained recovery*. For each world, mark recovered only if **both** A and B return to at least 75% of their respective **pre-damage** counts for **five consecutive steps** within the 60-step post-intervention observation horizon.

The primary paired comparison is the fraction recovered in **intact** minus **feedback-knockout**. Also report absolute fractions for all four conditions and paired discordant world counts (not just percentages).

**Secondary:** first sustained recovery time, final A/B, total catalytic conversions, total decay events, observed nonzero turnover, and maximum absolute molecule ledger discrepancy (expected total = initial total + cumulative supplied molecules; interventions only convert A/B/S into W). Count complete dropouts/extinctions and any world where pre-damage A or B is zero, without filtering them out.

**Uncertainty:** 32 independent held-out seed worlds 1000–1031; descriptive paired effect and percentile paired-world bootstrap interval (fixed analysis seed 424242, 5,000 resamples). This is **not** a pre-powered confirmatory statistical study.

**Development smoke seeds:** 0–7, used only to check invariants and output schema. Do not optimize model parameters to maximize held-out outcomes. The first held-out result will be preserved even if null or contrary.

**Run command:** `python -m experiments.chemical_calibration --output-dir runs/al01-cal` after implementation. Output summary (JSON) and run-level audit records (JSONL). No network calls, GPU, arbitrary code execution, or service deployment.

## Failure / falsifiers

- **Invalid experiment:** any ledger mismatch, nondeterministic replay, unequal initial post-damage states, missing run record, or mutation of source state across conditions.
- **Pipeline did not discriminate:** intact does not exceed feedback-knockout in sustained recovery. Preserve result, do not silently tune rates; interpret possibility that intervention harms kinetics, setup is poorly identified, or assay lacks power.
- **Conservation-only illusion:** inert state appears to recover damaged constituent numbers through an unrecorded rescue.
- **Resource-coupling failure:** starved variant recovers under zero usable S; investigate implementation instead of claiming autonomy.
- **Ambiguous:** effects unstable across seeds or depend on floor thresholds; report fragility and plan separate sensitivity study.

## What an observed success does **not** establish

The cycle was deliberately authored; A and B were deliberately seeded; the functional test directly mirrors the authored topology. Therefore success would be a sanity check on the causal assay **only**, not origin-of-life, autonomous organism maintenance, self-assembly, heredity, open-ended evolution, cognition or a new AI.

## Next scientific experiments, separate authorization of implementation decisions

- AL01-DISCOVERY: randomly generated, mass-conserving reaction networks, no handpicked viable topology, inclusion of all extinct/failed worlds, ablation of discovered internal feedback vs randomly matched edges.
- AL02-LINEAGE: independently constructed instruction ecology with actual self-copying program steps and mutation, lineage fidelity vs shuffled/descent-ablated controls.
- AL07-IDENTITY: passive attractor and oscillatory controls vs intervention-sensitive process identity.
- Only after results: spatial boundary conditions, richer chemistry, multi-resource ecology, within-life learning. No LLM by default.

## Reproducibility boundary

Freeze this protocol in Git history **before** producing held-out result records. Report source commit, Python version, environment, exit status, seed list, output hashes and any deviations. Simulation/checkpoint artifacts remain outside this public Git repository by default.
