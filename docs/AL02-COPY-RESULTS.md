# AL02-COPY — Verified executed reproduction and inherited opcode differences

**Research date:** 2026-10-08. **Experiment completed** under a predefined, deliberately seeded virtual CPU. **Not** a digital organism, spontaneous biogenesis, evolved intelligence, evolving interpreter or open-ended evolution.

## Frozen provenance

- [Preregistered protocol](AL02-COPY-PROTOCOL.md): commit `60932ea12f577605bb25baef4341853346072676`, recorded **before evaluating** holdout worlds 5000..5063.
- Interpreter added at `aa85adda512dea72fac0c9a03a2c4b0b872a867a`; independent causal auditor at `cfc75f6d4fb20ba05a8fc98814f7a33dadab3f84`; 21 new tests + two stronger state-ledger/anti-clone tests.
- Exact experimental execution source: `1322657ee5189c483aa12f04f14fc54c55100502`.
- [GitHub Actions run #37783308992](https://github.com/JeremyHennessy/Ora2.0/actions/runs/37783308992), status **success**, run logged 2026-10-08T13:18 UTC; **50/50 tests passed** with `-W error::ResourceWarning` before the holdout execution.
- Python **3.11.17**. No network calls, OpenAI API, LLM, GPU, external machine connection or host-execution bytecodes.
- Archived GitHub artifact: `al02-copy-complete`, ID `11553740402`, 90-day retention; independently downloaded and inspected after execution.

## Independent output checks

| File | SHA-256 independently checked | Lines |
| --- | --- | ---: |
| `worlds.jsonl` | `684f135f8f59261877414901a1d3f5e5b114a93ce83710e348cc82030de35d7f` | 256 |
| `births.jsonl` | `88cc94dda7bc00173e4ddfd0fdd8a3af0082b7f78926b4ad6e0e26838318fd44` | 1,621 |
| `events.jsonl` | `8d0872972a15c53155658df493d2ce10e1b00d34bb75e2b1f543fdab5820d7a5` | 42,249 |

Both the study code and an independent post-download script confirmed these SHA-256 values. The recorded birth count matches archived birth receipts; all world event streams sampled during external audit had contiguous event identifiers. The simulator checked a **256-unit material ledger** and a **nutrient→organism energy→heat ledger** on every virtual tick: maximum residual **0** under every treatment.

## Precommitted conditions and results

64 seeds, 5000–5063 inclusive, four interventions, maximum 600 interpreter instructions per world (256 total experimental worlds). One *deliberately supplied* executable seed tape `[EAT_A,COPY,LOOP,DIVIDE]` begins each world; no viable organism was discovered from primordial randomness.

| Arm | Worlds | Verified births | Births in worlds | World extinctions | Invalid birth certificates |
| --- | ---: | ---: | ---: | ---: | ---: |
| Mutating copy (8% per emitted opcode) | 64 | **853** | 64/64 | 64/64 | **0** |
| Faithful copy, mutations disabled | 64 | **768** | 64/64 | 64/64 | **0** |
| Byte COPY operation disabled | 64 | **0** | 0/64 | 64/64 | **0** |
| No food A or B | 64 | **0** | 0/64 | 64/64 | **0** |

`copy_disabled` had zero executed writes, and `no_food` had four mutated *incomplete nursery bytes* but **zero births**: unfinished copying was never counted as an offspring. Mutation-free arms had **0 mutated bytes**. The identical observed number of births in every `faithful` world is a consequence of deterministic identical starting conditions, **not 64 independent confirmations of an evolutionary effect**.

## Inherited variation, with exact limits

- Mutating worlds generated **254 offspring whose ordered opcode tape differed from the recorded parent's tape**; **364 mutated bytes written** in total, including incomplete nurseries.
- **118 grandchildren** matched the full novel opcode tape of a parent who had itself been born with a mutation. This measures actual *multi-generation faithful transmission of altered instructions*, not independent innovation of arbitrary new functionality.
- Distinct 4-byte child tapes observed in the mutation-enabled arm: **82** (including sterile/nonfunctional variants). Genome length and opcode alphabet are fixed; increased diversity is **not** unbounded evolution.
- Exactly **five recorded direct `EAT_A -> EAT_B` offspring** retained the other three canonical reproduction operations. Four of these five mutation-origin descendants later produced at least one child with the same B-feeding tape; the fifth had **zero daughters**. All five origins, including the non-reproducing one, are retained.
- Red food consumed: **768 beads** across faithful worlds and **768** across mutating worlds; blue food consumed: **0 faithful** vs **454 mutating** across **29/64** mutation-enabled worlds. This supports expressed resource-use variation under the investigator's two-food ecology, **not** open-ended intelligent adaptation.

## Separate prespecified blue-only assay

The first qualifying mutated B-feeding tape originated from **seed 5002**, parent `2` to child `6`, birth event ID `132`. The isolated assay initialized the same *genotype* in a new fixed environment with **0 A** and **3 B** food beads, copying enabled and mutations disabled; comparator was the original A-dependent genotype.

| Assayed tape | Offspring within 40 ticks |
| --- | ---: |
| `[EAT_A,COPY,LOOP,DIVIDE]` (ancestor) | **0** |
| `[EAT_B,COPY,LOOP,DIVIDE]` (mutant) | **3**, all with valid birth provenance |

**Important:** This assay constructs a new seed with the observed mutant *genotype*; it does not transplant the original daughter's physical state. It tests a **pre-authored EAT_B opcode**, not a genuinely invented sensory/learning mechanism. The test design intentionally looked for that exact variant after observing the mutation group; functional outcome is bounded to this predetermined opportunity.

## Interpretation against research standards

**Supported, limited claim:** under our investigator-defined virtual instruction and resource rules, parent programs performed byte-by-byte copy operations that produced auditable daughter instruction tapes. Substitution errors yielded transmitted variation across generations. The option to consume resource B manifested in some descendants, changing their ability to reproduce in an environment where A was absent.

**Explicitly not supported:**
- Spontaneous emergence of a replicator: genesis program supplied.
- Autopoiesis or a self-produced organism boundary: program memory, opcode semantics, scheduler and replication gate imposed by interpreter.
- Self-sustaining ecology: **all 256 worlds extinct** under finite resources.
- Self-created novel function: FEED_B capability pre-existed in a fixed ISA.
- Within-lifetime adaptive learning, agency, ecological construction, open-ended evolution or consciousness: no relevant controls or evidence.
- Independent external replication: only one model, one frozen seed panel and one execution with validated artifacts.

The independent audit catches a fabricated birth lacking COPY receipts, shuffled parent ID, or altered offspring byte; the anti-clone invariant also catches a resource-balanced rogue organism inserted without a birth receipt. These are **engineering properties tested in code**, not proof that a digital computer possesses life.

## New relevant literature ingested after the protocol was locked

AI-Research advanced to SHA `3a4d7c7017d3136f88dd08fffe733e7313538a7f` with CI run `37783268207` passing. Its new dossiers include the independent causal-lineage analysis of the Outlier cellular automaton ([Hintze & Bohm, 2026](https://doi.org/10.1038/s44260-026-00074-2)) and [Stepney's 2025 engineering framework](https://doi.org/10.1098/rstb.2024.0298). A new 10-property evidence specification distinguishes branching causal reproduction, functional heredity, self-maintenance and transformational novelty. These are important **new candidate measurement standards**, but they did **not** modify the preregistered AL02 outcomes or simulator physics. They will inform a **separately preregistered follow-up**, not retrofit stronger claims to the current data.

## Next scientific decision

Close the positive-control heredity study here. Next investigate whether inherited behaviors remain viable within resource feedback and ecological interactions, with **new environments** and an explicit no-evolution/null baseline; separately investigate whether entity identity and repair can be endogenous instead of memory-protected. A possible high-value original hypothesis is that offspring can **construct a persistent, costly ecological niche** that improves viability of unrelated descendants without anyone rewarding cooperation—then test if that effect survives removing cross-feeding and fake environmental memory. This is **untested speculation**, not an existing result.

No remote computer, always-on organism, API provider, private lab materials or evolving interpreter was deployed.

## Exact replay

```bash
# Use Python 3.11.17 and checkout experimental source SHA:
python -W error::ResourceWarning -m unittest discover -s tests -v
python -W error::ResourceWarning -m experiments.executed_heredity --seeds 5000:5064 --output-dir runs/al02-copy --source-revision 1322657ee5189c483aa12f04f14fc54c55100502
```

Store the synthetic artifact on backed-up experimental storage before GitHub's finite retention expires; Git repository stores source and verified result summaries, not the full run-state history.
