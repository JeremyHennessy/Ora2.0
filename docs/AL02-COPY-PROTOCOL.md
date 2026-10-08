# AL02-COPY v1 — Frozen executable heredity and lineage assay

**2026-10-08 · preregistration committed BEFORE evaluating held-out seeds.**
This tests only **a deliberately seeded positive-control self-copying program** in a deliberately authored finite virtual instruction ecology. It is **not** spontaneous life, unbounded evolution, autonomous agenthood, natural biochemistry or proof of consciousness.

## Scientific problem and source boundary

Previous Ora2.0 AL01 studies test synthetic chemical feedback but provide no descent. A separate substrate must demonstrate descendant construction by a *parent's executed operations*, with complete byte-level provenance. No old Ora/AgentTest code, design, phase, bug or benchmark may be used.

Public scientific prior art: Avida (Ofria & Wilke 2004, doi:10.1162/106454604773563612), evolution of complex functions in digital organisms (Lenski et al. 2003, doi:10.1038/nature01568), Taylor's requirements for open-ended digital evolution (arxiv:1507.07403). Research interpretation and negative evidence from AI-Research at main `da7297629d1208774df758029cf3efc6a9800035`, particularly `docs/artificial-life/02-historical-systems.md` and `15-experimental-verdicts-and-separation.md`. **Our virtual instructions are original model choices, not historical replication.**

## Explicitly authored environment

**Virtual material:** fixed pool of **256 uniquely numbered material units**, partitioned between available units, immutable living tapes and unfinished offspring nursery tapes. An instruction COPY consumes one available material unit and writes exactly one daughter byte. Division must consume the *already written complete nursery*, **not** call an engine clone API. Death returns material to the available pool.

**Virtual energy:** each remaining food bead of either type A or B contains **20 energy units**. Instruction execution dissipates 1; COPY additionally dissipates 1 on a successful write; DIVIDE additionally dissipates 2 if it succeeds. Successful division transfers **4 units of parent's energy into the child**, preserving the energy ledger. Exhausted programs die; leftover energy is dissipated into explicitly recorded `heat`. A and B food beads are consumed by corresponding FEED instructions. No external food or energy is replenished, no global artificial fitness bonus.

**Program alphabet, data-only integers 0..5**:
- `0 EAT_A`: try to consume one A food bead, add 20 energy if available;
- `1 EAT_B`: same for B;
- `2 COPY`: read program byte at parent's `read_head`, optionally copy-error mutate it, allocate one daughter material unit, write into nursery with complete provenance receipt, increment read head;
- `3 LOOP`: set program counter to instruction index **1** while `read_head < tape_length`; otherwise fall through;
- `4 DIVIDE`: only if the nursery has exactly `tape_length` **parent-executed** writes, energy and population budgets permit; promote written nursery material to daughter, record birth + lineage evidence, then reset parent's nursery/read head/counter. No tape duplication by engine;
- `5 NOP`: no effect besides costing one energy.

All opcodes and `LOOP`'s fixed index are researcher-selected primitives. Programs cannot invoke host operations, external tools, network access, shell, arbitrary Python, self-updating source code, OS administration or the GitHub API. A mutation changes only a child byte inside the bounded tape.

**Genesis:** exactly one author-supplied, viable four-token tape `[EAT_A,COPY,LOOP,DIVIDE]`, virtual energy=4 and population cap=64. The implemented model is *not* a spontaneous search for a viable replicator.

**World scheduler:** at each tick the next living ID in ascending cyclic order performs exactly one opcode. Death and births take effect at tick end; IDs are monotonic. A world's run terminates at 600 ticks or earlier if no organism remains. Underlying hosted clock and fixed instruction resources are environmental choices, not self-maintained biology.

**Mutation:** when copy errors are enabled, each written byte is independently replaced with a uniformly selected **different** opcode from the other five with probability 0.08, using a PRNG seeded by the world seed. When disabled, all byte copies are faithful. The type-switch `EAT_A -> EAT_B` is among possible inherited mutations. No human task rewards, no image novelty score, no external optimizer.

**World genotype:** a tape's exact ordered 4-byte sequence. Longer/shorter genomes never arise in v1; only substitutions. Reproduction may be impossible for mutant tapes. Phenotype readouts and survival are determined only by executed instructions and available A/B resources.

## Frozen sampling and controlled variants

**Implementation development seeds:** 0..7, for invariant tests only; never tune model parameters on held-out outcomes.

**First study seeds:** 5000..5063 inclusive (64 distinct PRNG streams). Exactly four matched conditions for each seed, with **600 virtual ticks** maximum, initial 12 A-food beads, 18 B-food beads, and 256 material units:

1. `mutating`: copy/error probability 0.08, all instructions enabled.
2. `faithful`: mutation probability **0**, all copying permitted.
3. `copy_disabled`: baseline tape executes but COPY is prohibited, mutation rate 0.08 (a negative/engine-duplication control).
4. `no_food`: zero A and B food beads, mutation rate 0.08 (a resource control).

