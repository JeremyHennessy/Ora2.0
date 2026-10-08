# Ora 2.0 — Artificial Life Research Laboratory

**Status (2026-10-08): independent catalytic, heredity, ecological and spatial-organization experiments with reproducible negative controls. No demonstrably living, autonomous or self-sustaining digital organism has been created.**

## Research mission

Investigate whether a computational environment can support persistent, self-maintaining, adaptive, and evolving digital organization — potentially allowing increasingly sophisticated behavior to emerge **without targeting conversation, human imitation, or conventional assistant tasks**.

This is a new artificial-life research program, **not a restore, rewrite, or continuation of the former Ora / AgentTest implementation**. The name is reused; the architecture and evidence must be established afresh.

It is not established that such a system would count as living or conscious. We will distinguish simulated behavior, measurable life-like organization, theoretical interpretations, and experimentally validated observations.

## Working principles

- Begin with research questions and falsifiable hypotheses, **not** a preferred model architecture.
- Compare artificial chemistry, digital evolution, developmental/cellular systems, and other credible substrates before selecting a path.
- Do not assume an LLM, Transformer, chatbot, pretrained model, or OpenAI API is necessary.
- Avoid rewards for performing human tasks, looking alive, speaking, or making impressive demonstrations.
- A system cannot have *zero* design assumptions: document environmental physics, computational constraints, selection effects, and observer choices explicitly.
- Record seeds, parameters, code revisions, machine configuration, costs, negative results, and experimental limitations.
- Keep the organism/environment runtime independent of the observer UI and of ChatGPT conversations.
- Use isolated, permissioned simulations. External actions and self-modification require separately reviewed bounds; experiments must be reproducible and reversible.
- Never describe visual complexity, long uptime, or population growth as proof of life, open-ended evolution, or consciousness.

## Project separation

