# AL01-RVCS — preregistered redundant catalytic maintenance stress test

**Frozen before all fresh experimental outcomes, 2026-10-08.** This is an original **research hypothesis** and a synthetic reaction-network experiment, **not** a claim that this idea is globally unprecedented or that the system is alive.

## Scientific question

Can a randomly sampled catalytic network maintain a damaged constituent through **alternative cyclic synthesis pathways**, so that loss of either path alone is tolerated, but loss of both causes failure, when a separately chosen two-edge deletion does not?

Unlike [AL01-DISCOVERY](AL01-DISCOVERY-RESULTS.md), this design **requires that the target have at least three distinct incoming production routes**, specifically to remove the earlier trivial one-edge-only confound. The experiment still measures an *authored graph chemistry*, not emergent cell boundaries or true metabolic organismhood.

### Motivating evidence / differentiation

- [AI-Research chemistry full audit](https://github.com/JeremyHennessy/AI-Research/blob/da7297629d1208774df758029cf3efc6a9800035/docs/artificial-life/12-chemical-replication-full-review.md): graph cycles are not equivalent to chemically self-producing organizations.
- [Hordijk–Steel catalytic network analysis (2024)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11286130/): catalytic connectivity matters but is not identical to stoichiometric amplification.
- [Varanasi–Korenaga 2026](https://doi.org/10.1103/nmt5-qsym): finite-size catalytic-core emergence has quantifiable network conditions.
- Independent project [N2: redundancy-versus-closure stress test](NEW-RESEARCH-HYPOTHESES.md), proposed **after** the first Ora2.0 survey's post-hoc degree audit. The next results must be evaluated separately, not pooled into the preceding confirmatory analysis.

## Frozen network and reaction physics

**Exactly preserve** the standard library `Protocol()` and `step()` reaction law in `experiments/network_discovery.py` as executed at source commit `dacab66383b2ddb7384fcec2b2a4f1b6fb6eee00`:
- Six internal species X0..X5, one nutrient S and waste W.
- 30 possible directed arcs excluding self-loops, drawn independently with probability 0.26 from each graph seed.
- Arc `i->j` catalyzes `S+Xi -> Xi+Xj` at encounter weight `0.12*Xi`; 10 encounter attempts/step.
- Basal `S->random X` p=0.02 per encounter; spontaneous basal source is an **external model choice**, not derived abiogenesis.
- 0.10 per-molecule decay into waste per step; +5 S/step normal feed.
- All mass accounted; all molecules are same abstract unit, not physical free energy.
- Initial S=30, all Xi=0; warmup 70 steps; fork identical state + PRNG after damaging each Xi by floor(0.60*Xi); follow-up 55 steps.

Never select a graph based on its observed viability. No training, rewards, external agents, arbitrary host code or internet access.

## Graph-only target and cut-set selection

For a graph, identify all arcs belonging to **directed cycles** using graph reachability (no dynamics or trajectory data). For each candidate target species t in increasing index order:
1. t has **at least 3 distinct incoming arcs** in the sampled graph.
2. **At least 2** incoming arcs belong to some directed cycle.
3. At least **2 other arcs** (target != t) exist for an equal-*edge-count* sham.
Select the first qualifying t. Choose `cut_first` and `cut_second` as the lexicographically first two distinct cyclic incoming arcs. Choose `sham_two` as the lexicographically first two arcs whose **destination differs from t**. All selection occurs **before simulation**, blind to flux and outcome.

Graphs lacking such a target remain in the **full 144-graph denominator**, with explicit reason `no_structural_candidate`. Their simulated treatments run as no-op single/double/sham cuts, but can never be counted as recovered or as screen positive. Sham arcs are **not matched on realized reaction flux**; this is an explicit alternative explanation and future improvement.

After warmup, a trajectory is `eligible` only if the preselected t has at least 6 molecules and perturbation removes at least 3. Lack of abundance remains **ineligible**, never quietly discarded.

## Seven forked treatments

1. `intact`: original reaction graph.
2. `cut_first`: first selected cyclic incoming arc into t disabled.
3. `cut_second`: second selected cyclic incoming arc into t disabled.
4. `cut_both`: both preselected cyclic incoming arcs disabled. Because t has >=3 incoming arcs, **at least one direct synthesis route remains**.
5. `sham_two`: two preselected non-target arcs disabled, an equal-count but **not flux-matched** control.
6. `basal_only`: all catalytic arcs disabled (basal chemistry remains).
7. `resource_denied`: no future nutrient inflow and conversion of remaining S to W at intervention, all catalytic arcs retained.

Every treatment receives the **same pre-intervention state, identical damage to all Xi**, and a **copied RNG state**. Branches diverge naturally after interventions. No engine repair.

## Frozen sample, outcomes, and denominators

- **144 new graph seeds**: 9000..9143 inclusive (do not mix with prior 7000..7079).
- **3 stochastic trajectories per graph**, seed `50000 + network_seed*10 + replica_index`, indices 0,1,2.
- 144 × 3 = **432** independent stochastic trajectories nested in 144 sampled chemistry universes; **3,024** seven-condition treatment runs; **166,320** post-intervention step events, all retained.
- **Sustained target recovery:** Xi(t) >= 0.75 × the same trajectory's pre-damage Xi(t) for **5 consecutive steps** within the 55 observation steps, identical to the preceding study.
- **Primary endpoint: redundancy signature** within an eligible trajectory if:
  `intact`, `cut_first`, `cut_second` and `sham_two` each achieve sustained recovery; `cut_both`, `basal_only` and `resource_denied` each **fail**. Count it by trajectory and across **distinct graph seeds**.
- **Screen-positive graph:** at least **2 of 3** trajectories satisfy that exact full signature. Screens are *not validated general discoveries*; screen positives require an independent new-seed study.
- **Secondary:** fractions recovering under each of seven treatments among *all eligible*; `intact - cut_both` and `sham_two - cut_both` paired differences; structural eligibility fraction across all 144 graphs; single-cut failures, sham failures, complete dropout, count of graph species, target in-degree, and all conservation residuals.
- **Uncertainty:** descriptive 95% percentiles from **4,000 bootstrap re-samples of graph clusters**, not from 432 pseudo-independent chemistries, random bootstrap seed `20261009`. No inferential p-value; no composite life/aliveness score.
- **Evaluation and selection remain distinct:** code may use protocol smoke seeds 0..7 for tests/replay, but these must not tune experiment parameters. The actual 9000..9143 heldout is run only after test suite passes.

## Negative outcomes and confounds that must be retained

- No or very few eligible graphs: mark the experiment **underpowered/inconclusive**, do not reduce the three-input requirement after seeing results.
- No signature: **refuted under this toy model and protocol**, do not loosen criteria retroactively.
- Cutting two incoming arcs may lower target production *purely kinetically*, even if a third route survives. A positive is at most evidence of **redundancy-like dependency in the specified model**, not autopoiesis, metabolism, self-organizing spatial boundary or molecular cooperation.
- Chosen sham arcs can affect upstream production and aren't rate matched; its control is imperfect and any ambiguous result must be reported.
- Basal source and feed rules remain authored, and the reaction graph was sampled by a designer's probability distribution.
- Mass conservation detects record consistency, **not** thermodynamic plausibility.
- This contains no organism identities, births, genotypes, reproduction, inheritance, evolution, intelligence or consciousness.

## Implementation, evidence and stopping

Write a new module `experiments/redundancy_probe.py` **without altering** the already verified AL01-DISCOVERY or AL01-CAL mechanics. Import their frozen step rules as a measurement substrate. Add tests that assert topology eligibility, disjoint cuts, third remaining target producer, equal cloned post-damage state and PRNG, null and all-graph retention, replay, and SHA-256 event-trace integrity. Execute GitHub Actions with synthetic outputs retained as artifacts.

Do not call a network "living" after any possible positive outcome. The next objective remains **independently falsifiable biological organization**, not a human-chatbot goal.
