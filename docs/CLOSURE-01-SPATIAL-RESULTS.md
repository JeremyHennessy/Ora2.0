# CLOSURE-01-SPATIAL — An authored shell does not establish functional autonomy

**Completed experiment:** 2026-10-08. **Study status:** verified synthetic, finite, mass-conserving spatial chemistry. **Scientific verdict:** internal catalyst recovery depends on declared A↔R reactions and available nutrient; **no net functional protective-shell effect was demonstrated under these conditions**. The world has NO genome, reproduction, thermodynamic energy ledger, self-chosen goals or living organismhood.

## Frozen identity and audit receipts

- The 99-line [precommitted protocol](CLOSURE-01-SPATIAL-PROTOCOL.md) was committed at `d8f1f79927a0943778c527ee6fc1e56848cf94f4`, **before held-out runs**.
- Simulator `experiments/closure_spatial.py` added at `80cbf6e0869948ac6fa06372e947555c1c6da1c8`, tests at `dd4a1e80514022760e155f53257c4b543034ac21`.
- Exact first held-out execution source: `9fd542528c6524240cd935fcd0e6a07c1e4c533d`, Python **3.11.17**, [GitHub Actions #37795271005](https://github.com/JeremyHennessy/Ora2.0/actions/runs/37795271005) completed **success**.
- **104/104** regression tests completed before the first study; **110/110** passed after the separate read-only diagnostic was added. No previous AL01/AL02/AL03/AL07 software was edited, and no host-code execution was available to virtual chemical processes.
- Retained archive `closure01-spatial-all-worlds` (GitHub artifact ID `11557349648`, time-limited 90-day storage), downloaded and independently inspected with an external SHA256 calculation.
- Original `worlds.jsonl`: **648 records**, SHA256 `6a8a81296bffd650ae927a66b7ae21d1ce93690e78ccf4c3190f8aaddd9c6253`.
- Original `traces.jsonl`: **38,880 post-intervention time-step records**, SHA256 `79eceef3f3e9e4d492d4b5b955103a50a26ba09569eae9f6322db641f425c28e`.
- **Both independent file checksums exactly matched the archived summary's manifest**, all 648 (seed, origin, treatment) combinations were unique/complete, and **0/38,880 traces showed a nonzero molecule-count residual**.

## Independent reproducibility and post-hoc audit

After the first held-out study was completed, a **separate read-only analyzer** `experiments/closure_spatial_diagnostics.py` and six adversarial tests were added, without changing the original simulator parameters or its original `worlds.jsonl` and `traces.jsonl` bytes.

- [Second GitHub Actions execution #37796741385](https://github.com/JeremyHennessy/Ora2.0/actions/runs/37796741385), execution commit `669d42f00eb63e4afc8da27c4101a53dc395e652`, **success**; **110/110 tests passed**.
- Entire original 36-seed / 3-origin / 6-arm panel was regenerated, and both raw file hashes matched the **original first run exactly**.
- The independent analyzer checked **648 world-specific trace SHA256 chains**, all **38,880** contiguous per-treatment steps, all paired branches and all particle ledger residuals.
- The combined GitHub artifact `closure01-spatial-all-worlds`, ID `11559470583`, includes the original results and a new `closure01-analysis/diagnostic-summary.json`. The ZIP was downloaded and independently checked: hashes and all counts agree.
- The **exploratory** pooled 36-seed-cluster bootstrap values below are now reproducible by running this separate analyzer on the archived JSONL files; they are **not** to be mistaken for prespecified confirmatory estimates.
- Deterministic rerun is a software-replay result, **not** an independent scientific reproduction in a different physical, chemical or software substrate.

## What was actually tested

36 frozen seeds `6100..6135` independently initialized each of three populations: `clustered` (12 A and 12 R seeded in same location), `dispersed` (same 24 catalysts randomly placed), and `nutrient_only` (no catalysts initially but **a designed basal S→A activation reaction**). Each got 60 warmup steps, then a preselected densest 3×3 region was damaged, and the same state and PRNG were branched into **six** matched 60-step treatments.

The treatment arms were: intact, disabling R→A, disabling A→R, suppressing M synthesis, suppressing M's diffusion effect, and complete nutrient denial. All paths included decay of catalytically active material and M, with S inflow declared per model.

**Caution:** Nutrient-only does NOT mean chemistry appeared from physically inert matter: the chosen simulator explicitly permits S→A basal activation and A→R catalysis. A zero-initial-reagent world is not evidence of spontaneous chemical or cellular life.

## Complete precommitted results by initial condition

All 36 starting worlds per origin are retained. Eligibility was assessed *before damage* using A/R core counts and existing M on a neighboring ring, and **ineligible worlds were not classified as experimental successes**.

| Origin | Eligible / total | Intact *dual* recovery | Permeability-null *dual* recovery | Intact *core A/R* recovery | No M synthesis *core* recovery | No R→A *core* recovery | No A→R *core* recovery |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Clustered | 31/36 | **11** | 10 | **13** | **26** | 4 | 2 |
| Dispersed | 30/36 | **10** | 8 | **13** | **26** | 4 | 2 |
| Nutrient-only | 32/36 | **6** | 9 | **11** | **27** | 4 | 2 |
| **Total** | **93/108 eligible** | **27/93** | **27/93** | **37/93** | **79/93** | **12/93** | **6/93** |

**The primary endpoint (“dual recovery”) intentionally requires both internal A/R and new shell material within the 3×3 neighborhood**. Therefore `no_M_synthesis` records **zero** dual successes **by design** (it cannot synthesize M); that comparison **must not be used as noncircular evidence** that membrane synthesis improves survival or functional boundary maintenance.

The intact and permeability-null arms recovered together in **27/93** eligible worlds, with **18** intact-only and **18** permeability-null-only discordant worlds. The zero aggregate difference, under paired intervention analysis, is negative evidence for an *advantage detectable by this dual endpoint*, not proof that the shell effect is universally absent. All 93 eligible worlds under **both** intact and permeability-null met the separate M-shell recovery screen, so shell pattern production itself was not a discriminatory fitness assay.

The independent core A/R endpoint—**defined without requiring M**—is more important for this issue: disabling M synthesis improved successful core recovery from **37/93** to **79/93** while retaining the same pre-damage checkpoints.

## Additional diagnostic analysis, explicitly post-hoc

After the complete archive was preserved and inspected, the research team pooled eligible worlds across the three origins for new diagnostic comparisons. This pooled bootstrap is **exploratory**, not a primary preregistered confirmatory result. The descriptive 95% intervals below resample the **36 initial random-seed clusters**, not the 93 records or 38,880 correlated frames as independent universes.

| Endpoint (eligible worlds) | Intact positives | Comparator positives | Paired intact − comparator | Clustered 95% descriptive bootstrap |
| --- | ---: | ---: | ---: | --- |
| Core recovery, suppress M synthesis | 37 | **79** | **−0.4516** | **[−0.5761, −0.3298]** |
| Core recovery, M has no transport effect | 37 | 33 | **+0.0430** | **[−0.0833, +0.1649]** |
| Core recovery, suppress R→A | 37 | 12 | **+0.2688** | **[+0.1429, +0.3918]** |
| Core recovery, suppress A→R | 37 | 6 | **+0.3333** | **[+0.2283, +0.4382]** |
| Dual recovery, M has no transport effect | 27 | 27 | **0.0000** | **[−0.1222, +0.1236]** |

**Interpretive priority:** The membrane-production pathways consume S and compete with catalyst regeneration for finite reaction encounters, so suppressing them changes resource allocation **and** eliminates shell material. The core-recovery improvement therefore **cannot be attributed to “cost” alone** without an explicitly cost-matched replacement control. Conversely, removing M's *transport effect alone* with M still produced shows no clear beneficial effect under the current assay.

**Secondary resource-denial result:** no qualifying world met the dual-recovery endpoint after all usable S was converted to waste and feed stopped. This is partly mechanically expected from fixed reaction rules; don't present it as proof of biological energy regulation.

## Verdict — what we actually learned

**Supported within this synthetic lattice:** A and R can actively regenerate under an investigator-chosen catalytic reaction network. Some initially nutrient-only lattices form A/R/M regions when a researcher-coded basal activation mechanism is available. Ring material M can re-form after damage under the four hardcoded reactions.

**Not supported:** that M forms a viable **protective boundary** causally improving core maintenance under matched cost, that a spatial region becomes its own autonomous organism, that repair processes are themselves created under a new biological organization, that chemical reproduction or heritable function has emerged, or that the experiment demonstrates abiogenesis, consciousness or general intelligence.

**Null explanation:** a well-mixed autocatalytic network plus spatial accumulation may generate attractive shell-like geometry, but external feed, fixed reaction probabilities and competing resource sinks explain the observed changes without any true individuality. We must avoid building a new model around an appearance-based interpretation of M as a “membrane.”

## Scientific next step, NOT yet measured

See [CLOSURE-02 design](CLOSURE-02-RESEARCH-DESIGN.md). Two strong directions:
1. **Cost-matched functional null:** Keep identical energy/substrate debit for M production but divert the product to inert W, separately toggling M's transport effect. Compare core A/R viability and leakage without including M in the scoring rule; preselect independent new seeds before any new simulation.
2. **New organizational substrate:** Form a protected local organization only when internally constructed transport boundaries and **repair-of-repair** pathways co-sustain one another; use independent region segmentation and negative attractor/external-protection controls. Do not merely increase M synthesis probability until “good-looking” shells pass.

The value of CLOSURE-01 is a **bounded falsification of a tempting toy design**. Do not quietly change its original rates, source version, eligibility, or archived results to make it appear more life-like.

## Exact replay

```bash
# Python 3.11.17, checkout execution SHA 9fd542528c6524240cd935fcd0e6a07c1e4c533d
python -W error::ResourceWarning -m unittest discover -s tests -v
python -W error::ResourceWarning -m experiments.closure_spatial --seeds 6100:6136 --output-dir runs/closure01-spatial --source-revision 9fd542528c6524240cd935fcd0e6a07c1e4c533d
```

The run uses bounded GitHub Actions compute, not an attached dedicated computer or continuously running entity. Back up the artifact before GitHub retention expiry.
