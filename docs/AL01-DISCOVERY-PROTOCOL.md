# AL01-DISCOVERY v1 — Precommitted random-network feedback study

**Protocol frozen in source control before evaluating study worlds.** Prepared 2026-10-08. This is an **original miniature artificial-chemistry model**, not a reproduction of Liu–Sumpter chemistry, any real thermodynamics, spontaneous biogenesis or a digital organism.

## Research question

When a fixed distribution of **previously unscreened** catalytic networks is exposed to bounded nutrient flow and constituent decay, do some randomly generated reaction graphs show **counterfactual recovery** that depends on an internal cyclic catalytic connection?

This tests a more interesting claim than AL01-CAL (which explicitly authored a restorative loop). It **does not** test organism boundaries, inherited functionality, neural cognition or indefinitely open-ended change.

## Literature intake

- `AI-Research` at `47dd59bf4de997e5d0e6508fee305973679bac3b`, especially `docs/artificial-life/12-chemical-replication-full-review.md` and `19-three-paper-methodology-comparison.md`. Literature sources do **not** include executable work from the previous Ora.
- Liu and Sumpter (2018), https://doi.org/10.1074/jbc.RA118.003795 — reaction-set self-replication requires more than a graph cycle, and energy and resource conditions matter.
- Varanasi and Korenaga (2026), https://doi.org/10.1103/nmt5-qsym — probabilistic emergence of RAF sets and finite-size catalytic cores. **Research abstract inspected**, not independently reproduced.
- Hordijk and Steel (2024), https://pmc.ncbi.nlm.nih.gov/articles/PMC11286130/ — structure and algorithms for autocatalytic networks. A graph cycle here is **not** itself a mathematical RAF proof.
- de Pinho and Sinapayen (2026), https://arxiv.org/abs/2603.01701 — evolving-population activity can lose apparent open-endedness under a neutral shadow; no metric in this protocol constitutes OEE.
- This protocol is a **new experimental design**, and we make **no claim of world-first originality or scientific discovery** before a broader novelty audit and replication.

## Unbiased network universe

- Each sampled network has **6 distinguishable internal species** `X0...X5`; nutrient `S`; inert waste `W`. Every molecule counts as one abstract mass unit, not a physically realistic molecular weight.
- For each network seed, independently test every ordered directed pair `i != j`, visiting i then j in ascending order. Include arc `Xi -> Xj` if `random.Random(seed).random() < 0.26`; **no self-loops**. Empty/acyclic graphs remain in the denominator.
- An included arc permits the artificial reaction `S + Xi -> Xi + Xj`. Catalyst Xi remains. Without S or Xi, the arc cannot produce Xj.
- Universal non-catalytic basal reaction `S -> Xk`, k uniformly selected in 0..5, is permitted with probability 0.02 **per encounter**, so a network with no initialized internal species can become active. This is an **externally designed spontaneous-source rule**, not natural emergence from real chemistry.
- Internal decay: each molecule Xi independently converts to W with probability 0.10 each step.
- Environment feeds exactly 5 S each step unless resource denial is active. Each step performs exactly 10 ordered reaction encounters. At an encounter, if S>0, first draw the basal reaction Bernoulli(0.02). If not selected, choose one of: no reaction weight 1, or each enabled catalytic arc weight `0.12 * Xi_count`; draw proportionally, visiting arcs lexicographically. Selected catalysis consumes one S and produces one target molecule. Then sample independent decay for all current Xi molecules in ascending species order.
- Initial reactor state: S=30, all Xi=0, W=0. No viable pattern/replicator is inserted at startup. No molecule can appear except through declared nutrient feed or conversion. No reward, goal or agent policy exists.

These fixed choices are **computational conveniences**, not borrowed experimental parameters or optimized values; negative outcomes are acceptable. `random.Random` reproducibility is scoped to the pinned Python runtime.

## Topology intervention, preselected without seeing dynamics

Compute all cycle edges: directed arc (i,j) belongs to a directed cycle if a directed path from j to i exists in the *original complete graph*. Preselect:
- `cycle_edge` = lexicographically first such edge, if any.
- `noncycle_edge` = lexicographically first edge that is not part of any cycle, if any.
- `target` = j of `cycle_edge`, if any.
This is **graph-blind to results and observed species concentrations**. A cycle is *not* sufficient evidence of functional organization.

A topology-rewired control receives exactly the same number of arcs selected uniformly without replacement from the 30 possible arcs by `random.Random(network_seed ^ 0x5A17)`. Rewiring does **not** preserve in/out-degree, and may have its own cycles; report that limitation. It does preserve species count, possible arc count and cost budget.

## Design and intervention protocol

