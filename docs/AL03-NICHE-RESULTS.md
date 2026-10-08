# AL03-NICHE — Preregistered ecological byproduct and role-transmission experiment

**Status:** completed synthetic in-silico resource experiment, 2026-10-08. No claim of spontaneous life, autonomous evolved ecology, intelligence or new instructions.

## Source / approval checkpoint

- [Frozen experimental protocol](AL03-NICHE-PROTOCOL.md) committed at `48e5ec662fe29e4decdc988dd2e1063a838a4487` before any held-out seed outcomes were viewed.
- New isolated experiment engine `experiments/niche_selection.py` at `7ff59e99745cbff33bfa57f099b2bc939423d5d9`. **AL01, AL02, AL07 working source was not modified.**
- Test file `tests/test_niche_selection.py` at `d86fef9d6d73c60b616bd63d9462739fbaf28faf`.
- Exact execution source `5049d52b1bcccff6ee896b01d3f1105260080afd`, [GitHub Actions #37788831042](https://github.com/JeremyHennessy/Ora2.0/actions/runs/37788831042): completed **success**, all **76/76** test cases passed before running full 48-seed survey.
- Synthetic artifact: `al03-niche-complete`, GitHub artifact ID `11554938751` (90-day retention). Complete archived observations retrieved and independently inspected; **all JSONL hashes matched** the emitted manifest.

## Verified experimental archive receipts

| File | SHA-256 | Rows |
| --- | --- | ---: |
| `worlds.jsonl` | `315bf995bd78df8a9274190753ee1596c710326941f48c94fe57763f726b94dd` | 240 |
| `events.jsonl` | `582dbd84864aa2a2746e505f120c0c7a406897c00e4be2b339b017bf5a44688b` | 145,334 |
| `traces.jsonl` | `aab4f84f348e0e52f2d9abaa3d2854dd407ca3c12b827106d9c8e2cc38f00b69` | 105,190 |
| `summary.json` | `adb4442be797ee98b5862091399006a1bf329b9aab57483fae508841bc575a3c` | Complete combined result |

All **240 distinct (seed, variant)** pairs were present. All independently checked file hashes agreed with the summary; **zero** world had a nonzero simulated mass or energy residual.

## Measured results — all 48 worlds retained in each arm

A fixed authored virtual "producer" P turns A (20 potential units) into usable energy12 plus B (8 potential). A fixed "consumer" C converts B into usable energy8 plus waste. P→C role mutation is pre-programmed at p=0.08; the world's initial founder is **deliberately seeded as P**. Reproduction is implemented by an engine-level energy threshold and a material-slot allocation, **not an instruction-copy mechanism**.

**Frozen primary outcome** required a P→C role transition in the ancestry, a C parent actually consuming B *before* reproducing, and a C daughter that also consumed B afterward.

| Condition | Worlds with qualifying consumer lineage | Births in all 48 worlds | B-feeding entities | Extinct by horizon 480 |
| --- | ---: | ---: | ---: | ---: |
| **Heritable role** | **42/48** | 1,872 | 336 | 0/48 |
| **Byproduct removed** | 0/48 | 2,035 | 0 | 0/48 |
| **Non-inherited role** | 12/48 | 1,872 | 160 | 0/48 |
| **Mutation disabled** | 0/48 | 1,872 | 0 | 0/48 |
| **No added A resources** | 25/48 | 661 | 157 | **48/48** |

- Heritable minus byproduct-sink: **+42/48 = 0.875** worlds; paired-world descriptive 95% percentile interval **[0.7708,0.9583]**; no control-only successes.
- Heritable minus nonheritable role: **+30/48 = 0.625** worlds; paired-world descriptive 95% interval **[0.4792,0.7708]**; no control-only successes.
- In the heritable arm: **8,540** B molecules produced through P conversion; **3,750** consumed by C. These are artificial reaction events, not independent chemical observations.
- In the byproduct sink: P conversion produces W with its B-potential8 dissipated to heat, so C cannot consume B. All controls preserve total potential and mass under the specified physics.
- Under no replenishing inflow, 25 temporary qualifying lineages appeared, but **every world went extinct** by the bounded horizon.

## Scientific interpretation and serious alternative explanations

**Supported, narrow claim:** Given a fixed, researcher-designed P→B resource conversion, a finite substrate, and mutation/inheritance of an authored role bit, the simulation produces multi-generational downstream nutrient use under several controlled finite time horizons. Removing B generation eliminates B-feeding by construction; disabling role change eliminates C-lineage creation by construction. Conservation tests show no free resource creation in this model.

**Caveats that prevent a stronger conclusion:**

1. **Trivial and nonmatched controls.** The sink removes the *only* B source; 0 B consumption is mechanically expected. The nonheritable control draws a C daughter with p=0.08 even when its parent is C, whereas the hereditary model keeps C with p=0.92. The 42-vs-12 outcome therefore has a very strong **built-in transmission advantage**, not a measured independent fitness benefit from naturally evolved heredity.
2. **Engine-assigned offspring.** This stand-alone ecological model copies a single role via an externally written division rule. It does NOT satisfy AL02's per-byte executed copying, so **cannot combine AL02 + AL03 success into a claim of one living entity with both capabilities**.
3. **External environment financing.** The 0/48 extinction result with periodic A supply is not indefinite survival. An environment administered by the researcher adds resources every third tick.
4. **Fixed affordances.** P and C resource rules, role-transition probabilities and viability thresholds were all authored before the experiment. No entirely new metabolic process, sensory mechanism, computational semantics, self-maintained boundary, or organism individuality evolved.
5. **Limited counterfactual controls.** The current experiment does *not* include flux-matched externally supplied B or lineages with equal role-transmission transition probabilities. These require a separately frozen new protocol; do not imply the comparison was done.
6. **One chosen ecology.** Results from 48 seeds and a 480-tick horizon do not generalize across different physical environments or implementations. Positive world counts are conditioned on this exact state space and exact model rules.

**Operational verdict:** empirical evidence of the **specified ecological feedback and role transmission inside a synthetic model**. It is **not** evidence of spontaneous ecological evolution, life, subjective experience, open-ended novelty, autonomous intention, or general intelligence.

## Recommended next discriminating study

Separate the **resource-production effect** from the **inheritance-by-construction effect**. Preregister a *matched-source* counterfactual where external A→B conversion supplies the same potential-weighted B flux as an observed producer pathway, while holding environmental material supply and computational opportunity accounting transparent. Independently compare role frequencies and mutational opportunity, or introduce a neutral ancestry-shuffle analysis not fed back into the simulator.

Only after those tests yield useful evidence should a separately licensed/reviewed design combine **AL02-style executed byte-copying** with ecological conversions or investigate environmental storage/repair. Any such study begins on a clean branch with its own protocol, not a rewrite of AL03 outcomes.

## Reproduce exactly

```bash
# Pin Python 3.11.17 and checkout execution SHA
python -W error::ResourceWarning -m unittest discover -s tests -v
python -m experiments.niche_selection --seeds 8000:8048 --output-dir runs/al03-niche --source-revision 5049d52b1bcccff6ee896b01d3f1105260080afd
```

The GitHub artifact is temporary; retain checksum-indexed backed-up copies if long-term preservation is required.
