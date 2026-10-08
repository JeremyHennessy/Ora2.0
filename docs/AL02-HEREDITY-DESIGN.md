# AL02 — Independent heredity and executable reproduction research design

**Status:** planning and candidate protocol, 2026-10-08. **No AL02 simulator, organism, genome or reproduction experiment has been implemented or run.** This is a distinct scientific substrate, **not** imported from the previous Ora project and not a continuation of its architecture.

## Why shift away from chemistry now?

The Ora2.0 [AL01-CAL](RESULT-AL01-CAL-2026-10-08.md), [AL01-DISCOVERY](AL01-DISCOVERY-RESULTS.md), and [AL01-RVCS](AL01-RVCS-RESULTS.md) studies generated reproducible evidence about **feedback and redundant constituent recovery inside designed synthetic reaction systems**. None has hereditary organization, identifiable descendants, within-lifetime learning or new ecological functionality. Further parameter tuning could inflate success while answering little about digital life.

**AL02 scientific question:** can a separate computational substrate support **causally verified reproduction and heritable functional change**, where producing offspring requires a structure's own sequence of resource-consuming operations rather than an engine-side `clone(parent)` call?

A system that simply resembles a parent does not qualify. Mutating a file in a repository does not qualify. A unique lineage record must be justified by **observed execution of parent operations**.

## Three competing implementation paths (no predetermined winner)

| Candidate | Primitive | Strongest advantage | Key weakness |
| --- | --- | --- | --- |
| A. Bounded virtual instruction chemistry | Programs manipulate local instruction-material cells; offspring executable material must be written by parent operations | Precise causal ancestry and copy fidelity tests | Interpreter, allowable operations and division rule are explicitly designed |
| B. Template-polymer symbolic reactor | Local monomers and template interactions create descendants with copying errors under conservation rules | Heredity analogy without CPU-like instruction execution | Hard to avoid hidden chemical templates that guarantee self-replication |
| C. Spatial cellular hereditary rules | Mutable rule fragments diffuse or transfer into newly bounded local structures | Potential connection to endogenous individuality | Identifying true parent/daughter and inherited function is difficult |

**Initial proposal: A**, as the first *measurement benchmark*, not a declaration that virtual CPUs are the ultimate living substrate. A and B should be independently compared before any hybrid.

