# Next research experiments — independent, falsifiable and substrate-neutral

**Planning status:** not run, not an authorization to claim digital life. Scientific premises from independent artificial-life publications and the [AI-Research ALife atlas](https://github.com/JeremyHennessy/AI-Research/tree/52161ce4ce08208232621845f3f08424f3adbc35/docs/artificial-life).

The completed [AL01-CAL](RESULT-AL01-CAL-2026-10-08.md) demonstrates the apparatus detects a **designed** catalytic cycle. The next tests must remove that scientific shortcut.

## Priority A — AL01-DISCOVERY: non-handpicked chemical feedback

**Research question:** how frequently do randomly generated, resource-conserving, local catalytic reaction networks produce repeatable resource-funded **recovery under disturbance**, and is any recovery causally dependent on the network's internal reaction structure?

**Change from calibration:** the experimenter must not hand-pick a successful feedback graph or organism precursor. Sample reaction networks from a fixed, published distribution independently of outcomes. Pre-register entire sample size, seeds, rate distributions, and all controls before inspecting results.

Candidate bounded model (design choices to freeze in a separate protocol): 4–8 distinct constituent species, 1–2 externally supplied precursor species, discrete stochastic mass-conserving reaction templates, decay to inert waste, generated catalyst-product graph. Define rules and supply as properties of the *environment*, with NO externally administered living-state reward or repair call.

**Essential variants**
- Original sampled network under normal inflow, matched disturbance, and resource denial.
- Reaction-edge knockout chosen by a **predeclared graph rule** blind to survival outcomes (avoid destroying the strongest edge post hoc).
- Scrambled-reaction control preserving species count, reaction count, and where feasible degree/molecular accounting.
- Inert/null chemistry with equivalent substrate feed and decays.
- Report **all sampled networks**, including immediate extinction and inert stability.

**Candidate independent endpoints**
- Preregistered minimum constituent/process persistence despite molecular turnover.
- Recovery after **untrained** perturbation; direct restoration via network flux, no rescue callback.
- Rate of feedback-linked positive outcomes across **all** candidate universes, uncertainty across independent network seeds and stochastic trajectory seeds.
- Sensitivity to energy/material supply, decay rate and topology.
- Difference between mathematical attractor and causal organized persistence.

**Falsifiers/risks:** positives vanish under topology-neutral null or outcome-blind knockout; no recovery outside a narrow hand-tuned configuration; supposed energy availability is unrelated to reaction chemistry; any observable "recovery" is caused by resource injection or the engine preserving a population. Good negative results should be retained, not masked through tuning.

**Important limitation:** even a positive AL01-DISCOVERY would establish **interesting in-silico chemical feedback**, not spontaneous life or a true organism, unless endogenous boundaries, individuality, heredity and wider organization are separately established.

**Before coding:** write exact generative distribution, preselect graph intervention algorithm, fix base rates and resource budgets based only on a development subset, define holdout and stopping rules, and code invariant/null tests. Archive protocol as a commit before evaluating holdout.

## Priority B — AL02-LINEAGE: executable heredity without cognitive rewards

**Distinct scientific question:** can a bounded virtual machine with executed copying instructions yield measurable intergenerational functional transmission under resource constraints, including occasional mutated descendants? This experiment deliberately tests a *different property* from A (heredity, not autopoiesis).

Design a **minimal new instruction ecology**, not a copy of any existing digital-organism implementation. The instruction set, scheduler, memory protection, reproduction primitives and resource economics remain explicit human decisions. No text model, assistant objective, externally scored logic task or optimizer is required.

**Essential evidence:** run traces showing an actual program executing a copy sequence; parent and child program hashes; lineage edges tied to execution receipts; mutant traits that persist in descendants; viable reproduction count and resource cost.

**Controls:** copying disabled, mutations disabled, randomized parent links, and separately random inherited program payloads. For any claimed new resource-handling function, test fresh niches never used in selection.

**Falsifiers/risks:** offspring are made by an engine cloning hook rather than executed genome copying; inherited "function" is merely a fixed simulator-defined bonus; parent-child trait link disappears against environment-matched shuffled controls; no viable offspring outside a single protected niche.

**Before coding:** independently justify instruction and memory semantics, freeze novelty assays and negative controls; use seeded sandbox interpreter with fuel/memory limits and no host function calls. No arbitrary host-code execution.

## Priority C — AL07-IDENTITY: prevent false positives

A separate evaluator tests candidate organization detectors against frozen sprites, inert oscillators, passive field attractors and actively restored reaction structures. Track constituent turnover and causal intervention response; report confusion matrix and false-organism rate.

No labels like "alive" until operational definitions and baselines are externally defensible.

## No early integration

Do not merge the chemistry world and instruction ecology into a hybrid until **each independently produces reproducible evidence** and the hybrid has a specific discriminating hypothesis. Do not add neural nets, LLMs, artificial reward signals, observers, or a dedicated local computer just to make the simulation look more alive.

## Prioritization

1. AL01-DISCOVERY is the **next implementation candidate** because AL01-CAL already validates molecule-accounting and controlled knockout measurements.
2. AL02-LINEAGE is the most informative **independent comparator**, with separately testable inheritance.
3. AL07-IDENTITY should follow to prevent attractive patterns from being mislabeled organisms.
4. Only then design cross-substrate experiments on resource exchange, repairable boundaries, ecological novelty and acquired memory.

All hypotheses should remain open to null outcomes; no claim that intelligence must emerge from evolution.
