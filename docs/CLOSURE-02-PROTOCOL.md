# CLOSURE-02-FUNCTION v1 — Precommitted cost-controlled shell function

**Date:** 2026-10-08. **Status at this source revision: protocol committed before all new held-out outcomes.** An independently designed bounded test of a *prewritten* spatial chemistry. **Not** an organism, autopoiesis, de novo cell origin, reproduction, intelligence or a scientific-world-first claim.

## Why this is different from CLOSURE-01

[CLOSURE-01](CLOSURE-01-SPATIAL-RESULTS.md) found intact A/R core recovery in 37/93 eligible spatial worlds, compared with 79/93 when M synthesis was disabled. Turning off only M's authored diffusion effect produced 33/93 core recoveries. The old **dual** score was partly circular because it required making M. Therefore this experiment must NOT score a shell based on its own existence or appearance.

Scientific intake from AI-Research, last verified source `63914404809d799923832f83b0b2dc0ae6cb8bc3` (offline tests green): [Banzhaf et al. 2016 method review](https://github.com/JeremyHennessy/AI-Research/blob/63914404809d799923832f83b0b2dc0ae6cb8bc3/docs/artificial-life/36-banzhaf-2016-open-ended-novelty-full-review.md) separates simulator-installed individuality/fitness/replication from emergent mechanism; [pass-8 operational rubric](https://github.com/JeremyHennessy/AI-Research/blob/63914404809d799923832f83b0b2dc0ae6cb8bc3/docs/artificial-life/40-pass8-peer-review-and-test-rubric.md) requires independent functional measurement and matched nulls. Neither paper is reproduced in this experiment. No legacy Ora/AgentTest design, phase or failure logic may influence this project.

## Original physics held constant

Import `experiments.closure_spatial` (original source left **unmodified**) and use exactly its:
- 9×9 periodic lattice, 5 abstract species S/A/R/M/W, reaction constants/encounters, basal S→A conversion, A/R/M decay, synchronous cardinal diffusion, M-dependent A/R hop law, 8 S per step external supply, 60 warmup steps, 60 post-damage steps.
- Three fixed origin classes: `clustered` (pre-seeded A/R in one cell), `dispersed` (same total A/R at pseudo-random sites), `nutrient_only` (no pre-seeded A/R but **programmer-installed** basal activation). **No new metabolic or biological rules**.
- Pre-damage target = densest A+R 3×3 region, row-major tie; eligibility = core A≥4, core R≥4 and at least two ring cells with M. Damage A/R by floor(0.55×cell counts) in chosen 3×3; ring M by floor(0.65×cell M). Use exactly the parent `damage` and `region` functions. NO target re-selection after interventions.
- Full identical warmup state and `random.Random` internal state copied to every arm before damage; all local A/R/M perturbations identical.

**Single experimental extension:** a shell-production reaction that would normally spend one S to add one M may instead spend one S and add one inert W at the **same destination cell**. All four catalytic reaction-selection weights and its consumed reaction encounter remain otherwise identical. This is called a **ghost shell**, not a real shell. Different arms may *subsequently diverge in number of production events* because the new M density changes diffusion. Therefore it is **cost-matched for each reaction event**, **not globally flux-, energy- or trajectory-matched**. No physical thermodynamic free-energy model is claimed.

Record an independent **movement proposal/acceptance ledger** by checking, at each A/R diffusion proposal, whether its *original source* and proposed cardinal destination straddle the fixed pre-damage 3×3 core. Count proposals and accepted hops in both directions separately; the denominator for outward escape is the count of **outward proposals**, not population or survival. The shell-imposed hop law itself reduces migration by construction, so a lower escape rate **alone** cannot establish organismal protection.

## Frozen five arms

1. `shell_effect`: synthesize M and use M-dependent catalyst permeability (equivalent to prior `intact` physics).
2. `shell_inert`: synthesize M at same cost; catalyst hops use constant 0.24 (equivalent to `permeability_null`).
3. `ghost_effect`: consume S and reaction opportunity to produce W instead of M; surviving initial pre-damage M can still affect diffusion until decay.
4. `ghost_inert`: same ghost W production and consumption; M cannot affect catalyst diffusion.
5. `no_shell`: eliminate M synthesis channels and their S/reaction costs (equivalent to prior `no_M_synthesis`).

All arms retain researcher-provided S replenishment. No agent, organism, reward, health bar, repair callback, protected cell or host-system interaction exists.

## Seed identity and fixed run budget

**Development only**: seeds `0..7` test conservation, equivalence to old physics, protection of origin/target/PRNG and output contracts. Do not tune chemistry, eligibility, scoring or held-out window from development results.

**Evaluation**: **64 fresh seed IDs 6400..6463 inclusive**, all three origins per seed and all five arms per origin: **192 paired initial worlds**, **960 treatment runs**, **57,600 post-damage step traces** at 60 each. Retain every ineligible, extinct/inactive and failed world. Treat 64 seed groups as independent statistical resampling clusters: the three modes share seeds and the five arms share checkpoints, not 960 independent worlds.

## Outcomes frozen BEFORE evaluation

**Primary outcome 1: membrane-independent core recovery.** On an eligible pre-damage world, both core A and core R exceed or equal 70% of **their respective pre-damage counts for three consecutive steps** during 60 post-damage steps. This is the existing CLOSURE-01 *core-only* endpoint; **M production/coverage is nowhere in the score**. Report by origin and all origins combined, intact vs shell_inert, ghost_effect, ghost_inert and no_shell. Include eligible/full denominators and pair discordance, plus descriptive 95% percentile confidence intervals from **4,000 seed-group bootstrap resamples**, fixed seed `20261008`.

**Primary outcome 2: normalized proposed-boundary escape.** Report per arm total A/R diffusion proposals from inside to outside the *fixed* core and the fraction that were accepted, along with same figures for **outside→inside**. Compare `shell_effect - shell_inert` to test the *direct programmed transport function*, not recovery. Also compare `ghost_effect - ghost_inert` to isolate benefit of M remaining from the pre-damage checkpoint. If a world had zero proposals, mark its escape rate null, **never silently drop the world**. These fractions are per molecule proposal, NOT independent statistical replicates; ecological inference must still cluster at seed level.

**Secondary independent endpoints:** total new A, new R, new M and new W via ghost reactions; A+R synthesis per spent S by declared reaction channel; global A/R/M/W and externally injected substrate, end-of-run center occupancy, count of qualifying worlds, incomplete/dead worlds, original core/ring M at warmup, initial and final molecule conservation residuals. Do not collapse to a new 'alive score'.

**Interpretation in advance:**
- If `shell_effect` reduces outward hops **without** improving core recovery relative to `shell_inert`, report *a prewritten diffusion barrier without established repair benefit*.
- If ghost and shell arms differ after removing production costs, explicitly separate **M material density effects** from loss of S production opportunity. Ghost's costs are matched only event-by-event, not trajectory totals.
- If `no_shell` still recovers better, treat the current membrane synthesis scheme as **disfavored** for organismal self-maintenance and prioritize an independent substrate, not higher M rates.
- If the complete study has very few eligible worlds, report *inconclusive*; never relax target thresholds after observing outcome.
- An apparent recovery in `nutrient_only` is causally dependent on the fixed basal activation S→A; **not spontaneous biogenesis**.
- Any forged conservation, unequal fork, non-monotonic trace count or source-revision mismatch invalidates the assay; stop rather than selecting only good worlds.

## Implementation boundary

New standard-library `experiments/closure02_functional.py`, `tests/test_closure02_functional.py`, and its own GitHub-hosted Actions workflow, with full hash-verified JSONL outputs. Reuse/validate the old CLOSURE-01 physics **without editing the source file or any prior study history**. Keep science code, analyst and future observer separate.

No continuous simulation, GPU, LLM, OpenAI API, paid compute, local D: automation, new GitHub Actions self-hosted runner, cloud computer or network-facing agent. The recent local Codex report accepting bounded Windows RUNTIME-01 recovery is separately recorded in `docs/RUNTIME-01-WINDOWS-ACCEPTANCE-2026-10-08.md`; it does **not** establish checkpoint/restart for this spatial world. No external machine has been operated by this commit.

**Predeclared invocation once tests pass:**

```bash
python -W error::ResourceWarning -m unittest discover -s tests -v
python -W error::ResourceWarning -m experiments.closure02_functional --seeds 6400:6464 --output-dir runs/closure02-functional --source-revision <git_commit>
```

Preserve failures, every seeded origin, world-level records, movement and reaction ledgers, and per-tick checksum receipts. GitHub artifacts have finite retention; local D: files are not drive-failure backups.
