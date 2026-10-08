# AL01-RVCS — recorded fresh-network distributed-catalysis result

**2026-10-08. Status:** Completed preregistered **synthetic reaction-network** experiment. This does **not** show a living organism, endogenous boundary, inherited biological innovation, general intelligence or spontaneous life.

## Provenance and frozen protocol

- Scientific hypothesis: [N2: redundancy-versus-closure stress test](NEW-RESEARCH-HYPOTHESES.md), proposed after inspecting earlier AL01-DISCOVERY outcomes.
- [AL01-RVCS protocol](AL01-RVCS-PROTOCOL.md) was created at commit `2931ce9d59eb0aacadb81a3775399af2801e4f42`, **before** executing holdout graph seeds 9000–9143.
- Implementation: `experiments/redundancy_probe.py` at `215c8c0e5504b0be02352dd22beedf0c573f5aa1`; tests at `9274f4c71006fa4fef125093c660aaa62605ac83`.
- **Executed source commit:** `e756da8c8cac5d62ae2c4e24f3e548cd2a7719f0`.
- [Successful GitHub Actions run #37780922686](https://github.com/JeremyHennessy/Ora2.0/actions/runs/37780922686) with all **29 tests passing**, then complete 144-graph survey.
- Artifact `al01-rvcs-complete`, GitHub artifact ID `11552865219` (synthetic ZIP; expires after 90 days). Full JSONL graph universe and **all** treatment steps were retrieved, rehashed and independently checked against summary.

## Verified output hashes

| File | SHA256 | Rows |
| --- | --- | ---: |
| `network-manifest.jsonl` | `57b4ef55d4bb8a0f4cd9dc2bee633fd9980b55da5a86d796b99100596c4bf430` | 144 |
| `run-records.jsonl` | `34259da5f6ed40253ed93c045f5523701ddb306a13f7986b6839c539fa7b1ba7` | 3,024 |
| `run-traces.jsonl` | `03276d2440c4f9c7761fba13abe0dca2c02bd687e951fd82f404f456aa577b24` | 166,320 |

All hashes matched summary. All seven conditions for a trajectory shared an identical checkpoint and damage to its internal constituent populations. **Maximum absolute molecule-count residual: 0.** For every eligible graph/trajectory, after double-edge deletion at least **one other direct incoming catalytic route remained**.

## Unselected denominators and eligibility

- **144** fresh randomly sampled graph seeds 9000–9143; **432** stochastic paths, three per sampled graph.
- **50/144** graph topologies satisfy *a priori* constraints: target in-degree >= 3, at least two cyclic incoming edges and two off-target sham edges.
- **147/432** trajectories in those graphs also meet pre-damage abundance/damage criteria; **285/432** are ineligible and remain in archived data.
- The eligible trajectories belong to **50 independent graph universes**. Three paths sharing one graph are *not* independent graph samples.
- 3,024 seven-arm experimental treatment runs; 166,320 post-damage traces.

## Exact preregistered outcomes

| Treatment | Sustained target recovery / 147 eligible trajectories | Rate |
| --- | ---: | ---: |
| Intact original graph | 141 | 95.9% |
| First cyclic incoming arc disabled | 116 | 78.9% |
| Second cyclic incoming arc disabled | 112 | 76.2% |
| **Both cyclic incoming arcs disabled** | **34** | **23.1%** |
| Two non-target "sham" arcs disabled | 144 | 98.0% |
| Only background basal conversions active | 0 | 0% |
| Resource feed denied and available feedstock removed | 0 | 0% |

**Strict precommitted redundancy signature:** 63/147 eligible trajectories (**42.86%**), descriptive cluster-bootstrap 95% percentile interval **[0.3425, 0.5137]**. To count, both single cuts and sham pair needed to recover, the double cut and two no-catalysis/resource controls needed to fail, and intact needed to recover. The signature occurred in 50 candidate graphs as follows: 13 graphs with 0 of 3 pathways, 15 graphs with 1 of 3, 18 graphs with 2 of 3, and 4 graphs with 3 of 3.

**Screen-positive graphs:** 22/144 sampled networks achieved the strict signature in at least two independent stochastic trajectories of that same graph. This is an **exploratory within-run screen**, not an independently reproduced selection. No world was excluded from its full-sample denominator.

Secondary sham-minus-double-cut paired recovery contrast: **+110/147 = 0.7483**, network-cluster 95% percentile interval **[0.6554, 0.8356]**.

Among eligible paths, target in-degree was 3 in 120 trajectories and 4 in 27. **No eligible target had only one or two direct synthesis routes.** The third retained route after double cut does not guarantee it had available catalyst or sufficient reaction flux.

## What the observations can and cannot mean

**Evidence-supported, bounded conclusion:** Some completely unscreened graph draws exhibit **redundancy-like causal maintenance of one prespecified constituent** in this finite, abstract stochastic catalytic model: either of two cyclic synthesis links alone is sufficient in some trajectories, but removing both impairs reconstitution, while the two-edge off-target sham often has little effect.

**Important remaining alternatives:**
- Preselecting the target for its incoming cycle arcs aligns intervention and metric. This can produce mechanically predictable effects even in nonliving reaction systems.
- The off-target sham edges have the same **count**, not the same observed kinetic flux or causal influence. They may simply be less active than cut edges.
- We used the **same authored chemical rules** as the earlier experiment. New network seeds are a **new sample of the same model**, not an independent experimental replication of a natural phenomenon.
- Basal production, nutrient replenishment, decay physics, reaction templates, and the source of stochasticity are investigator-chosen. They do not amount to physical biochemistry or evolutionary origin-of-life.
- None of this demonstrates spontaneous creation of chemistry or self-produced protective individuality; no genotype, offspring, hereditary variation or selection was present.

**Explicitly false claims to avoid:** "Ora became alive", "Open-ended digital evolution was achieved", "the first artificial life was created", "emergent general intelligence", "self-aware", "completely objective-free" or "network redundancy is biological autopoiesis".

## Main decision: close this chemistry survey branch before new mechanism design

This is useful positive evidence about **mechanisms in a toy system**, not reason to scale the same setup indefinitely. Rather than tuning our rules to obtain more positives or bolting neural networks onto it, the next scientific program should test an **orthogonal requirement for organismhood: heritable reproduction with independently checked new functionality** (AL02-LINEAGE).

An alternative future experiment on this chemistry system may compute a *causal organization fingerprint* across multiple flux-matched interventions, rather than counting the number of target synthesis edges removed. That is currently an **original untested hypothesis**, and further chemistry claims depend on a new protocol.

## Exact replay

```bash
python -m unittest discover -s tests -v
python -m experiments.redundancy_probe --networks 9000:9144 --replicates 3 --output-dir runs/al01-rvcs --source-revision e756da8c8cac5d62ae2c4e24f3e548cd2a7719f0
```

Check out the executed source commit first and match Python version for exact replay. Synthetic archives must be backed up separately before GitHub artifact expiry. Do not rewrite precommitted thresholds based on this result.