- **Development-only validation seeds:** network seeds 0..7, trajectory replicates 0..1. These are for code invariants/schema only; do not adjust parameters after inspecting their outcomes.
- **First evaluation seeds:** 80 networks with seeds 7000..7079 inclusive, each with 3 independent trajectory RNG seeds `30000 + network_seed*10 + replica_index`, replica indices 0..2. Do not pick only the living-looking networks.
- Warmup: 70 steps in original network with feed and basal reactions.
- Fork a byte-identical reactor state and independent PRNG object with identical state into **six** conditions, including identical destructive perturbation of every Xi: convert floor(0.60 * Xi) units into W. Missing species stay missing. The network selected for an ablation is independent of the warmup state.
- Observe 55 more steps:
  1. `intact`: original arcs, nutrient feed remains on.
  2. `cycle_edge_removed`: preselected cycle arc removed; when no cycle exists, run an explicitly labeled **no-op control**, *not* a fake knockout.
  3. `noncycle_edge_removed`: preselected acyclic arc removed; if no such arc exists, labeled **no-op**.
  4. `rewired`: independently sampled same-count arcs; **not** considered degree-matched.
  5. `basal_only`: all catalysis disabled, basal source and feed unchanged.
  6. `resource_denied`: original arcs retained, immediately convert remaining S to W, no more external S.
- **Conservation:** S + Σ Xi + W = original molecule count (30) + cumulative externally supplied S. The clock counts only simulation steps. If conservation fails, the run is **invalid**.
- No engine-based rebuilding, protected organism state or repair callback exists.

## Predeclared measures and denominator protections

**Eligibility** is defined solely by graph topology and *pre-damage* counts: the network has a cycle edge, its fixed target count at the fork is >=6 and at least 3 target molecules are removed by damage. Every **noneligible** trajectory remains in the sampled universe and is reported, never called an experimental success.

**Sustained target recovery:** on an eligible trajectory, target Xi reaches >=0.75 of *its own exact pre-damage abundance* for **at least 5 consecutive steps**, at least once during the 55 post-perturbation steps. The target is selected **without inspecting outcomes**. No outcome is defined as individual-organism survival.

**Primary:** within eligible trajectories, paired recovery difference `intact - cycle_edge_removed` with uncertainty bootstrapped by **network seed cluster** (not individual correlated frames or 3 trajectories as independent chemistry universes). Also report eligible counts, total network counts, all six variant recovery rates and paired discordance; if none eligible, label inconclusive.

**Secondary:** pathwise mass-conservation residual (must =0), number of networks containing directed cycles, eligible/evaluable networks, target recovery times, ongoing net reaction activity and resource consumption, acyclic-arc ablation difference in networks where that arc exists, contrast with basal-only / denied / rewired conditions, and all failures/extinctions. No composite "alive score".

**Screen-positive network (exploratory classification, not life):** at least two of its three replicate trajectories are eligible and have `intact=true`, `cycle_edge_removed=false`, and `basal_only=false`. This selection creates a **descriptive screen**, not independent confirmatory evidence. Candidate networks must receive newly sampled independent evaluation seeds in a *future separate trial* before claiming a reproducible effect.

**Uncertainty:** 4,000 cluster-bootstrap resamples, deterministic bootstrap seed 20261008; descriptive 95% percentile interval, no unadjusted p-value for exploratory metrics. Mark worlds/replicates and environment rules precisely.

## Falsifiers and limits

- If the difference is zero/negative or collapse/inelegibility dominates, report it. Do not silently change arc probability, decay, thresholds or selection rules.
- If reaction-network recovery is explained by basal-only recovery, random rewiring or a trivial single incoming edge, do not call it internally produced autonomy.
- Destroying one preselected cyclic edge can be **trivially lethal** if it is the only production route to the target. Keep exact in-degree and edge information and examine this as a null explanation.
- Basal births and indefinite future feed are externally supplied. An intact positive is **not** an organism, self-produced membrane or energy-independent metabolism.
- Finite graphs with six species cannot exhibit unbounded structural novelty. None of these simulations establishes inheritance, reproduction, intelligence, consciousness, or genuine life.

## Reproduction and custody

Implement in new `experiments/network_discovery.py` with Python stdlib only and no external network, agent tools or machine permissions. Add independent unit tests for deterministic replay, graph selection, branching controls, conservation, ineligibility and summary calculations. Run protocol-frozen holdout only after tests pass; archive all network descriptors, trajectories and controls, including zeros. CI workflow outputs are synthetic and have finite retention; no permanent organisms run through GitHub.

Provisional command (after implementation):

```bash
python -m unittest discover -s tests -v
python -m experiments.network_discovery --output-dir runs/al01-discovery --networks 7000:7080 --replicates 3
```

**Stop and separately document deviations instead of retroactively rewriting this protocol.**
