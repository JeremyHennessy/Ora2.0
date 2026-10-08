# AL01-DISCOVERY v1 — Complete preregistered survey result

**Experimental status:** completed *synthetic chemistry* survey, 2026-10-08. **This does not create, demonstrate, train or identify a living digital organism.**

## Identity / precommitted design

- [Precommitted protocol](AL01-DISCOVERY-PROTOCOL.md) at commit `687c5aeb3398ee7bf2c0e23ab7bcf61f1062086b`; published before any holdout networks were executed.
- Implementation committed `5b8b0b89320e24b6a582f998daf483fdbca03940`; test suite `674bbaed06be9498874087c00c80508061d75ef6`.
- Executed source commit `dacab66383b2ddb7384fcec2b2a4f1b6fb6eee00`.
- [GitHub Actions run 37779761681](https://github.com/JeremyHennessy/Ora2.0/actions/runs/37779761681): `success`, both all-suite unit tests and frozen survey passed.
- Artifacts: `al01-discovery-complete` artifact ID `11551198751`, 90-day GitHub retention. It includes the full graph manifest, records, per-step traces and summary; zipped bytes were independently retrieved and checked.
- Source: `experiments/network_discovery.py`, stock Python standard library; no LLM, OpenAI API, pretrained agent, GPU dependency, server runtime or environmental control interface.

## Exact data preservation receipts

| File | SHA-256 | Records |
| --- | --- | ---: |
| `network-manifest.jsonl` | `6f098134a74470d0359c198fa48457fb686b15d10122abaea076953008b3ec3f` | 80 sampled graph definitions |
| `run-records.jsonl` | `1f094a100eb3b98f0ad0f07a40d0ac87e281fe13ae1d7b6d285c029dd9313bdc` | 1,440 treatment records |
| `run-traces.jsonl` | `870b5c7bfa7cec8d542f29aa95366fe81653a5b4bc844c0abda865bf8a306418` | 79,200 complete synthetic step events |

**Independent audit:** SHA-256 of every decompressed artifact matched the experiment summary; observed max absolute molecule ledger residual is **0**. The 80 networks include all acyclic networks and all ineligible worlds; no networks were selected on their outcomes. All 21 available unit/integration tests passed during the GitHub study run.

## Precommitted sample and results

- **80 network graphs**, seeds 7000–7079, 3 independent stochastic trajectories per graph = **240 trajectories**.
- **59/80** sampled graphs contain at least one directed catalytic cycle; 21 do not.
- **151/240** trajectories satisfy the *predefined* eligible target criterion, across **56 independent graphs**. Ineligible (89) are retained and cannot become "recovered" by denominator manipulation.
- All six treatments were run on every trajectory = **1,440 treatment runs**.

| Variant | Sustained target recovery among eligible | Rate |
| --- | ---: | ---: |
| Intact sampled graph | 142 / 151 | 94.0% |
| Preselected cycle edge removed | 47 / 151 | 31.1% |
| Preselected non-cycle edge removed (includes marked no-op when unavailable) | 146 / 151 | 96.7% |
| All arcs rewired at equal arc count | 72 / 151 | 47.7% |
| Basal-only chemistry | 0 / 151 | 0.0% |
| Resource denied | 0 / 151 | 0.0% |

Primary descriptive paired intact-minus-cycle-knockout effect: **95/151 = +0.62914**. Cluster-resampled **95% descriptive bootstrap interval `[0.52667, 0.72727]`**, grouping all three stochastic trajectories within each sampled network. Pairwise discordance: intact-only 95, knockout-only 0, same 56. This interval applies to this **chosen abstract chemistry sampling distribution**, not biological systems or all possible graph universes.

**Predeclared screening label:** 30/80 networks met the stricter within-graph 2-of-3 paired recovery screen. These are **exploratory screen hits, not confirmed organisms or independent validation**. No after-the-fact analysis was used to select networks to run.

## Explicit exploratory confound inspection — NOT preregistered subgroup confirmation

After seeing the complete data, we inspected the in-degree of the preselected target species. These strata were **not the predeclared primary comparison**. They identify a major alternative explanation and motivate a *new locked holdout protocol*.

| Target in-degree | Eligible paths | Intact recovery | Cycle-edge knockout recovery | Interpretation |
| --- | ---: | ---: | ---: | --- |
| Exactly 1 | 57 | 53 | **0** | **Trivial structural bottleneck:** the edge being deleted is target's only catalytic production route |
| At least 2 | 94 (35 graph seeds) | 89 | 47 | Larger-than-zero descriptive contrast, but graph bottlenecks and kinetics may still explain it |
| At least 3 | 47 (17 graph seeds) | 45 | 30 | Contrasts persist with more alternate incoming arcs; fewer graph replicates |

Also, 134 eligible trajectories across 49 graph seeds had a **non-cycle arc actually available** for the sham knockout (rather than a no-op). Among those, intact recovered 125, cycle-edge knockout 33, sham deletion 129. This is an exploratory sensitivity check, not controlled for matched catalytic flux or same in/out-degree.

**Caution:** the assay chooses its target from a known cyclic edge. Removing that edge is directly coupled to the measured target's production. This is a powerful **measurement-design bias**. Even positive effects with in-degree >1 do **not** show a self-made membrane, causal organizational autonomy, a distinct organism, spontaneous metabolism, or evolution. The no-resource and basal-only controls also reflect explicit designer-provided nutrient injection and substrate rules, and the rewiring changes the production graph without balancing observed flux.

## Verdict

- **Confirmed within toy model:** stochastic reaction networks sampled without selecting viable patterns can generate cyclic catalytic dynamics and measurable dependence of a prespecified target's post-damage recovery on particular network edges.
- **Not established:** organismal self-maintenance, new organizational identity, endogenous boundaries, heredity, reproduction, open-ended novelty or intelligence.
- **Potential null explanation:** removing the measured target's production pathway, graph degree and baseline target amount are sufficient to explain much or all of the measured effect.
- **Independent reproduction:** none. This was a new program and one preregistered sample of random graphs, not a replication of author claims.

## Next experiment, separate preregistration

Use a **fresh graph sample and a frozen multi-edge / alternate-producer analysis** to test whether resilience comes from replaceable distributed routes rather than one trivially necessary synthesis edge. Freeze the objective and matched controls **before** seeing the new results. Keep this result immutable and never revise the original protocol post hoc.

For exact replay, check out the executed commit and run:

```bash
python -m unittest discover -s tests -v
python -m experiments.network_discovery --networks 7000:7080 --replicates 3 --output-dir runs/al01-discovery --source-revision dacab66383b2ddb7384fcec2b2a4f1b6fb6eee00
```

**Preservation:** the source and full manifests remain reference points. GitHub Actions artifacts expire; copy this archive to controlled, backed-up experiment storage before its 90-day retention ends.
