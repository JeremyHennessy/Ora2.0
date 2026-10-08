# AL01-CAL — First observed outcome and limitations

**Date:** 2026-10-08 · **Status:** completed measurement-calibration run. This is *not* an artificial organism, nor a reproduction of any published artificial-life result.

## Frozen identities and receipts

- [Protocol](AL01-CAL-PROTOCOL.md) was published before the held-out run at commit `fd31bdc49c8c9af82cb0de64cedf8b752d97edf9`.
- Execution commit: `6b1f408d64e3664aea472b8e288e05c4f1a42595`.
- [GitHub Actions execution #37777974697](https://github.com/JeremyHennessy/Ora2.0/actions/runs/37777974697): completed **success**, 2026-10-08 12:35 UTC, attempt 1.
- GitHub artifact: **al01-cal-results**, artifact ID `11550606622` (ZIP, contains `summary.json`, `run-records.jsonl` and `run-traces.jsonl`; 90-day retention, not permanent storage).
- Python `3.11.16`; no installed modeling/training dependencies and no network calls from simulator.
- Source SHA256: `0822190ac34623e478aa659954ff8321e219986067cd34be6bbbb16196a58a53`
- Records SHA256: `7c5984e4ef330567eaec52f32442e9299d633c410e2b93d3e93f947464388299`
- Traces SHA256: `b4327a133007b125f9a6c2cf64d76234ca46d5d56e8c81001df3cd1c20474d4d`
- Artifact contents independently inspected after download: **128** world/variant records and **7,680** time-step trace events; both file hashes exactly matched the reported manifest. No filtered seeds.

## Measured result

| Condition | Sustained recovery | Rate |
| --- | ---: | ---: |
| Intact feedback cycle | 29 / 32 | 90.625% |
| B→A feedback disabled | 0 / 32 | 0% |
| Both catalytic reactions disabled (inert) | 0 / 32 | 0% |
| Nutrient feed denied and remaining S disabled | 0 / 32 | 0% |

- Primary difference (intact minus knockout): **+0.90625** of independently seeded worlds (29/32).
- Descriptive paired-world bootstrap 95% percentile interval: **[0.78125, 1.0]**, 5,000 resamples with fixed seed; it is **not** evidence for general organismhood or a causal conclusion in arbitrary chemistries.
- Discordant worlds: intact-only 29, knockout-only 0, both same 3.
- Pre-damage A or B zero: 0/32 worlds.
- Recovery latency among 29 successful intact worlds: **median 17 steps**, range 5–55.
- **Failures retained:** seed IDs `1013`, `1016`, `1020` did **not** meet the five-consecutive-step pre-registered recovery threshold in the intact condition.
- For every recorded step, **molecule ledger residual = 0**. No unrecorded mass creation was detected.
- All **10 unit/integration tests passed** in the execution workflow before the experiment ran.

## Interpretation

**Confirmed engineering result:** the deterministic simulator conserves molecule counts (including explicit nutrient inflow) and the prechosen recovery criterion discriminates the presence of an authored restorative reaction under this intervention and parameter regime.

**What the result does NOT show:** spontaneous origins, endogenous boundary production, chemical or thermodynamic metabolism, natural organism autonomy, heredity, evolution, environmental general intelligence, digital sentience or consciousness.

The B→A knockout removes the only reaction that can synthesize A: its inability to restore A is **partly guaranteed by design**. That is acceptable for a **positive control/calibration** and *not* acceptable as independent discovery of self-maintenance. The starved condition additionally converts remaining S to W (resource removal), rather than merely stopping inflow; the external intervention is explicit in the protocol.

The three intact failures show even a designed mutual-catalyst loop does not always satisfy a stringent five-consecutive-step recovery criterion under stochastic decay.

The system has no individual organism boundary or inheritance, so do not promote this result beyond **mechanistic apparatus calibration**. We should next investigate **non-handpicked candidate networks**, count *all* failed worlds, and compare them against independent lineage evidence from a different substrate.

## Experiment completed versus science remaining

- **G1:** sufficient evidence of deterministic replay, provenance, controlled interventions, a positive-control difference, and conservation, for this test harness.
- **G2:** *not established* — no hereditary descent or new capability.
- **G3:** *not established* — initial topology was expressly designed; there was no topology discovery or spontaneous organization.
- **Other metrics:** unmeasured.

## Next experiments (not yet executed)

1. [AL01-DISCOVERY](NEXT-EXPERIMENTS.md): preregister how to *sample* small reaction universes without cherry-picking and test their recovery/knockout distribution, including extinct wells.
2. Independent [AL02-LINEAGE](NEXT-EXPERIMENTS.md): build a bounded virtual instruction ecology in which copying is an executed action and heritable traits are audited against shuffled controls.
3. Compare both studies under separate endpoints, not a composite "aliveness" measure.

Rerun after checkout (same source commit and Python version):

```bash
python -m unittest discover -s tests -v
python -m experiments.chemical_calibration --seeds 1000:1032 --output-dir runs/al01-cal --source-revision 6b1f408d64e3664aea472b8e288e05c4f1a42595
```

The tracked source and workflow are sufficient to regenerate the deterministic artifacts. GitHub Actions artifact retention is not permanent; retain verified external copies before expiry.
