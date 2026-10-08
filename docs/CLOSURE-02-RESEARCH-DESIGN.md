# CLOSURE-02 — Cost-controlled boundary function, or replace the model

**Completed decision:** [CLOSURE-02-FUNCTION results](CLOSURE-02-RESULTS.md) evaluated the five branch types specified below with 64 new seed groups, 157 eligible origins and 140 passing tests. Although programmed M permeability reduced catalyst escape and produced modest benefit relative to inert M, active additional M synthesis **did not improve core restoration beyond the cost-matched ghost**, while `no_shell` had the highest recovery. We therefore retire the current shell-production mechanism as a leading candidate and preserve it as a negative control. The process-based alternative below remains **planned**, not implemented.


**Historical research proposal, now experimentally evaluated in a separate preregistered study (2026-10-08).** Not an approved source recipe for “digital life,” a published first, a working protocell, an organism, or a result. Any implementation requires its **own separately frozen protocol before held-out data**. No code or problems from the previous Ora project are design inputs.

## What CLOSURE-01 changed

The [completed CLOSURE-01 trial](CLOSURE-01-SPATIAL-RESULTS.md) showed something useful and adverse: generating M-rich shell-like material did not generate measurable net functional benefit under the current definitions. Across 93 prequalified worlds, intact core A/R recovery was 37, but it rose to 79 when M-production reactions were disabled; intact and M-inert controls had 37 vs 33 core recoveries and **27 vs 27** “dual” recoveries. The latter primary metric requires M-production events **by definition** and cannot establish independently useful boundary function.

We should *not* respond by changing reaction constants, cherry-picking an attractive shell world, or making an animation implying life. Instead, test the most plausible null explanation with new worlds and physical controls; if it fails, **retire this spatial law**.

## C02-H01 — Does manufactured shell material protect what produced it?

**Hypothesis:** at a held-out resource/damage regime, productive M-shell interactions reduce outward loss of A/R at a given resource cost; this measurable effect vanishes when M has no permeability influence. It is a hypothesis about a *predefined chemical mechanism*, not autopoietic life.

### Next five experimental branches (proposal, exact freeze pending)

1. **SHELL + EFFECT:** produce M with S consumed, and activate the existing M-dependent A/R diffusion term.
2. **SHELL + NO EFFECT:** same M synthesis and S consumption, but the M-dependent diffusion term set to zero. Already available as a comparator in CLOSURE-01, but use **fresh independent seeds**, not post-hoc threshold tuning.
3. **GHOST-SHELL + EFFECT:** whenever a reaction channel would produce M, consume the same S but produce inert W instead. Existing M at the intervention checkpoint can still reduce diffusion until decay. This conserves **mass and same-cost per executed reaction**, though **not** exactly matched *number of production events over a diverging trajectory*.
4. **GHOST-SHELL + NO EFFECT:** same ghost product and no diffusion benefit. Compare to #3 to test whether retained initial M, rather than new synthesis, causally contributes.
5. **NO SHELL, NO COST:** disable shell channels, preserving substrate and reaction opportunities for A/R reconstruction (existing CLOSURE-01 control).

All five treatments branch from an **identical post-damage lattice and RNG state**, with the same baseline S inflow and the same death/diffusion rules. No entity, scheduler action or protected shell is ever “healed” by the host.

### Primary functional measurement — intentionally independent of shell appearance

- **Catalytic work capacity:** new A and R constructed **per S molecule actually consumed** over held-out post-damage windows; their net turnover and recovery in the *preselected* region.
- **Functional retention:** outward A/R diffusion **events crossing the predefined 3×3 perimeter**, normalized by the number of molecule movement opportunities and evaluated against inward flux. This directly measures the alleged membrane function, not whether M looks like a ring.
- **Damage resilience:** unmodified A/R core recovery over an additional held-out damage schedule; no requirement that M be present in the endpoint.
- **Occupancy/energy:** mass conservation, external inflow, catalyst/M/W counts, resource cost of M/ghost formation, zero free-engine repair.
- **Uncertainty:** resample independent source seeds, with all three starting-origin modes and ineligible groups retained. Include an experiment that disables *all* M production and compare to a passive M-lattice fixture, clearly labeled externally protected.

**Falsifier:** permeability effect fails to reduce normalized outward escape or increase repair function at matched resource cost, or any effect is equally present when all M is inert. Conclude that *this spatial shell model has no useful boundary under tested conditions* rather than tuning until success.

## C02-H02 — Organism identity cannot be assumed from ring pixels

Even if H01 appears positive, shell creation is still an authored material conversion in a finite lattice, and a region's center is chosen by the experimenter. A separate identity test is essential.

Compare **three independent detectors**, pre-trained or parameter-frozen on dev-only examples:
- spatial connected-component M ring with persistent A/R;
- local causal dependency network based on A↔R reaction/flux events, no pixel appearance required;
- randomized label/permeability-null model matched for total M and local density.

Require detection of **process identity through component turnover and new damage**, while rejecting passive diffusive pockets and inert oscillators. Report false positive and false negative rates; treat ambiguous split/merge events as **unknown**, not invented daughter organisms.

## Alternative experimental substrate B — no virtual lipids at all

If cost-controlled shell chemistry lacks independent protective function, don't keep refining a failed choice. Compare against a **self-regenerating process graph** with finite local event/memory budgets. Each active process consumes resources to maintain productive outgoing links, and productive links help generate the *processes that replace failed process nodes*. There are **no immortal graph nodes or external repair API**. Damage and random null processes are blinded.

Scientific value: it tests self-maintained **causal organization** without relying on a programmer drawing a membrane as a special type of molecule. Caveat: ordinary fault-tolerant software could pass; add controls for designer-specified recovery and cost/accounting. A positive is not evidence of life without heredity, ecological selection, individuality and evolution.

## Evidence needs before implementation

- Link to and method-audit the specific synthetic protocell paper proposing the transport/reaction law; avoid claiming a new discovery merely by authoring a lattice.
- Freeze exact conservative reaction law, quantitative movement-opportunity counters, cost comparator and new **held-out seeds** in a new commit.
- Prove a passive attractor/fake engine-repair example cannot pass the functional boundary evaluator.
- State upfront what H01 positive, null, negative, invalid simulation and insufficient eligible worlds mean.
- Include variation in initial M placement as a robust control, without feeding a discovered successful ring into every subsequent trial.
- Archive failures, trace history and software identity. Separate source E2 reviewed evidence from experiment E3 toy-world verification.
- Never select a model because its image resembles a creature. Do not combine separate CLOSURE, AL02 and AL03 successes as though they were achieved by one organism.

**Research checkpoint:** AI-Research at verified main `37ec45027e2bfd62030fb9c6c1840294c35f366a`, source-aligned with the earlier Stepney 2025, Stringmol failure and protocell reaction literature; additional public primary models include [Taneja & Higgs (2025)](https://doi.org/10.3390/life15050724) and [A 2025 autocatalytic protocell model](https://doi.org/10.1103/PhysRevE.111.014424). Neither demonstrates that our shell code is physically accurate, or grants permission to copy an author implementation with unknown license.

**No host self-modification, continuous autonomous runtime, OpenAI API, or dedicated-computer connection is in scope**. Research changes remain on a separate branch until independently tested and reviewed.
