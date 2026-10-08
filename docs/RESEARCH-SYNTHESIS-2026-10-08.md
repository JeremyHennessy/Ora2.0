# Scientific intake: artificial life and experimental priorities

**Intake date:** 2026-10-08 · **Source baseline:** [AI-Research main 52161ce](https://github.com/JeremyHennessy/AI-Research/tree/52161ce4ce08208232621845f3f08424f3adbc35) · **Evidence status:** literature synthesis + original engineering hypotheses, **not** an ALife replication.

## Scope and boundary

This is an independent project; no code, architecture, experiments, methods or failure narratives from any previous Ora project are design inputs. Read only scientific material relevant to the new artificial-life problem. GitHub contains source/reproducible experiment definitions, not a living runtime.

## What was actually reviewed

The AI-Research ALife research atlas, its 5-family [architecture comparison](https://github.com/JeremyHennessy/AI-Research/blob/52161ce4ce08208232621845f3f08424f3adbc35/docs/artificial-life/03-architecture-comparison.md), [evaluation framework](https://github.com/JeremyHennessy/AI-Research/blob/52161ce4ce08208232621845f3f08424f3adbc35/docs/artificial-life/05-evaluation-framework.md), [12 hypotheses](https://github.com/JeremyHennessy/AI-Research/blob/52161ce4ce08208232621845f3f08424f3adbc35/data/alife/hypotheses.jsonl), [8 future proposals](https://github.com/JeremyHennessy/AI-Research/blob/52161ce4ce08208232621845f3f08424f3adbc35/data/alife/experiment-designs.jsonl), [contrary evidence](https://github.com/JeremyHennessy/AI-Research/blob/52161ce4ce08208232621845f3f08424f3adbc35/docs/artificial-life/09-counterevidence.md), [feasibility bridges](https://github.com/JeremyHennessy/AI-Research/blob/52161ce4ce08208232621845f3f08424f3adbc35/docs/artificial-life/11-feasibility-and-cross-disciplinary-bridges.md), and relevant source articles. The compendium records **176 works in 30 tracks, 12 ALife hypotheses, 8 proposed ALife experiments** at this intake; most records are E1 metadata/primary reports, not local replications.

Directly cross-checked primary publications:
- Liu & Sumpter (2018), [collective self-replication in chemical networks](https://pmc.ncbi.nlm.nih.gov/articles/PMC6295724/). Authors model reaction systems with kinetics, conservation and emergent autocatalysis; **our calibration model is not a reproduction of their experiments**.
- Ofria & Wilke (2004), [Avida platform](https://doi.org/10.1162/106454604773563612). Actual executable heredity and digital evolution under an authored instruction and resource environment; do not import Avida code or presuppose its rewards.
- Plantec et al. (2025), [Flow-Lenia](https://doi.org/10.1162/artl_a_00471). Mass-conserving local transport supports complex localized patterns and mixed parameter landscapes; complexity and evolutionary activity are not established open-ended biological organization.
- Mordvintsev et al. (2020), [Growing Neural Cellular Automata](https://distill.pub/2020/growing-ca/). Regeneration experiments use target-derived learning or damage training; don't infer organism-derived developmental purpose.
- Taylor (2015), [requirements for open-ended evolution](https://www.tim-taylor.com/papers/taylor2015requirements.web.html). The five requirements are theoretical proposals, **not** a theorem proving sufficiency or a universally accepted definition.
- Segura (2026), [experimental probes of autopoietic self-maintenance](https://doi.org/10.1016/j.biosystems.2026.105928). **Abstract/publisher text screened, not full methodology reviewed:** the author distinguishes a system's causal closure from its measured response profile, a direct caution against calling a successful perturbation test "life".

## Significant findings

1. A self-copying program is evidence of **heredity**, not automatically of endogenous self-maintenance or self-produced boundaries.
2. An elegant persistent spatial attractor may not metabolize, regenerate, reproduce, learn or evolve.
3. A physically inspired conservation law and an ecological selection pressure are still human-defined model assumptions; document them, and disable any *special* survival or novelty bonus.
4. Sustained functional novelty cannot be established by a short run or single complexity metric. Explicit counterfactual function tests and controls for neutral drift are essential.
5. A CPU-only small-world experiment can answer an important causal question; expensive large worlds may obscure mechanisms before they are validated.

## Working options, deliberately not one merged architecture

| Foundation | Testable first property | Critical falsifier | Initial cost | Fundamental gap |
| --- | --- | --- | --- | --- |
| A. Artificial chemistry | Resource-fed feedback maintains transient constituents under damage | Equivalent recovery when necessary feedback is disabled | Low CPU | Composition and internal reaction network do not themselves define an organism |
| B. Executing hereditary programs | Copy operation changes descendants' programs and transmitted function | Same trait association when parent links are shuffled | Low CPU | A virtual CPU/genome boundary is designed |
| C. Conservative local fields | Localized organizational persistence after untrained perturbation | Passive attractor or mass-preservation control performs identically | CPU/GPU | Replication and lineage may be absent |
| D. Developmental cellular computation | Generalizes repair across different injuries | Recovery only works on externally trained damage/template | Variable | Target fitness may be externally imposed |
| E. Coevolving niches | Endogenous ecological changes cause new viable function | Changes explained by external novelty objective or more resources | Variable | Many implementations are evolutionary curricula, not reproducing organisms |

**Decision:** do not select any long-term substrate yet. Build a small, independently specified **experimental harness** first and calibrate whether it reports a mechanistically obvious causal difference. Then implement an independent heredity or field comparator, rather than combining the strongest features into an opaque system.

## A deliberately modest first step

Experiment **AL01-CAL** tests the **measurement pipeline**, not spontaneous origin of life: a designed two-species catalytic cycle compared with matched knockout and resource denial. An expected positive outcome would only show that our harness can distinguish internal feedback from an intervention. It will **not** establish spontaneous metabolism, true individuality, replication, evolution, intelligence or consciousness.

We will **not** promote AL01-CAL to a claim of emergent biology or E3 scientific replication. A scientifically stronger **AL01-DISCOVERY** follow-up should sample reaction networks without selecting for outcome, log all extinct/trivial cases, and compare against carefully chosen nulls. It is not yet implemented.

## Remaining research gaps

- Obtain complete method/negative results for 2018 reaction study and 2025 Flow-Lenia before claiming any exact replication.
- Formalize conserved reaction stoichiometry and potential energy/free-energy bookkeeping; molecule counts are not thermodynamics.
- Specify endogenous boundary formation separately from well-mixed chemical stabilization.
- Develop a lineage-verified, resource-bounded digital program comparator with no designer logic-task bonus.
- Establish calibration of process identity metrics vs inert oscillators and static attractors.
- Hardware capacity remains unknown; no assumptions about GPU or available storage have been made.

## Evidence discipline

**Published author claim** is not an independent reproduction. **Proposed architecture** is not a working system. **Simulation harness correctness** is not autonomous life. Advancing will require separate evidence for each claim level.

Existing AI-Research "research-only" prohibition applies to **that compendium's tasks**; the user separately authorized starting design and experimental work in this independent **Ora2.0** repository on 2026-10-08. No changes to the AI-Research repository were made in this work.