Research antecedents: [Avida platform](https://doi.org/10.1162/106454604773563612); [Lenski/Ofria et al. 2003](https://doi.org/10.1038/nature01568); [Taylor 2015](https://arxiv.org/abs/1507.07403); [AI-Research ALife architecture comparison at 2026-10-08](https://github.com/JeremyHennessy/AI-Research/blob/da7297629d1208774df758029cf3efc6a9800035/docs/artificial-life/03-architecture-comparison.md). These are prior work and cautions, not evidence that the design below is unique or will succeed.

## Candidate A — strict implementation boundary

**Host/sandbox**
- Write a new deterministic, finite interpreter that processes data-only tokens from a **fixed, minimal** instruction set. The only effects occur in bounded virtual memory/resource state; interpreter instructions cannot invoke Python functions, a shell, the network, filesystem, GitHub or machine administration.
- Track exact source and interpreter revision; mutation affects only inert genome *data* under interpreter rules, not the interpreter's Python source or host.
- Limit virtual memory, instructions per step, organism occupancy, population and resources; resource starvation/invalid instructions can cause extinction.
- A candidate virtual organism has an explicitly allocated segment only as a **measurement convenience**. Treat the segment boundary as designer-provided, not endogenous life.
- A scheduled virtual tick and energy accounting are also designer-provided. Never confuse uptime with life.

**Reproduction must be an executed event, not cloning**
1. A deliberately supplied **minimal viable replicator** serves as a positive control in the first test. This is not spontaneous origins.
2. It must read its own program data, execute bounded **copy/write** instructions, and pay for instruction execution/material allocation.
3. A division operation may *mark* completed written daughter material as executable only when a predeclared integrity condition holds. The engine must not directly populate an offspring genome by copying the parent's list or strings.
4. Birth receipts link every daughter byte to an actual executed write in the parent's operation trace. Every birth has a parent, daughter, instruction provenance, material/resource delta and program hash.
5. Copy errors during writes can introduce inherited variants. Variants compete only through the virtual physics and its resources, **not** via an LLM judging intelligence, image beauty or successful human tasks.

**First test does not claim spontaneous replication:** because the initial viable copier is supplied, the first question is whether the measurement infrastructure can *distinguish physical-like executed copying and inheritance from an engine-driven duplicate*.

## First bounded falsifying study — AL02-COPY (to preregister fully before implementation)

Run separate identical-seed worlds with:
- Working instruction-executed copier and no copying errors.
- Copy/write disabled: the interpreter cannot produce an offspring from its parent's memory by a hidden engine operation.
- Finite-material/energy denial: complete daughter material cannot appear without paid supply.
- Engine-side fake duplicate inserted only as an **evaluator negative-control fixture**, never mistaken for a true birth.
- Copy errors enabled vs disabled (conditional second stage): link parent/daughter mutations to exact write events.
- Deliberately shuffled parent IDs with identical apparent genome resemblance: heredity evidence must fail this control.

**Primary outcome stage 1:** complete, valid instruction-to-offspring material provenance for **every reported birth**; audit mismatch count must be zero. Separately measure viable descendants, reproduction latency and resource expenditures across all seeds, including sterile/extinct ones.

**Primary outcome stage 2 (only after stage 1):** functional heritable change, demonstrated by parent/descendant retained *behavior under an independent resource/interaction assay*, with outcomes distinguishing mutation from environmental coincidence. Do not credit genome length, edit distance or chromosome visual shape as functional novelty.

Use preregistered independent seeds, bounded compute, clear failure categories, whole-world denominators, held-out resource settings and frozen evaluation logic. No inference of indefinite evolution or cognition.

## Falsifiers and negative-result treatment

- A child exists without all required executed write receipts → **invalid heredity evidence**.
- True offspring arise after disabling the only reproductive operations → **engine-copy leakage**.
- Resource counters are not causally linked to copying and division → **decorative economy**.
- Parent/child mutation is merely environmental resemblance or shuffling → **no demonstrated inheritance**.
- Program descendants cannot maintain viable reproduction outside an extremely tuned seed → record **substrate fragility**, not "birth of life".
- Selected "novelty" is just a preprogrammed bonus for human-defined tasks → cannot be called emergent new ecological ability.
- Any host/system permission or external API is accessible to virtual instructions → **invalid sandbox**, do not deploy.

## Original, explicitly unverified research ideas after AL02-COPY

- **Causal lineage certificates:** test whether ancestry can be reconstructed solely from logged material/write transfers and remains stable under deliberate parent-ID corruption. This may enable organismhood claims without assuming genotype appearance defines identity. This is a research conjecture, **not asserted as a first ever algorithm**.
- **Ecological function inherited without an explicit task reward:** if an unexpected mutant exploits a new byproduct of other descendants, validate with blinded material conversions, hidden resource switches, and descendant-transfer tests rather than rewarded logic tasks.
- **Organism/environment co-construction:** compare environment-conditioned reproduction with replication whose program partially constructs its own protective boundary; defer until independent heredity and independent boundary-maintenance evidence both exist.

## Required design decisions before actual code

- Primitive memory model, exact instruction-token set and execution semantics.
- Molecular/material budget linked to every write and division.
- How virtual age, mortality, write errors and scheduling operate.
- Which parental state is inherited and which environmental state is *not*.
- Baselines that cannot fake a child's recorded causal creation.
- Holdout seeds and independent functional novelty tasks **before** evaluating the new organism environment.
- Exact CPU and RAM use before running persistent simulations on any dedicated computer.

## Advancement rules

**G2-a:** trusted interpreter and independent evaluator, every birth has verifiable executed copying, no host privilege escape, and no fake progeny in null control.

**G2-b:** at least one lineage shows repeated nontrivial heritable variation beyond random parent-link controls, documented in resource-limited worlds. Mutations alone do not establish useful evolved function.

**G2-c:** independently checked descendant functionality transfers across unseen resource regimes without an externally imposed intelligence/novelty reward. If this does not occur, stop and report rather than inventing a success narrative.

**Next engineering deliverable:** pin AL02-COPY's exact instruction machine semantics and preregister a small first sample, then implement the smallest test interpreter. This document is the research/architecture handoff, **not authorization to pretend an AL02 organism already exists**.

The [AI-Research compendium](https://github.com/JeremyHennessy/AI-Research) remains the evolving source reference; each new experimental decision should explicitly record the checked source SHA and scientific method reviews. GitHub is the source/research store. A dedicated computer, when available and separately configured, may eventually supply isolated continuous compute and durable state, but is not currently connected.
