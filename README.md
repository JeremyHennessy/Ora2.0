# Ora 2.0 — Artificial Life Research Laboratory

**Status (2026-10-08): three verified synthetic-chemistry studies plus one separately verified executed-heredity experiment. This is a research laboratory, not a demonstrably living or self-sustaining digital organism.**

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

## Privacy

This repository was **public when the founding scaffold was created**. Never commit credentials, private-machine addresses, personal files, checkpoint data containing sensitive information, private paper archives, or environment secrets. Review visibility before connecting a dedicated machine or any self-hosted runner.