| System | Responsibility |
| --- | --- |
| [AI-Research](https://github.com/JeremyHennessy/AI-Research) | Source-backed literature, competing theories, open research questions, evidence synthesis (may be private) |
| **Ora2.0** | Experimental substrates, simulations, metrics, reproducibility, checkpointing, observer |
| Dedicated local machine (future) | Long-running, isolated computation and durable organism/world state |

**GitHub stores source code and versioned research; it is not itself an always-on organism runtime.**

## Start here

- [Founding research charter](docs/FOUNDING-CHARTER.md)
- [Experiments and progression gates](docs/EXPERIMENT-PLAN.md)
- [Dedicated computer / runtime design](docs/LOCAL-RUNTIME.md)
- [Source-backed artificial-life research synthesis](docs/RESEARCH-SYNTHESIS-2026-10-08.md)
- [Substrate-neutral experimental system design](docs/SYSTEM-DESIGN.md)
- [AL01-CAL frozen experimental protocol](docs/AL01-CAL-PROTOCOL.md)
- [AL01-CAL verified results and limitations](docs/RESULT-AL01-CAL-2026-10-08.md)
- [Next competing hypotheses and experiments](docs/NEXT-EXPERIMENTS.md)

## Immediate direction

1. Extend the literature synthesis in AI-Research and identify decisive experiments.
2. Choose multiple competing artificial-life mechanisms and preregister their simplest falsifiable tests.
3. Build deterministic, seed-replayable experimental infrastructure with no externally exposed execution permissions.
4. Measure evidence of adaptation, maintenance, heredity, novelty, and transfer against controls.
5. Only after reproducible results, add persistent local runtime and a strictly observational web interface.

## First experimental artifact

The standard-library-only `experiments/chemical_calibration.py` implements a deliberately **designed** two-species catalytic loop, matched disruption/ablation/resource-denial conditions and exact molecule accounting. It is an engineering measurement calibration, **not** a digital organism or spontaneous chemical-life discovery.

On 2026-10-08, the preregistered 32-seed run recorded sustained component recovery in **29/32 intact worlds** and **0/32** of each knockout, inert and starvation control; **3 intact failures were retained**. All 10 tests passed and the 128 records / 7,680 time-step traces passed independent checksum verification. See [full limitations and receipts](docs/RESULT-AL01-CAL-2026-10-08.md).

Run independently with Python 3.11+ (no third-party dependencies):

```bash
python -m unittest discover -s tests -v
python -m experiments.chemical_calibration --seeds 1000:1032 --output-dir runs/al01-cal
```

The generated `runs/` directory is Git-ignored. GitHub Actions archives the short-lived synthetic outputs, but only an externally backed-up copy provides durable retention. **No persistent autonomous process or remote machine is connected.**

## Random-network exploration (AL01-DISCOVERY)

The second experiment sampled 80 unscreened six-species reaction graphs, preserving the 21 acyclic ones and all failures. **151/240 trajectories** were eligible under the frozen pre-damage rule; intact recovery was **142/151**, compared with **47/151** after preselected cyclic-edge removal and **146/151** under a non-cycle-edge-control (including logged no-op cases). The full 79,200 post-step traces and 1,440 variant records were hash-verified. All 21 unit/integration tests passed.

**Interpretation:** this is causal measurement inside a deliberately authored toy chemistry, **not** evidence of digital life, replication, true metabolism or emergent general intelligence. Post-hoc inspection found some effect is trivially explained by deleting a target's only production route. A new blinded follow-up is therefore needed before stronger conclusions.

- [Frozen random-network protocol](docs/AL01-DISCOVERY-PROTOCOL.md)
- [Full experimental results and confounds](docs/AL01-DISCOVERY-RESULTS.md)
- [Original research hypotheses (untested)](docs/NEW-RESEARCH-HYPOTHESES.md)
- [Run and archived artifacts](https://github.com/JeremyHennessy/Ora2.0/actions/runs/37779761681)

## Independent redundancy experiment (AL01-RVCS)

Fresh random networks were required to have **three or more alternate incoming synthesis paths** to avoid the trivial single-producer confound. In 144 unscreened graph draws, 50 met the graph eligibility rule; 147 trajectories were evaluable. The precommitted strict redundancy signature occurred in **63/147 eligible paths**, with 22 of 144 networks meeting a 2-of-3 repeatability screen. The **29** suite tests passed, the full 3,024 variants and 166,320 step traces were hash-verified, and all negative outcomes were retained.

This supports **redundancy-like synthetic chemistry**, **not living digital organization**. The next priority is independent testing of *hereditary reproduction* in a bounded program substrate, rather than optimizing further chemical results.

- [Frozen experimental protocol](docs/AL01-RVCS-PROTOCOL.md)
- [Measured result and confound analysis](docs/AL01-RVCS-RESULTS.md)
- [Verified workflow and complete artifact](https://github.com/JeremyHennessy/Ora2.0/actions/runs/37780922686)

## AL02-COPY — Executed heredity under finite resources

The separately designed virtual instruction system can **execute one-byte COPY writes**, assemble daughter tapes from paid virtual material, and provide per-byte causal birth receipts. A four-opcode self-copying tape was **intentionally supplied at genesis**—there is no claim of spontaneous replication.

A frozen study of **64 world seeds × 4 conditions** recorded **853** mutating-arm births and **768** faithful-arm births, all with valid write-linked ancestry; copy-disabled and no-food arms produced **0** births. The mutation-enabled arm included **254 children with altered genomes** and **118 faithfully inherited mutant grandchildren**. A source-recorded A-food→B-food opcode variant produced 3 children in a sealed B-only assay; the original A-only tape produced none. **All 256 worlds eventually went extinct** when usable resources ran out. Energy/material residuals remained zero. Full test and artifact hashes are documented below.

- [AL02-COPY frozen protocol](docs/AL02-COPY-PROTOCOL.md)
- [AL02-COPY measured results, limitations, checksums](docs/AL02-COPY-RESULTS.md)
- [AL02 heredity architecture comparison](docs/AL02-HEREDITY-DESIGN.md)
- [Next science: ecological inheritance and causal-lineage analysis](docs/NEXT-ECOLOGICAL-RESEARCH.md)
- [First 64-seed experimental receipt](https://github.com/JeremyHennessy/Ora2.0/actions/runs/37783308992)

This is **executed inheritance inside an authored, bounded simulator**, not evidence of a self-maintained living entity, learned cognition, self-created interpreter, or open-ended evolution.

## AL07-TRACE — Verified causal genealogy (read-only)

Using the **unchanged and hash-verified** AL02 archive, an independent read-only analysis replayed execution receipts, material ownership/turnover, program counters, parent-child IDs, energy/resource ledgers and deaths across all 256 worlds. **All 1,621 recorded births passed**, with **0 invalid worlds** and an observed maximum descendant generation of **8** in the mutation-enabled condition. Of the observed authors of offspring, **219** had at least two children that themselves reproduced across the complete study. This does **not** prove independent spatial causal selfhood, living autonomy or open-ended evolution.

- [Frozen genealogy audit protocol](docs/AL07-TRACE-PROTOCOL.md)
- [Complete results, reproducibility and limits](docs/AL07-TRACE-RESULTS.md)
- [Independent source code](experiments/causal_genealogy_audit.py)
- [Successful 66-test CI and preserved evidence](https://github.com/JeremyHennessy/Ora2.0/actions/runs/37786729570)

## AL03-NICHE — Ecological resource specialization study

In a separate **engine-replicated** two-role ecological model, a P entity uses resource A and produces byproduct B; C entities use B. This model has **fixed, designer-authored** resource skills and cloning thresholds, unlike AL02's independently traced byte-write inheritance.

In the frozen 48-seed/5-treatment survey, **42/48** heritable worlds exhibited a predeclared multi-generation B-feeding lineage, compared with **12/48** worlds under independently assigned offspring roles and **0/48** worlds with B production disabled or mutations disabled. All 48 no-inflow worlds ultimately became extinct (25 transiently produced the lineage). **76 tests passed** and all 240 world outputs and material/energy receipts matched checksums. These outcomes primarily reflect authored resource conversion and inheritance parameters, **not spontaneous novelty, organism-level autopoiesis or perpetual survival**.

- [AL03 frozen protocol](docs/AL03-NICHE-PROTOCOL.md)
- [AL03 completed results and serious confounds](docs/AL03-NICHE-RESULTS.md)
- [Reproducible 48-seed GitHub Actions run](https://github.com/JeremyHennessy/Ora2.0/actions/runs/37788831042)

## AL03-MAINT — The cost of merely staying alive in our model

A new preregistered stress study tested the original AL03 finite world without maintenance debit, then independently added small, medium or large periodic energy costs to **every** live entity (including entities not scheduled to act). The approved AL03 model was **not changed**.

A read-only audit first regenerated and **matched all three original AL03 raw-file SHA256 hashes**. All 192 original externally fed worlds finished at population cap 40 and spent 71–76% of their recorded step histories at that cap. The new study included **48 fresh seeds per each of five treatment conditions**. All fed conditions still had survivors at step 480, but mean finishing population varied dramatically:

| Condition | Mean population at tick 480 | Surviving worlds |
| --- | ---: | ---: |
| No idle upkeep (original rules) | 40.0 | 48/48 |
| 1 unit every 8th tick | 37.875 | 48/48 |
| 1 unit every 4th tick | 24.8125 | 48/48 |
| 1 unit every tick | 5.8125 | 48/48 |
| 1 unit every 8th tick; **no outside supply** | 0 | 0/48 |

**Crucial negative result:** the prespecified binary survival endpoint **could not discriminate any of the four continually fed maintenance conditions**, despite dramatic population and turnover changes. Persistence at a fixed horizon is not an aliveness or sustainable-organization metric. Exact conservation records and failure cases were retained.

- [AL03-MAINT frozen protocol](docs/AL03-MAINT-PROTOCOL.md)
- [AL03-MAINT independent historical saturation audit and measured result](docs/AL03-MAINT-RESULTS.md)
- [Source code](experiments/maintenance_stress.py) · [Read-only retrospective analyzer](experiments/retrospective_saturation.py)
- [Next research direction: endogenous organizational closure](docs/CLOSURE-01-RESEARCH-DESIGN.md)
- [Successful preregistered GitHub Actions evidence](https://github.com/JeremyHennessy/Ora2.0/actions/runs/37791242970)

## CLOSURE-01-SPATIAL — Testing an apparently protective shell

A **new independent 9×9 spatial chemistry** uses five abstract molecule types (S/A/R/M/W), locally constructed material M and an explicitly authored rule that lets M reduce catalyst movement. We tested **36 seeds × three independently defined origins × six interventions** (648 runs) with an identical preregistered post-damage 3×3 target. The nutrient-only origin can activate A through a **hardcoded basal S→A conversion**; it is not a simulation of abiogenesis.

Across **93/108 eligible pre-damage worlds**, the intact network achieved **37** independent *core A/R recoveries*. When M synthesis was disabled, that rose to **79**, whereas disabling only M's effect on diffusion yielded **33**. The combined shell+core criterion occurred **27/93** times under both intact and permeability-null conditions. The result **does not establish a protective shell**; disabling M synthesis also frees resources for A/R, so a cost-matched follow-up would be needed.

The original study passed **104 tests**; a second full replay with a separate raw-record/trace-chain analyzer passed **110 tests**, regenerated byte-identical data, and verified all **648** treatment records and **38,880** step traces. No molecule-count residual was found. This is **negative evidence about a particular engineered reaction-diffusion rule**, not a result about the possibility of artificial life generally. Previously approved simulator code/results are unchanged.

- [Frozen spatial chemistry protocol](docs/CLOSURE-01-SPATIAL-PROTOCOL.md)
- [Verified outcomes, negative evidence and source hashes](docs/CLOSURE-01-SPATIAL-RESULTS.md)
- [Designer-shortcut ledger](docs/CLOSURE-01-SHORTCUT-LEDGER.md)
- [Next design: cost-controlled function or an independent substrate](docs/CLOSURE-02-RESEARCH-DESIGN.md)
- [Original frozen experiment (104 tests)](https://github.com/JeremyHennessy/Ora2.0/actions/runs/37795271005)
- [Independent archived-data replay and diagnostics (110 tests)](https://github.com/JeremyHennessy/Ora2.0/actions/runs/37796741385)
- [Read-only diagnostics source](experiments/closure_spatial_diagnostics.py)

## Privacy

This repository was **public when the founding scaffold was created**. Never commit credentials, private-machine addresses, personal files, checkpoint data containing sensitive information, private paper archives, or environment secrets. Review visibility before connecting a dedicated machine or any self-hosted runner.
