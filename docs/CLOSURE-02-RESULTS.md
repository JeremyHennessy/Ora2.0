# CLOSURE-02-FUNCTION — Cost-controlled shell physics, complete result

**2026-10-08 · Completed.** New independently sampled, finite **engineered** spatial chemistry trial. It tests the effect of **programmer-authored** transport-reducing material M, **not** artificial life, spontaneous compartments, internalized physics, heritable organismhood, or sentience.

## Frozen protocol and exact execution identity

- [CLOSURE-02 preregistration](CLOSURE-02-PROTOCOL.md) committed at `6f2e1552613c0e60687622057d99db0f4290d104` **before** evaluation seeds 6400–6463 were run.
- Standalone `experiments/closure02_functional.py` originally implemented at `32a4232f1b0ce4e26ccb3c9bd4437b70965569b4`, with tests `a3794d42ce7c8ad5e9860629d7923c636f44d249`. None of the AL01/AL02/AL03/AL07/CLOSURE-01 source modules, earlier protocols or archived outcomes were changed.
- Actual first held-out GitHub execution revision: `675b786a90af7d8e23f51f6eedf30a7fe03ddb81`; [successful workflow run #37807254735](https://github.com/JeremyHennessy/Ora2.0/actions/runs/37807254735).
- **136/136 tests passed**, Python **3.11.17**. The newly added tests establish identical transition results and PRNG state to the old CLOSURE-01 source for `shell_effect=intact`, `shell_inert=permeability_null` and `no_shell=no_M_synthesis` on development seeds.
- Full GitHub Actions artifact: **closure02-functional-all-worlds**, ID `11563910239`, finite 90-day GitHub retention. Downloaded and independently inspected at this checkpoint.

## Raw archive integrity, not just summary claims

| File | Actual SHA-256 independently computed | Rows | Matches manifest? |
| --- | --- | ---: | --- |
| `worlds.jsonl` | `e75376cd6e711a6ae3a20d8dd277ae203486982b91046f56e92117122c45ec33` | **960** | Yes |
| `traces.jsonl` | `fcbb04f897fe6f0ac5de2db6494f56a691340b8b008d61064a9dceb374960fd4` | **57,600** | Yes |

All **960** unique (seed, origin, treatment) keys were found; held-out seed IDs **6400–6463**; 64 seed families × 3 initial origins × 5 interventions. **Zero** nonzero molecule-mass residuals among all 57,600 traces. Complete eligible and ineligible worlds remain in the archive. Branch tests pass independently of study data; this is *one* in-silico implementation/physics family, not independent scientific replication.

## Prespecified denominator

The target was fixed **before** intervention and selected by local A+R concentration. Eligibility was also determined before intervention: A≥4, R≥4 within 3×3, ring cells with existing M≥2. **157 of 192** original seed+origin worlds qualified; **35 did not**, retained without being relabeled as failed recovery. All 5 arms operated on the same post-damage A/R/M conditions per original world.

No “live organism” was inserted at any time, although the `clustered` origin **begins with author-placed catalysts**, and `nutrient_only` contains author-provided basal A activation.

## Result: core A and R recovery independently of shell appearance

The **primary recovery criterion requires only A and R**, each at ≥70% of its own predamage core count for three consecutive steps. It **does not** require ring M or any shell-production event.

| Arm | Core A+R recovery / 157 eligible origins | Accepted outward / attempted outward A/R diffusion | Outward hop fraction |
| --- | ---: | ---: | ---: |
| **Shell effect** — M produced and changes permeability | **70** | 2,433 / 16,431 | **14.81%** |
| **Shell inert** — M produced at the same cost, no permeability effect | **50** | 3,787 / 15,656 | **24.19%** |
| **Ghost effect** — spent-S synthesis produces W; residual old M still active | **71** | 3,424 / 16,006 | **21.39%** |
| **Ghost inert** — spent-S synthesis produces W; residual old M inert | **52** | 3,928 / 15,919 | **24.67%** |
| **No shell** — suppress both costly shell routes, while any preexisting M still decays | **148** | 6,437 / 29,761 | **21.63%** |

**Important interpretation:** `shell_effect` has lower observed outward acceptance by construction: **the authored M concentration explicitly reduces hop probability**. The observed difference in *successful internal recovery* between shell effect and shell inert (70 vs 50) gives a modest conditional benefit under this authored rule but **not** a positive net benefit of synthesizing M. The *ghost effect* retains existing M after the initial damage but **no new M** is made and nevertheless shows 71 recoveries vs 70 with additional shell synthesis, while the cost of chosen M/ghost reaction events is matched.

### Paired descriptive contrasts

These are **predeclared comparisons** of the independently specified *core-only* endpoint. Uncertainty is descriptive, **4,000 bootstrap resamples of the 64 source-seed clusters**, so 157 eligible origin modes and 57,600 correlated step events are **not** independent scientific universes.

| Shell-effect minus comparator | Difference in recovery fraction | Descriptive 95% bootstrap interval |
| --- | ---: | --- |
| Versus **shell inert** | **+0.1274** | [ +0.0190, +0.2436 ] |
| Versus **ghost effect** | **−0.0064** | [ −0.1037, +0.0881 ] |
| Versus **ghost inert** | **+0.1146** | [ +0.0185, +0.2078 ] |
| Versus **no shell** | **−0.4968** | [ −0.5762, −0.4167 ] |

None of the above intervals generalizes beyond the author-specified reaction/diffusion parameters. They do not establish new metabolism, adaptive intelligence, life or autopoiesis.

## Strong alternative mechanisms and remaining shortcomings

1. **Suppressing the production pathway strongly benefits recovery.** Shell channels consume precursor S and finite reaction encounters that otherwise might regenerate A/R. Suppressing shell synthesis improved recovery from 70/157 to **148/157**. Resource competition is a plausible mechanism, but this intervention also changes reaction-selection probabilities and subsequent trajectories; it does not isolate cost alone. This *disfavors* the current pathway, not all possible boundary chemistries.
2. **Residual M confound:** `ghost_effect` does not create new M after damage, but remaining M from warmup **still reduces diffusion**. Thus its 71/157 does not prove M never matters; it suggests continued synthesis is not needed for the measured short-horizon result.
3. **Only per-event cost matching:** each selected ghost reaction spends one S, one encounter and deposits W instead of M; the evolving trajectories have **different numbers** of selected conversions (35,837 M events in shell-effect vs 36,297 ghost events among eligible worlds). Therefore **total resource flux, opportunity cost and exposure are not globally matched**. This could account for some recovery differences.
4. **No true energy equation:** an equal-count particle conservation ledger does not constitute a thermodynamic potential/free-energy balance. Shell diffusion reduction is a convenience authored by the scientist.
5. **Outward and inward permeability:** active M slows both exits and entries. Outward crossing fraction alone is not the same as selective homeostatic protection or causal individuality. Source seed groups are the statistical units; per-particle proposals are repeated correlated attempts.
6. **Sampling constraints:** 64 fresh seeds within one 9×9 model, a finite 60-step endpoint and predamage target chosen by maximum A+R concentration. Do not infer indefinite survival or novelty from these numbers.

## Current scientific verdict

**CLOSURE-02 does not support a net maintenance advantage for continued synthesis of this particular M material under the declared regime.** The observed short-horizon diffusion suppression is mechanistically expected, and the no-shell treatment is substantially more effective at restoring core A and R. The proposed shell *production pathway* should be **retired as the leading self-maintained-boundary candidate** and preserved as a **negative control**, not made more attractive by retroactive rate tuning.

**This does not refute the wider possibility of endogenous organization.** The next independent design should test a substrate where *functional organizational prerequisites regenerate one another under material/energy costs*, with passive persistent-process, external-rescue and internal-repair-knockout comparators. Crucially, it must not predeclare that a shell/ring is the organism.

## Exact replay

```bash
# Checkout the executed Git commit above and use Python 3.11.17.
python -W error::ResourceWarning -m unittest discover -s tests -v
python -W error::ResourceWarning -m experiments.closure02_functional --seeds 6400:6464 --output-dir runs/closure02-functional --source-revision 675b786a90af7d8e23f51f6eedf30a7fe03ddb81
```

**Operational boundary:** This is GitHub-hosted bounded science; it has not been executed on the Windows desktop. The separate RUNTIME-01 local Codex report shows AL01 fixture *process-exit recovery*, **not** CLOSURE-02 restart resilience, crash recovery under all reactions or a persistent virtual organism.

## Custodian verification and closure receipt (2026-10-08)

The primary Work/Codex custodian read the **original ZIP in memory**, independently recalculated its ZIP and two raw-file hashes, verified both source-module checksums against the original execution revision, checked all 960 world-specific trace hashes and 57,600 raw-count/ledger observations, and recomputed recovery directly from A/R counts. No downloaded simulator was executed on the desktop and no D: evidence was accessed.

- Original ZIP SHA256: `c1aabbe1429a41533dbc66c6622a21144b95da101524e0b80e7a91d3d038e755`.
- Independent recovery recount: shell_effect 70, shell_inert 50, ghost_effect 71, ghost_inert 52, no_shell 148; denominator 157.
- Hardened auditor no longer trusts `core_ok`: it derives eligibility, threshold flags and recovery time from counts; checks raw conservation, event debits, forbidden products, flux totals, final-grid core counts and exact source identity.
- **145 tests passed** at `7564736f8878f5640039f84d9adfa6eff2a01d89`, including coherent-rehash adversarial fixtures.
- [Manually dispatched replay/audit #37808679089](https://github.com/JeremyHennessy/Ora2.0/actions/runs/37808679089) passed at that revision, Python 3.11.17. Original worlds/traces hashes matched exactly; every raw recovery count and flow total passed the strengthened audit.
- Verified replay artifact ID **11564510728**, ZIP digest `c17227eed46efb8a57322e4204cd3ff1975449f7498d817040a2bd3fae801eb6`; contains raw records and audit receipts. GitHub retention expires **2027-01-06**; independent archival preservation remains necessary.
- Intermediate workflow **#37808289640** failed because the newly required audit revision argument had not yet been added to its invocation. This integration failure is retained; it is not a new scientific failure or a reason to replace seeds. The invocation was fixed and the reviewed manual run above passed.

The full-study workflow is now **manual-only**. Its repeated held-out executions are deterministic software replay of the same study, not fresh statistical replication. No new study protocol, treatment definition, chemistry rate or historical raw data was changed.

**Decision:** close this study as a qualified negative for the shell-production candidate. The shell-vs-ghost interval spanning zero is not evidence of equivalence. Continue with a discriminating repair-of-repair measurement gate; no automatic shell tuning or positive life claim.
