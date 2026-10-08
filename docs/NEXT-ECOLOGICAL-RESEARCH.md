# Next scientific program — from copying instructions toward ecological organization

**Prepared 2026-10-08. Research design only.** This document does not assert that Ora2.0 is alive, indefinitely evolving, intelligent or consciously experiencing anything.

## What we now know from independent Ora2.0 research

- **AL01-CAL:** a deliberately seeded catalytic loop can causally recover after damage under an explicit nutrient feed.
- **AL01-DISCOVERY:** random catalytic graphs (including failures) sometimes maintain the chosen constituent after damage; removing its sole production route trivially breaks it.
- **AL01-RVCS:** under graph-redundancy restrictions, some toy networks tolerate either of two cuts but not both; neither ecology nor true organism boundary is demonstrated.
- **AL02-COPY:** actual parent-executed byte writes create auditable offspring; mutations sometimes transmit across multiple generations, and a designer-specified second-food opcode can provide a resource-specific advantage. **All finite-food worlds go extinct.**

Do **not** merge these distinct substrate mechanisms simply to claim a checklist of life criteria. Showing property X in one simulator and Y in another is not proof that a *single* self-sustaining organism has both.

## New literature after AL02-COPY was frozen

AI-Research main `3a4d7c7017d3136f88dd08fffe733e7313538a7f` (verified passing validation) added:
- [Hintze & Bohm, 2026](https://doi.org/10.1038/s44260-026-00074-2): replication should be analyzed as branching **causal ancestry**, not shape recurrence. Their finite-world result in the *Outlier* cellular automaton says nothing about Ora2.0's genome copying having endogenous metabolic selfhood.
- [Stepney, 2025](https://doi.org/10.1098/rstb.2024.0298): distinguish requirements for life from design and implementation; **autopoiesis, agency, and open-ended adaptation** are proposed conceptual requirements, not demonstrated in our program.
- AI-Research `docs/artificial-life/23-unified-organism-evidence-standard.md`: AL-C01..AL-C10 mark replication, multi-generation, function, maintenance, resources, agency and open-endedness separately.
- Research on mutable computational languages / meta-chemistries was added as a tentative ALIFE 2026 concept. It is **not a sufficient justification for putting an organism in control of host Python execution or deployment**.

## Decision: two **independent** low-cost tracks, no mandatory feature list

### Track E — AL03-ECOLOGICAL-RECORD (research proposal)

**Original research hypothesis H-E1 (untested, historical novelty unverified):** offspring and non-descendants might inherit *usable environmental conditions* through costly byproduct transformations, creating an additional feedback channel beyond copied opcodes. This could generate resource-dependent lineages and ecological effects **without a task-specific intelligence reward**, but those effects may be entirely attributable to programmer-defined exchange primitives.

**Important design challenge:** current 4-opcode replicators use one resource and die when it runs out. Simply adding infinite food hides the problem; it would extend uptime without demonstrating self-production.

**Candidate minimal rules to compare, not yet frozen or coded:**
- A resource can be converted into useful energy + explicitly accounted byproduct under local work, with numerical conservation of **energy potential, physical units, and waste heat**. Avoid inferring thermodynamics from counters.
- A distinct interpreter operation may access the byproduct at a predeclared energetic cost. **The operation itself is designer-provided**; selection could discover its use through mutations or gene sequencing only within this fixed capability universe.
- Bound food and material supply, leakage and decay. Avoid scripted successful cooperation or granting a resource bonus for visually novel behavior.
- Only after positive calibration, compare freely inherited eco-relevant instruction sequences, where survivors affect the next generation's environment.

**Decisive interventions:**
1. Byproduct retained vs removed, holding energy potential supplied equal.
2. Resource-user lineage vs user-disabled matched world, plus external reservoir delivering the *same* resource flux without a producer.
3. Same program/environment genomes but history-shuffled resource placement (if spatial).
4. Isolated producer, isolated consumer, and coupled mixed population.
5. Donation costs visible in producer survival and descendants, not artificially free nutrient creation.
6. Frozen unseen shifts in resource type, patchiness, duration and supply source.

**Endpoints:** new viable ecological interaction, indirect evidence of source-dependent use, descendant **functionality** on an unseen resource challenge, lineage and interaction causality, resource ledger equality, survival/extinction, neutral-drift controls, world-level uncertainty and any saturation. Count all sterile/extinct worlds.

**Likely disappointing outcome:** apparent cooperation is only a pair of programmer-defined conversions and vanishes under resource normalization. Such a result is informative, not a failure requiring further patching.

**Do not implement** until an exact resource bookkeeping law, genome encoding, independent null baselines, and hidden environmental test are preregistered in a new immutable protocol. Do not rewrite AL02-COPY to simulate ecological success.

### Track I — AL07-CAUSAL-LINEAGE-AUDIT (low-cost analysis)

**Hypothesis H-I1 (untested):** direct material-write receipts can distinguish actual multiple sibling births from repeated program emissions or forged ancestry, but an event-level gene ledger is **not equivalent** to a complete causal dependency graph of an emergent distributed individual.

**Proposed read-only analysis of AL02-COPY's *existing* retained dataset:**
- For each parent with multiple children, show independent write receipts and material identities. Reconstruct generation depth, sibling sets, lineage branching counts and exact death/extinction outcomes.
- Inject fake “births” with no COPY receipts, sibling-as-parent substitution, copy/write-order permutation and reassignments that preserve apparent genomes; require auditor failure.
- Track material ID **reuse across deaths** with time-indexed provenance, rather than falsely declaring that one reused token means the same organism persisted.
- Compare lineage models based solely on string similarity against executable event ancestry. Report false links/correlated copy errors.
- Acknowledge that shared resource consumption creates ecological causation between siblings, so write-provenance independence is a weaker claim than fully counterfactual social/physical independence.

**No new evolutionary world needed for initial H-I1.** This creates an independent *measurement* that can later evaluate richer ecological substrates.

## What would change scientific confidence

**Toward a stronger digital-organism program:** a *single* substrate shows parent-caused offspring, heritable function that responds to unseen environment, endogenous constituent/boundary maintenance and resource-accounted ecological effects, confirmed by mechanism-disabling controls. Long-term novelty requires separate evidence across horizons and independent measurement families.

**Against a promising direction:** all novelty reduces to a hardcoded opcode swap, all lineages collapse without designer reservoir, no heritable new ecological capability appears after controlling resource inputs, or an apparent organism is just immutable allocated memory. Preserve that negative evidence.

## Architectural independence and security

No previous Ora architecture/phase/algorithm is used. Experiments operate inside bounded, **data-only** instruction interpreters. Future meta-computation must remain confined to inert virtual semantics and must never imply host-code modification, GitHub write authority, internet access or arbitrary file access. The proposed dedicated local computer remains a future **separately commissioned isolated runtime**, not connected now.

## Suggested implementation sequence

1. Preserve all AL01 and AL02 raw runs, exact Git hashes and source-pinned Python.
2. Run **read-only AL07 causal genealogy analysis** on the current verified AL02 artifact, with injected false-lineage controls.
3. Before adding any other life mechanism, finalize the **AL03 ecological mass/energy flow** and its strongest alternatives (reservoir-driven growth vs actual producer-dependent niche use).
4. Build and run a bounded AL03 study only after its new protocol passes source review and unit tests.
5. Revisit architecture choice from observed evidence rather than aesthetics or a forced “level of intelligence” milestone.
