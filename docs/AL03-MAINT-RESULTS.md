# AL03-MAINT — Population-cap and energy-maintenance sensitivity

**Observed result date:** 2026-10-08. **Status:** completed preregistered in-silico maintenance-cost study, with independent original-data reanalysis. **No new living organism or natural artificial chemistry demonstrated.**

## Verified provenance

- Approved prior AL03 main baseline: `3f0483db08ada43d06f032811e8f2fa52060ade2`.
- New [precommitted AL03-MAINT protocol](AL03-MAINT-PROTOCOL.md) was committed at `1857ec1977737afa643dbe2fdc40df3b59da2606` **before** executing study worlds.
- The new module `experiments/maintenance_stress.py` was committed `0c028ce2a11f54fd704240909b2c933768bb0bc1`. The retrospective read-only `experiments/retrospective_saturation.py` and negative tests were added separately.
- Exact first study execution Git SHA: `a4186da4e4fa52dcf65c299372ffc2ccdb5520df`, Python `3.11.17`.
- [GitHub Actions run #37791242970](https://github.com/JeremyHennessy/Ora2.0/actions/runs/37791242970) completed **success**. All **90/90 tests** passed *before* the old AL03 replay and new held-out survey.
- Full archived synthetic evidence: GitHub artifact **`al03-maintenance-complete`**, ID `11556507244`, 90-day retention. Archive was independently downloaded, unzipped, checked against reported hashes and inspected for all treatment denominations.
- **Zero changes** to `experiments/niche_selection.py`, previously frozen AL03/AL02/AL01/AL07 research protocols or their reported results. No self-hosted agent/machine was connected.

## Part 1 — New post-hoc analysis of the *original* AL03-NICHE records

AL03-NICHE world data was regenerated using the originally frozen source, protocol and seed panel `8000..8047`. The **three original exact SHA256 hashes were checked** before any new summary:
- Original `worlds.jsonl`: `315bf995bd78df8a9274190753ee1596c710326941f48c94fe57763f726b94dd`
- Original `events.jsonl`: `582dbd84864aa2a2746e505f120c0c7a406897c00e4be2b339b017bf5a44688b`
- Original `traces.jsonl`: `aab4f84f348e0e52f2d9abaa3d2854dd407ca3c12b827106d9c8e2cc38f00b69`

**Post-hoc saturation audit** used all 240 world summaries and original step histories; it is *not* a preregistered confirmatory test. Its `world-cap-audit.jsonl` has 240 rows, SHA256 `0383a57fea7752060035a28395ee00e3fba972b9f80b150959568d656874d8a4`.

| Original AL03 arm | Worlds ending at 40/40 population | Fraction of observed ticks at cap | Median first cap tick | Extinct by horizon |
| --- | ---: | ---: | ---: | ---: |
| Heritable | **48/48** | **75.929%** | 123.5 | 0/48 |
| No-heredity assignment | **48/48** | **74.627%** | 126 | 0/48 |
| No mutation | **48/48** | **72.708%** | 132 | 0/48 |
| Byproduct sink | **48/48** | **71.016%** | 132 | 0/48 |
| No external resource inflow | **0/48** | **0%** | n/a | **48/48** |

**Evidence-supported correction to interpretation:** a saturated static upper bound, periodic energy input and no per-global-tick maintenance expenditure can make an AL03 population appear stable without showing an endogenous mechanism for sustainability. These 192 externally-fed worlds did not show unlimited growth or self-created survival; they filled their imposed occupancy ceiling.

## Part 2 — Frozen new maintenance-cost experiment

**Fresh held-out worlds:** new seeds `8500..8547`, 48 per treatment, five intervention arms = **240 complete worlds**, same 480-tick horizon. Four arms retain the original external A supply; the fifth explicitly denies A replenishment. The only new energy rule is an externally priced debit to **all** living entities at a specified interval, including organisms not scheduled to act.

| New study arm | Final mean population | Alive at tick 480 | At capacity 40 at end | Fraction of full timeline capped | Upkeep energy spent | Deaths specifically due to upkeep |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Original physics (0 upkeep) | **40.0** | 48/48 | 48/48 | **75.447%** | 0 | 0 |
| 1 energy each 8th tick | **37.875** | 48/48 | 21/48 | **16.697%** | 87,234 | 1,349 |
| 1 energy each 4th tick | **24.8125** | 48/48 | 0/48 | 0% | 115,230 | 1,842 |
| 1 energy every tick | **5.8125** | 48/48 | 0/48 | 0% | 135,416 | 2,532 |
| Every 8th tick, **no new A** | **0.0** | 0/48 | 0/48 | 0% | 7,179 | 362 |

- In the original AL03 source, actor energy is debited when an entity gets a scheduled turn, not for maintaining idle occupancy. The new upkeep is a **designer-authored environmental cost** that changes the population dynamics without repairing entities or supplying abilities.
- **Primary binary persistence diagnostic:** Among the four fed arms, *all* 48 worlds retained at least one entity through step 480. Therefore the prespecified primary *survival/no-survival* outcome was **uninformative for distinguishing maintenance frequency among fed arms**, despite much lower populations. Its paired difference is **0** for those contrasts.
- **External supply denial:** all 48 upkeep-8/no-feed worlds went extinct. This is partly guaranteed by finite initial fuel and positive energy dissipation; it is not proof of independent homeostasis or general viability theory.
- **Secondary population endpoints:** show graded, strong sensitivity to upkeep interval; high maintenance supports fewer simultaneous entities under constant engineered food replenishment.
- **Demographic turnover:** total births: 1,872 baseline, 3,435 upkeep-8, 3,289 upkeep-4, 2,992 upkeep-1, 659 upkeep-8/no-feed. More birth opportunities mean more chances for hard-coded P→C role changes; any rise in consumer-lineage count **must not be labeled an evolved ecological innovation** without exposure-matched evaluation.
- **Resource validity:** all 240 worlds passed material-slot uniqueness and both numerical energy/mass ledgers; **maximum residual exactly zero** in all trace outputs.

## Independent output checks and scope

Archive `al03-maintance-complete` was independently inspected and contains two distinct output folders. Data SHA-256 and row counts:

| File | SHA-256 | Rows |
| --- | --- | ---: |
| `al03-maint/worlds.jsonl` | `2f0888b699a78c01452a638448ef70bf41fab013279ad4d2fe3b5854814b2b17` | 240 |
| `al03-maint/events.jsonl` | `7856d89c5e8c8495729d8cdbd0faed8accb6c6d9d0f34d5e5feb9b3ed7467e61` | 493,848 |
| `al03-maint/traces.jsonl` | `7804a782cda279dabfa3406e8f0d02248d64f80cec823b14dcea2b4aa012345b` | 98,303 |
| `al03-cap-audit/world-cap-audit.jsonl` | `0383a57fea7752060035a28395ee00e3fba972b9f80b150959568d656874d8a4` | 240 |

All three `al03-maint` hashes matched the emitted `summary.json`; old AL03 SHA records matched the independent historical audit. Tests include strict byte-identical baseline against original engine for development seed(s), trace-after-upkeep equality, forged material/energy rejection, replay and full-seed coverage.

**Typo warning:** The GitHub artifact's authoritative name is `al03-maintenance-complete` (not the shortened spelling in any narrative). The data manifest and source SHA are the integrity authorities.

## Scientific interpretation

**Observed:** the old AL03 ecology's full-cap persistence is extremely sensitive to *one additional, simple externally imposed cost*. A fixed 1 energy per entity every tick reduces mean ending population from 40 to roughly 6 under otherwise identical food laws, yet at least one virtual program still survives each fed trial to this horizon.

**Inference:** baseline population cap was a weak measure of sustainable organization. Resource-accounted entity replacement and internally produced maintenance remain unanswered. The model's event-log evidence does not establish true metabolism, self-produced boundaries, independently emergent hereditary skills or any form of conscious agency.

**Not a finding:** that 1/8/4 maintenance frequencies have natural biological meaning, or that indefinite ecological equilibrium is demonstrated by finite 480-tick simulations. Energy units and rules are symbolic, and future generative environments might behave differently.

## Next decision

**Stop broadening AL03 with arbitrary new taxes or optimizing a larger target population.** Design a *different* falsifiable test of **endogenous maintenance**: a candidate virtual organization must actively replace an internal prerequisite (e.g., a boundary or catalytic producer) using energy and materials it obtains through its own interactions, with an intervention that selectively disables its repair function. Compare intact, passive stability, developer-respawn, and resource-denied worlds under equal initial budgets. This mechanism should not be bolted into AL03-COPY or chemistry without evidence.

Alternatively, preregister a strict **birth-exposure and resource-flow matched** ecological niche comparison to distinguish inherited role behavior from extra mutation opportunities and artificial byproduct injection. Both directions require new physics/protocol, *not changes to finished studies*.

## Reproduction

Use Python 3.11.17 and fixed execution revision `a4186da4e4fa52dcf65c299372ffc2ccdb5520df`:

```bash
python -W error::ResourceWarning -m unittest discover -s tests -v
python -m experiments.niche_selection --seeds 8000:8048 --output-dir runs/al03-original --source-revision 5049d52b1bcccff6ee896b01d3f1105260080afd
python -m experiments.retrospective_saturation --input-dir runs/al03-original --output-dir runs/al03-cap-audit
python -m experiments.maintenance_stress --seeds 8500:8548 --output-dir runs/al03-maint --source-revision a4186da4e4fa52dcf65c299372ffc2ccdb5520df
```

Keep *raw* synthetic output in controlled backed-up storage; GitHub workflow artifacts have finite retention. This report preserves adverse findings and exact evidence, not a claim that a self-sustaining digital organism has been created.
