# AL03-NICHE v1 — Preregistered byproduct ecology and inherited resource choice

**Frozen 2026-10-08 before evaluating study seed worlds.** This is a self-contained synthetic ecology experiment. **No claim of spontaneous life, endogenous metabolism, executed genome copying or unprecedented research discovery.**

## Research input, separation and original hypothesis

At this checkpoint the latest [AI-Research](https://github.com/JeremyHennessy/AI-Research) main SHA is `999d341d156ce88950993e4ae6e43fa133a612a7`, with validation run `37787540852` **success**. Consult its Stepney (2025) complete review (autopoiesis vs agency vs open-ended adaptation), Stringmol (2016) full review (resource/decay selection loopholes), and Physis/Stringmol semantic-closure comparison (program change != changed computational meaning). These published sources motivate skepticism; they do **not** establish this study's outcomes.

**Original project hypothesis AL-H-ECO1 (untested; historical novelty not established):** given environmental resource processing that creates a chemically distinct *usable byproduct*, an initially homogeneous heritable virtual population may develop an **inherited downstream resource specialization** through unbiased role changes. The same effect should disappear when the byproduct is removed and should weaken when the role is not reliably inherited. No human-designed intelligence reward or visual novelty scorer is provided.

This explicitly tests **ecological selection**, not AL02's executed copying. The role bit and reproduction rule here are **simulator-authored**, so this study's descendant lineage cannot independently satisfy AL02's per-byte copying criterion. Do not merge evidence from separate substrates into a single “living creature” score.

## Fully defined abstract physics

**Discrete well-mixed world**, no spatial boundaries or latent self-produced compartments. Three abstract external molecule types A, B and inert W:
- A carries **20 artificial potential-energy units**.
- B carries **8 potential units**.
- W carries zero potential.
- Matter conserved: `A + B + W = initial_A + cumulative_A_supply`.
- Energy conserved: `20*A + 8*B + sum(living_internal_energy) + dissipated_heat = 20*initial_A + founder_energy + 20*cumulative_A_supply`.

This is **numerical energy bookkeeping**, not realistic thermodynamics; no claim about physical free energy or biological metabolism.

Each virtual entity has a single designer-defined role/genotype symbol **P** (A converter/“producer”) or **C** (B converter/“consumer”), finite internal energy, generation number, body material ID and ancestry record. There are **40 uniquely numbered body slots**; initially only slot 0 is used. A birth allocates a free slot, and death releases its slot. A role mutation changes only P↔C.

The **genesis** is one intentionally seeded P entity, initial internal energy **8**, **18 A** resources, **0 B** and **0 W**. The environment is not a primordial random origin-of-life experiment.

### Precommitted step mechanics

One entity acts on each simulated tick; ascending cyclic actor ID order. The world ends after **480 ticks**, or sooner if no entity remains. No resurrection.

1. On every **third tick** (3,6,9...) exactly 1 A enters the reactor unless `no_inflow` control; log external added matter +20 potential energy.
2. The selected entity spends 1 energy to inert heat for its action. If it has no energy, die without acting.
3. A **P** with available A consumes 1 A, receives 12 usable energy and produces exactly **1 B** carrying the remaining 8 energy. In `byproduct_sink` control, produce W instead and dissipate the remaining 8 as heat. No energy appears for free.
4. A **C** with available B consumes 1 B, converts it to W and receives 8 usable energy.
5. A P without A, or a C without B, obtains no input but still pays its instruction/action cost.
6. After its action, if its energy is **at least 26**, a body slot is free and population is below cap 40, reproduce **once**: transfer 8 energy to a new daughter, dissipate 2 as heat, decrement parent's energy by 10. The daughter begins with energy8, generation parent+1 and one available material slot. **This engine-mediated division is *not* an executed copying operation.**
7. Depending on treatment, offspring role is inherited with per-birth mutation probability **0.08** (P↔C), or inherited perfectly, or independently drawn with P=0.92,C=0.08 regardless of parent. This third treatment is a **nonheritable comparator** with matched *P→C production probability* but a different overall role-change rate; do not claim equal mutation budget.
8. After action/division, any entity with zero energy dies, releasing body slot. Its remaining energy, if any, is dissipated to heat on death. No immune state, external maintenance callback, or lifesaving script.

On birth a unique increasing daughter ID and parent ID are logged, with parent/daughter roles and exact resource events. Inheritance is *role transmission via the engine*, not an evolved replicase or new genotype-to-phenotype mapping.

## Matched five-arm design (fresh seeds, no tuning)

**Development tests only**: seeds 0..7 may verify conservation and event format; no tuning to target research outcome.

**Frozen evaluation**: **48 independent world seeds 8000..8047 inclusive**, each run once for 480 ticks maximum under all five treatments (240 worlds total), matching RNG seed across treatments but permitting natural divergence:

- **heritable** — P→B byproduct, heritable role mutations at p=0.08.
- **byproduct_sink** — same mutation semantics, but P turns A into W and dissipates B's residual 8 potential as heat.
- **nonheritable_role** — normal byproduct production, but daughter role drawn P with probability 0.92 / C 0.08 independent of parent.
- **mutation_disabled** — normal byproduct production, daughter always inherits parent's role, so genesis-P descendants remain P.
- **no_inflow** — normal byproduct and heritable mutation, but no periodic addition of new A. Food A initial supply is finite.

All birth/death and failed-world records remain in sample; no lucky lineage cherry-picking. Fixed physical mechanics shared across arms except named treatment.

## Outcome definitions frozen before held-out trial

**Primary world-level outcome: established downstream-feeding lineage.** A world passes only if it has an unbroken ancestry sequence originating from a **P→C descendant role change**, then a C parent successfully consumes B **and** gives birth to a C daughter that herself later successfully consumes B. A C birth or genotype similarity alone is not enough; actual per-tick B-resource conversion receipts required. This tests downstream *role persistence and ecological viability*, not invented intelligence.

**Primary contrasts:** fraction of the 48 seeds meeting the event criterion under `heritable` minus `byproduct_sink` and `nonheritable_role`. Report per-world paired discordance, descriptive 95% paired-world bootstrap percentiles with **4,000** resamples (fixed analysis seed 20261008), and full sample denominators. No unpowered significance claims.

**Secondary:** total births, P→C switches, B molecules generated and consumed, viable C daughters that themselves consume B, generation depth, extinction-by-480 fraction, peak population, material slot reuse after death, material/energy residual, externally added A, remaining A/B/W/heat, unique role-pattern genealogies. Report effects even if primary fails.

**Stop/falsification signals:**
- **Invalid model:** any mass/energy discrepancy or simultaneous occupation of a body slot; abort without suppressing the failing world.
- **No ecological effect:** byproduct sink allows comparable C-to-C B-fed lineages despite no B source, or the heritable arm does not exceed controls; retain null result, do **not** tune budgets or mutation rate after seeing the outcomes.
- **No selective/hereditary benefit:** role expression differs, but descendants' successful resource use does not persist beyond nonheritable control.
- **External mechanism dominates:** the result is driven by programmer-authored role/energy budgets, initial mutant supply, fixed population cap, or calendar inflow; report such dependence rather than proclaiming open-ended self-organization.
- **Long-horizon fragility:** lineages collapse at 480 ticks or only a tiny subset of seeds sustain activity; preserve all extinctions.

**Interpretation excludes** spontaneous ecosystem-origin, endogenous organism boundary, executed genome copying, self-chosen agency, neural learning, new interpreter semantics, consciousness or unlimited innovation. The P and C resource reactions are predefined and finite.

## Implementation and validation boundary

Use an entirely new `experiments/niche_selection.py` standard-library-only module and independent tests. **Do not edit AL01, AL02, AL07 source or prior protocols.** Track every distinct virtual body ID and globally conserved energy/matter; record deterministic seed, environment, both event and per-world traces, and hashes. Run all existing tests *first*, then the full 48-seed experiment on GitHub Actions and archive all cases. Every software failure or scientifically negative world is a retained result.

**Frozen command (once implemented):**
```bash
python -W error::ResourceWarning -m unittest discover -s tests -v
python -m experiments.niche_selection --seeds 8000:8048 --output-dir runs/al03-niche --source-revision <exact-commit>
```

Future studies, **separately preregistered**: externally forced B delivery under mass/energy-matched flux (not in this experiment), shared spatial niches/trace memory, and—only after both modules independently work—AL02-style parent-executed reproduction inside ecological worlds. Do not claim true organismal autopoiesis by combining unrelated successes.
