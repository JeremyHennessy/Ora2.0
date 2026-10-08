# AL07-TRACE — Audited causal genealogy of AL02 synthetic bytecode replicators

**2026-10-08 · Completed, checked against archived raw AL02 events.** A positive result here establishes **event-level genealogical consistency** in a designed finite virtual instruction system, NOT life, an evolved physics, a spontaneously generated organism, or counterfactual independence of siblings.

## Exact source / observation receipts

- [Frozen AL07 protocol](AL07-TRACE-PROTOCOL.md), authored **before** this read-only audit, at commit `010c6f098158e1157c9fe93e0e9507ec1af25f00`.
- New independent auditor: `experiments/causal_genealogy_audit.py`, committed at `381c5bc54832f4ec60842a6880c6a3dbe86e8693`; tests `tests/test_causal_genealogy.py` committed at `4c74084599fd060cdbc9ca1d1f148f5fb2e8a15c`.
- [GitHub Actions run #37786729570](https://github.com/JeremyHennessy/Ora2.0/actions/runs/37786729570) at source SHA `49e8441a3b16acdb05435e1d85cd809efa48113c` — **success**, **66/66** regression + adversarial tests.
- The run independently **regenerated** all originally frozen AL02 worlds using Python **3.11.17** and checked source data SHA-256 against the original published AL02 archive **before** running the new auditor. No AL02 physics, seeds, or test criteria were changed.
- Original AL02 data hashes all matched exactly:
  - `worlds.jsonl` SHA256 `684f135f8f59261877414901a1d3f5e5b114a93ce83710e348cc82030de35d7f`
  - `births.jsonl` SHA256 `88cc94dda7bc00173e4ddfd0fdd8a3af0082b7f78926b4ad6e0e26838318fd44`
  - `events.jsonl` SHA256 `8d0872972a15c53155658df493d2ce10e1b00d34bb75e2b1f543fdab5820d7a5`
- Archived result artifact `al07-trace-evidence`, GitHub ID `11554492822`, 90-day retention (NOT permanent storage). This archive was independently downloaded and inspected.
  - `genealogy-worlds.jsonl` SHA256 `d6074f5b646b48ddcb95c0fe5c434cfb169659a66ac52dd2c2e4b9277ebdfb37` — **256** world-level analysis rows.
  - `genealogy-summary.json` SHA256 `42aee642f9dd9e4c584926bc18808c74a6a523a0ad3cd3f450053373fd6cfc57` — full combined metadata and per-arm analysis.

## Empirical result, no selection of surviving worlds

| Audited condition | AL02 births independently reconciled | Fertile descendants | Parents with ≥2 direct children | Parents with ≥2 *fertile* children | Maximum observed generation |
| --- | ---: | ---: | ---: | ---: | ---: |
| Mutations enabled | **853** | 309 | 217 | 91 | **8** |
| Faithful copying | **768** | 384 | 192 | 128 | 4 |
| COPY disabled | 0 | 0 | 0 | 0 | 0 |
| Food denied | 0 | 0 | 0 | 0 | 0 |
| **Total** | **1,621** | **693** | **409** | **219** | — |

**0/256 worlds failed the independent time-ordered genealogical audit.** All **42,249 recorded events** were reconciled with the world/birth manifests. The new auditor independently tracked:
- active parent program/data and read-head position at every COPY instruction;
- one specific material unit per executed daughter-byte write, nursery transfer, birth and death;
- permitted post-death material reuse vs simultaneously owned duplicate units;
- actor and tick ordering, execution confirmation of COPY and DIVIDE, opcode semantics and parent/daughter hashes;
- genotype descent, generation number and multi-generation branching;
- an independently recomputed energy ledger and final food/material balances.

The audit observed **2,074** reallocation events using previously released material in mutation-enabled worlds, and **1,472** in faithful-copy worlds (counts of events, **not** a count of unique molecules). Conservation residual remained **0**.

**Genotype variation:** 254 altered child tapes; 118 grandchildren exactly retained the mutated parent's genotype. Mutation-armed worlds attained depths ranging from 1 to 8 generations, while faithful-copy worlds attained depth 4. These are features of this *finite scripted instruction substrate*, not evidence of increased evolved intelligence.

## Explicit falsifiers and adversarial evaluation

The new unit tests reject forged BIRTH records without corresponding write events, swapped parent IDs, premature or duplicated child IDs, an occupied material unit allocated twice, out-of-order/missing events, mismatched active source bytes, fake COPY EXEC instructions, and energy injection. They also verify that legitimate material release/reallocation is not treated as a new organism.

**Limitation:** the event stream and interpreter were originally authored in the same project. The audit is **independent software over the logs**, not independent observation of natural chemical interactions. The *causal* claim here is confined to parent-executed byte writes, not all possible physical causal links or environmental independence. The programmer specified reproductive semantics, genesis program, resource sources and mortality.

Multiple siblings with authentic parent-written bytes can **still causally influence each other** through shared resources, update scheduling and environment. Do not translate "91 parents with two fertile children" into "91 independently self-organizing biological families." Formal Outlier-style counterfactual necessary-cause cellular ancestry is a distinct test not performed here.

## What this does and does not advance

- **Supported:** verifiable execution-linked daughter program construction, multi-generation program transmission and resource/mass bookkeeping in this artificial instruction ecology.
- **Not demonstrated:** spontaneously originated replicators, a self-produced boundary, resource-renewing ecology, independent emergent identities, adaptive learning, new self-invented instruction semantics, open-ended function or life.
- **Research next step:** preregister a **new** causal ecological-resource exchange model with strong no-producer, resource-matched external feed, and history-shuffle controls. Keep chemistry feedback and instruction heredity separate unless an explicit hypothesis requires integration.

## Reproduction

No protected dataset, API key, desktop program or old Ora code is required. Check out source SHA and use Python 3.11.17:

```bash
python -W error::ResourceWarning -m unittest discover -s tests -v
python -m experiments.executed_heredity --seeds 5000:5064 --output-dir runs/al02-al07-input --source-revision 1322657ee5189c483aa12f04f14fc54c55100502
python -m experiments.causal_genealogy_audit --input-dir runs/al02-al07-input --output-dir runs/al07-trace
```

The AL07 script enforces all three original AL02 raw hashes before proceeding. Absence of a new organism is **not** evidence that digital life is impossible; it is a boundary on the present claims.