Each is a **separate new world from same genesis conditions except named intervention**; the four runs share the exact random seed. The 64 worlds are independently seeded stochastic streams only in the mutation-enabled condition; the mutation-off and no-copy deterministic controls do *not* become 64 statistically independent tests just because their seeds differ.

**Total:** 256 complete experimental worlds. All failures/extinctions count; no selecting surviving seeds. Do not secretly extend horizons, change mutation rate, seed a blue-feeding organism, add A or B supply, or reset worlds because of extinctions.

## Independent audit criteria

- **Every claimed birth** must have **exactly one** actual parent-executed COPY receipt per daughter tape index, recording parent genome and source-unit identity, destination-unit identity, original opcode, emitted opcode, mutation indication, operation step and stable unique event ID. DIVIDE cannot create byte material. Child's genome/tokens must match consumed nursery.
- **Tamper control:** a fabricated engine-side birth with no COPY receipts must fail independent verification; reassignment of parent IDs and inconsistent mutated opcodes must also fail.
- **Mass ledger:** available material + parent/child tape material + unfinished nurseries = 256, with **no duplicated live material-unit IDs**.
- **Energy ledger:** living energy + food_A*20 + food_B*20 + heat = `4 + initial_food_A*20 + initial_food_B*20`, exactly at every tick. Food consumed and energy transferred at receipt, no free inheritance energy.
- **Determinism:** fixed Python version, seed, and git revision replay must yield byte-identical world records and event histories.
- **No host escape:** bytecode interpreter has no eval/import/exec/IO opcodes. No process, filesystem, or network APIs exposed through the virtual machine.

## Prespecified endpoints, without an "alive" score

**Primary:** fraction of recorded births for which the independent auditor verifies *all* material, parent, token, and executed-write receipts. If any certificate fails, classify **invalid birth evidence**; do not exclude failures.

**Negative controls:** copy-disabled should report **zero births**; no-food should report **zero births**; faithful must report only unmutated offspring and no changes in genome opcode sequence.

**Secondary:** births/world, unique descendant tape sequences, mutations by byte and their transmission, viable **grandchildren of mutated descendants**, population trajectory, world extinction, total food consumed by A/B, energy dissipation, material ledger discrepancies, incomplete nursery failures, attempted divisions that fail. Parent/child genotype associations are interpreted against valid executed writing rather than source resemblance alone.

**Explicitly exploratory functional assay:** any observed child with genome `[EAT_B,COPY,LOOP,DIVIDE]` can be tested as a new *founder* in a **separate, fresh, non-mutating** world with 0 A beads and 3 B beads, and contrasted to the original `EAT_A` parent tape under identical settings. The outcome is whether at least one birth is produced in 40 ticks. Record the first birth receipt that generated each assayed genotype. This assay **tests a pre-existing resource-choice opcode, not an independently invented cognitive ability**. If no such mutant occurs, report absence honestly.

**Uncertainty:** descriptive world-level counts and, only for genuinely varying quantities, bootstrap intervals clustered by seed (fixed resampling seed 20261008 and 4,000 resamples). Never treat correlated offspring or ticks as independent evolutionary experiments.

**Smoke tests:** 0..7 may check mechanics, resource partition, mutation, receipt and no-clone controls; data from those cannot change frozen study settings.

## Pass/fail and interpretive boundaries

- **Pass G2-a (engineering):** at least one valid birth, 100% auditable receipts, zero simulator-invariant breaches, zero copy-disabled and no-food births.
- **G2-b (limited heredity):** actual parent byte copying and repeatable transmission of distinct child mutations to grandchildren beyond engine copying or source-only environmental resemblance; do not claim functional evolution if none occurs.
- **G2-c (environmental function):** independent, held-out nutrient environment differentiates observed inherited nutrient choices; this still is programmer-authored functional capability and does **not** establish open-ended evolutionary invention.
- If no viable offspring, report result; do not tune world to produce living-looking behavior until a **newly committed protocol** is established.
- Mutation and natural selection are not objectives; population stability may favor a simple replicator. No assumption of increased intelligence.
- A self-copying finite virtual program and its host-defined tape boundary/energy costs do **not** prove self-produced individuality, metabolism, learning, sentience or organismhood.
- Retain failed worlds and null results, no organism is authorized access to any live system.

## Exact execution

After implementation and immutable pre-holdout tests:

```bash
python -m unittest discover -s tests -v
python -m experiments.executed_heredity --seeds 5000:5064 --output-dir runs/al02-copy --source-revision <exact-git-sha>
```

Archive all world summary records, full operation/write/birth events, full lineage certificates, run manifests and checksums. No heavyweight dependency or machine hookup. Original study protocol must **not** be changed in response to holdout results.
