# CLOSURE-01-SPATIAL v1 — Frozen local organization, repair and shell-function assay

**Registered 2026-10-08 before held-out study outcomes.** We are studying a wholly authored artificial chemistry, **not** demonstrating a living organism, autonomous boundary genesis, abiogenesis, inherited reproduction, or consciousness. A spatial shell here is a *functional toy permeability parameter*, not a lipid membrane.

## Scientific foundation, boundary from former Ora

Use **only new artificial-life reasoning and reviewed science**; no architecture, code, experiment or failure narrative from the former Ora/AgentTest project has been used.

Scientific antecedents:
- Stepney (2025), doi:[10.1098/rstb.2024.0298](https://doi.org/10.1098/rstb.2024.0298), explicitly distinguishes autopoiesis, agency and open-ended adaptation as proposed requirements, not demonstrated by any toy protocell.
- Taneja & Higgs (2025), doi:[10.3390/life15050724](https://doi.org/10.3390/life15050724), study **an explicitly lipid-bounded** autocatalytic protocell model: its observed vesicle dynamics are *not* de novo boundary origin.
- A 2025 physical protocell reaction study, doi:[10.1103/PhysRevE.111.014424](https://doi.org/10.1103/PhysRevE.111.014424), analyzes how autocatalysis may persist **inside a specified vesicle**.
- [AI-Research](https://github.com/JeremyHennessy/AI-Research), verified baseline commit `37ec45027e2bfd62030fb9c6c1840294c35f366a`, CI `37791881061` green, warns against observer-defined individuality, passive attractors, resource-injection confounds and externally authored survival bonuses. It remains a **research-only** reference repo and will not be modified by Ora2.0.

No author's simulator/source is copied here, and no exact replication is claimed. This is a new, explicit and falsifiable toy-world experiment.

## Research question

Can **local elemental reactions** reconstitute an internally active, localized region and its surrounding *transport-reducing material* after controlled damage? Do both feedback reactions, shell synthesis and shell permeability causally contribute beyond passive retention, when tested on **clustered positive-control**, **randomly dispersed**, and **nutrient-only with basal activation** initial conditions?

### The core limitation

The researcher fixes all chemical species, their reactions, and a rule making M reduce diffusion. In particular, generating an M-rich ring is **not** independent proof of autopoiesis; a positive would demonstrate **mechanistic coupling under this declared physics only**.

## Physics — exactly specified before seeing outcomes

- **9×9 periodic square lattice**, integer particles S (substrate), A (factory catalyst), R (restorative catalyst), M (immobile transport-reducing material), W (inert waste). No protected organism identity, walls or special selected “living” sites.
- Initially four S per lattice site (324 total material units). **Seeded cluster**: remove 24 S from the deterministic lowest-index S sites, add 12 A and 12 R at the center site (4,4); no M is inserted. **Dispersed**: 12 A and 12 R are placed by independent seed draws at sites with available S, consuming one S per deposited catalyst; no M is inserted. **Nutrient-only**: unchanged 324 S and no catalyst. All three have exactly 324 initial abstract material units. The resulting worlds have different initial chemical free-energy content; do not imply thermodynamic equivalence.
- Each simulated step begins with **8 S additions**, placed in uniformly sampled cells using the world PRNG, except `resource_denied` branch. Record cumulative supply.
- Each of 81 sites in increasing index order gets one stochastic **basal activation attempt**: with S>0 and Bernoulli p=**0.006**, convert 1 S→1 A.
- Then each site has exactly **two reaction encounters**, in cell order. If S>0, choose between no-reaction weight 1 and four weighted pathways with each weight `0.35 * local_catalyst_count`:
  1. A + S → A + R (restore R)
  2. R + S → R + A (restore A)
  3. A + S → A + M at a uniformly selected **cardinal neighbor**
  4. R + S → R + M at a uniformly selected cardinal neighbor.
  One S is consumed and exactly one product molecule is added (potentially to neighbor); both catalysts remain. Disabled reactions receive zero weight. All four are investigator-defined; no energy barrier thermodynamics is modeled.
- After reaction, each A and R molecule independently decays into W with probability **0.09** and each M independently decays into W with probability **0.08**.
- Finally, molecules of S, A and R undergo simultaneous bounded diffusion (each original particle moves at most once/tick, cardinal-neighbor selected uniformly if a movement occurs). S hop probability **0.50**. A and R hop probability is **`0.24 / (1 + 0.80*(M_source + M_dest))`**. Under `permeability_null`, catalysts hop with fixed p=**0.24**, regardless of M. M and W do not diffuse. Transport is **locally authored physics** and deliberately tests whether M matters functionally rather than cosmetically.
- Periodic boundaries and particle moves conserve molecules exactly, checked at each simulated step: `Σ(S+A+R+M+W)=324+total_supplied_S`. **This is abstract mass accounting, not a Gibbs-energy or metabolic work ledger.**

## Damage and independent target selection

- Warmup **60 steps**, with all pathways and supplied S. Each replicate's site of interest is chosen once from the *pre-damage* state: pick the center of the 3×3 region with **maximum A+R**, row-major tie break. The target is selected before forking and **never reselected** to follow the largest post-hoc survivor.
- Define the 3×3 center-plus-eight-neighbors region as "core"; the eight neighboring cells form the "ring." Pre-damage core A, core R and number of ring cells with M≥1 are recorded.
- Eligibility (determined **before** branch outcomes): core A≥**4**, core R≥**4**, and ring M coverage≥**2**. Ineligible worlds/arms are still run and logged; never excluded from the full sampled denominator.
- Damage identically in every treatment: move floor(**0.55** × molecule count) of A and R to W *at every site in the core*, and floor(**0.65** × M) in each ring cell to W. PRNG state and full damaged lattice are cloned identically into all six treatments.
- Observe **60** additional steps per treatment, using the same PRNG state at fork. Dynamics naturally diverge when a pathway is disabled.

## Six matched branches

1. `intact`: all four reactions and full M-dependent permeability, continuing substrate.
2. `no_R_to_A`: selectively disable pathway R + S → R + A (factory rebuilding route absent).
3. `no_A_to_R`: selectively disable pathway A + S → A + R (restorative rebuilding route absent).
4. `no_M_synthesis`: selectively disable both M-producing reactions. Existing shell may passively persist and decay; no engine resets it.
5. `permeability_null`: all reactions active, but M **does not reduce A/R diffusion**; shell material can still form, so any core-localization benefit needs independent testing.
6. `resource_denied`: no new S after intervention, and all currently available S is converted to W at the fork; all other reactions nominally active. This is a *strong* resource-denial intervention, not just stopping inflow.

No extra survival reward, health score, life toggle, hidden actor list, periodic repair, resource-generating exception or outside AI model. The system may produce no well-defined individual at all.

## Frozen seed panel, costs and endpoints

**Development-only smoke seeds:** 0–7. Use only for code/invariant/replay testing, never for picking “promising” outcome parameters.

**First held-out panel:** **36 seeds** `6100..6135`, each used in **all 3 initial conditions** `clustered`, `dispersed`, `nutrient_only`. Each origin+seed is branched into 6 treatments, giving **108 independent pre-damage worlds** and **648 matched intervention runs**. These 108 worlds are clustered into **36 shared PRNG seeds** for descriptive confidence intervals, and **should not** be described as 108 independent chemistry laws.

**Primary endpoint (candidate dual organizational recovery):** for an **eligible** pre-damage world, at least **three consecutive** post-damage steps where both core A and core R are **≥0.70** × their respective pre-damage counts **and** at least **2 of the ring's 8 sites contain M**, while **≥2 new M-synthesis events** have occurred within the core+ring neighborhood since intervention. The threshold is explicitly authored and couples naturally to the definition of repair; shell-deficient branches may fail **by construction**, making this a **mechanistic screening metric rather than proof of autonomy**.

Report dual recovery incidence **among eligible** and **across the full 36 worlds per origin** (with ineligible coded not-assessable, *not* false success). Contrast intact vs `no_R_to_A`, `no_A_to_R`, `no_M_synthesis`, `permeability_null`, and `resource_denied`; include paired world discordance and 95% *descriptive* clustered-bootstrap percentiles with 4,000 resamples seed **20261008**. Zero eligible worlds ⇒ **INCONCLUSIVE**, do not tune eligibility retroactively.

**Independent secondary outcomes, not combined into one life score:**
- Core A/R recovery **without** M as a requirement; compare `intact` vs `no_M_synthesis` and `permeability_null`. This can reveal if the shell is irrelevant.
- M-ring coverage and total M turnovers after damage; shell production from inner catalysts versus external environment **is built in by reaction law**.
- Local retention ratio `(A+R inside fixed preselected core)/(A+R globally)` and its difference vs permeability-null, interpreted cautiously under variable global catalysts.
- Trajectory of A/R/M, W and S, total substrate supplied, inert extinction/activation, mass residual, candidate core churn, and final spatial grids.
- Recovery timing, total retained mass and percentage of worlds without enough pre-existing organization for test eligibility.
- Failure of distributed “repair of repair” when either A↔R construction path is removed; compare against independent core recovery to avoid circular shell-based metrics.

The digital worlds **do not reproduce as organisms**, have no genome, bounded state and an arbitrary fixed law. No amount of visual ring formation can prove life, agency, sentience or open-ended evolution.

## Stop, interpretation and reproducibility rules

- If the seeded calibration produces no eligible regions, **report it** and consider a newly preregistered mechanistic calibration—do **not** increase seed/damage thresholds retroactively or exclude failing seeds.
- If the nutrient-only world produces apparent structures, trace all causal paths to the **basal S→A author-defined reaction**; do not claim primordial abiogenesis.
- If M rebuilds in the same way when M permeability is disabled, classify **structural material growth without demonstrated functional containment**.
- If removing an A↔R pathway only weakens the directly measured target product, note the tautological direct-production explanation.
- If random dispersed worlds perform as well as deliberately localized seeds, document absence of a seed-individuality advantage.
- Archive all failed worlds, trace lengths, seed/initial-mode/variant pairs, and source/model hashes before claiming any phenotype.

**Implementation:** isolated standard-library `experiments/closure_spatial.py`; independent `tests/test_closure_spatial.py`; matching bounded CI workflow. Keep all prior AL01/02/03/07 source code untouched. No arbitrary executable code, OpenAI API, exposed browser execution, autonomous web access, machine privilege, persistent runtime or connection to the user's dedicated local computer. The named source code and randomized dynamics remain separate from the observer UI.

**Frozen invocation after tests:**

```bash
python -W error::ResourceWarning -m unittest discover -s tests -v
python -W error::ResourceWarning -m experiments.closure_spatial --seeds 6100:6136 --output-dir runs/closure01-spatial --source-revision <source_sha>
```

The genuine next research question after this bounded assay is **endogenous individuality** under independent local-causality detectors, not assigning a vitality score to a grid. Preserve null outcomes and avoid after-the-fact rules designed to create a pretty organism.
