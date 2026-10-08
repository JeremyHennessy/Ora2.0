# Experiment Plan — Evidence Before Claims

**Status:** proposal; not executed.

The laboratory advances through explicit hypotheses and reproducible results, not phase numbers or the appearance of progress. The stages below are research gates, not a commitment to a particular evolutionary outcome.

## Stage 0: Evidence and comparison

- Review relevant AI-Research dossiers and original ALife literature.
- Compare artificial-chemistry, digital-evolution and developmental systems: minimal mechanism, known failures, resource cost, independent controls, reproduction availability.
- Select one *smallest discriminating experiment per candidate*. Do not optimize a single favorite against weak comparators.
- Define observation and outcome metrics *before* experimental runs.

**Pass condition:** documented candidate comparison, falsifiers, fixed protocols, budget constraints, and clean references.

## Stage 1: Reproducible substrate harness

- Deterministic/seeded environment stepping and simulation time.
- Explicit resource/boundary rules with invariant checks.
- Event journal with action / environmental transition / observation / checkpoint IDs.
- Atomic checkpoints, checksum or hash validation, and crash/restart replay.
- Separation between simulation engine, stored state, analysis, and optional viewer.
- Tests for determinism, failed restart, corrupted checkpoints, and resource accounting.

**Pass condition:** same seed+revision+configuration yields the same state trajectory and independent observer produces the same measurements on at least two fresh runs.

## Stage 2: Minimal life-like mechanisms

For each research candidate, test the minimal plausible mechanism for persistent organizational structure and adaptive change. Avoid anthropomorphic interfaces or preprogrammed solutions.

**Controls:** dead/passive artifacts, non-heritable variants, frozen/non-learning variants, randomized local rules, shuffled environments and controlled disturbance tests (as scientifically applicable).

**Pass condition:** at least one prespecified measurable effect beats suitable matched controls repeatedly, with documented failures. No automatic “life” label.

## Stage 3: Evolution, individual learning and ecological novelty

Vary environmental conditions, interaction budgets and selection pressures; distinguish within-lifetime adaptation from hereditary selection. Test hidden environmental perturbations and unseen mechanism combinations.

**Pass condition:** evidence of transfer or repeatable functional novelty that survives ablations, rather than just increasing population or animation complexity.

## Stage 4: Persistent isolated runtime

Only once the harness and checkpoint recovery work: deploy simulations to the dedicated computer using an unprivileged service with disk quotas, backups, bounded CPU/GPU usage, restart semantics and read-only observer telemetry.

**Pass condition:** independently confirm bounded uptime, exact restart recovery, storage integrity, and security isolation. Continuous running itself does not prove scientific progress.

## Stage 5: Long-horizon experiments

Run multiple independent lineages, preservation protocols, perturbation studies and scale comparisons. Investigate whether functional novelty plateaus, and publish negative findings to the project evidence log.

**Pass condition:** repeated, falsifiable findings with holdouts. No implied guarantee of open-ended evolution.

## Research record per run

Record: hypothesis ID, candidate/substrate version, Git commit, immutable config, fixed seed(s), environment rules, machine profile, wall time, simulated time, resource budgets, snapshot and event hashes, analysis commit, results and confidence intervals, controls, falsifiers, unexpected outcomes, and reasons to repeat or stop.

## What must not happen

- An LLM/chat interface becomes the organism by accident.
- A heartbeat or CI completion is treated as evidence of growth.
- A failed experiment gets rewritten silently into a new successful criterion.
- The browser renderer is allowed to mutate world truth.
- Data from prior experiments is overwritten by current state.
- Production/local host is used as an unbounded experiment scratchpad.
- Experiment code is deployed to the dedicated machine without an explicit inspection step.

## First decision to make with research evidence

Pick the smallest comparison across at least **two distinct substrate families**, with one falsifying outcome that could favor a simpler explanation. Do not choose a particular “genome” or “brain” before this comparison.
