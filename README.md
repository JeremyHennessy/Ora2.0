# Ora 2.0 — Artificial Life Research Laboratory

**Status (2026-10-08): independent artificial-life research laboratory with one completed, reproducible chemical-feedback measurement calibration. No artificial organism has been created, trained, or demonstrated to be alive.**

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

## Privacy

This repository was **public when the founding scaffold was created**. Never commit credentials, private-machine addresses, personal files, checkpoint data containing sensitive information, private paper archives, or environment secrets. Review visibility before connecting a dedicated machine or any self-hosted runner.
