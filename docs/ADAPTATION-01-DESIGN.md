# ADAPTATION-01 — experience improving useful action under unseen change

Separate prospective design track. No controller installed, AgentTest changed,
reward function supplied, LLM introduced or simulation activated by this document.
Reproduction is not a prerequisite for this question. KINETIC-01 component
reconstruction cannot answer it: that chemistry has no registered action-selection
or experience-plasticity mechanism.

## Question and candidate substrate

Can a finite physical state altered by prior encounters improve resource-acquiring
actions during a previously unseen environmental change, compared with equally
funded fixed reactive behavior? The primary outcome is useful action/energy return,
not prediction accuracy alone or attractive movement.

Assess a distinct bounded sensor–interaction substrate with generic finite
state and local encounter-dependent trace updates. Sensory exposure, state writes,
reads, interaction/action execution, maintenance and movement must all have explicit
energy/material costs. The world supplies finite consumable resources and hazards;
do not add a success score, teacher action, correct policy or externally replenished
agent energy. Any plasticity law is an installed possibility, openly declared,
not an emergent ability. Random initial structures cannot be screened for success.

An informative environment must separate the immediate cue from the delayed
resource consequence. Independently generated, held-out changes should include
cue reversal, changed delay and new resource location; the actor receives no phase
labels, future randomness or privileged resource map. Experiences are ordinary
world interactions, never curated demonstrations. Do not choose a substrate solely
because it resembles a conventional neural architecture; compare simpler physical
traces and finite-state interaction mechanisms before freezing one candidate.

## Required causal comparisons

Use prospectively paired unscreened initial structures and environmental tapes:

* Experience-dependent candidate, with paid state formation/readout/maintenance.
* Fixed reactive control, same initial structure, sensing and action budget.
* Memory-disabled control, same charges for attempted state writes/reads; no retained
  encounter information. Lost resource must become audited waste/heat.
* Association-disrupted history control, same paid state capacity and actual
  incoming environment. Independently precommit an index permutation of retained
  observed outcomes relative to their cue/action records. Preserve the exact
  memory intervention and its external assistance cost.
* Order-only history permutation, as a separate diagnostic. This preserves whole
  cue/action/outcome records and tests temporal-order dependence; it does not
  remove experience information from an order-insensitive learner.

Report all actors, including immobile, depleted, extinct and unsuccessful ones.
Matched resource allowances cannot refund unused memory costs after seeing outcomes.
Learning-period advantage does not establish generalization: require a prospective
paired advantage on unseen challenges, alongside costs and survival denominators.
Prediction diagnostics, action usefulness, within-life improvement, selection and
inheritance remain separate outcomes. No selection or reproduction occurs in this
first causal test; descendants would need a later independent contract.

The independently audited [finite correlation preflight](CORRELATION-CAPACITY-01-RECEIPT.md)
finds that full incoming-input permutation changes resource capacity in18/30
rows despite equal single-symbol marginals. Freeze the identical incoming
environmental source across causal arms. Shuffle retained history only; price
that intervention and memory reset. Input corruption and dynamical phase
self-correction do not count as reconstruction of apparatus or useful learning.
Information ceilings are not measured action quality or attained energy output.

## ADAPTATION-CONTROLS-01: distinguish order from association

October 11, 2026. Design clarification only; no actor, controller, scientific
sample, action policy, reward function or new world law is implemented.

An authored semantics example illustrates the distinction. Four observed-memory
records have cue/outcome pairs `(A, resource), (B, empty), (A, resource),
(B, empty)`. Reordering those four whole records retains exactly the same pair
multiset. A learner using aggregate cue/outcome counts therefore receives the
same association information, although chronological order changes. Permuting
only their retained outcome references can instead produce `(A, empty),
(B, resource), (A, empty), (B, resource)` with unchanged cue/outcome marginals.
These are invented explanatory records, not measured experiences or a policy.
The illustrative swap is not a permutation selected or frozen for an experiment.

Keep chronological world events immutable in every arm. Memory intervention
changes only the actor's retained internal state, never the real outcome, current
sensory exposure, resource identity, arrival time or incoming environment tape.
Only actually observed past outcomes are eligible: never inject a hidden resource
map, phase label, future event or teacher action. The evaluator must retain the
source-record identities and slot mapping for audit without exposing those
provenance labels as privileged actor inputs.

Before execution, freeze the substrate's realizable memory representation,
eligible observation window, intervention schedule, permutation generator and
independent random stream. The index permutation must be independent of cue,
action, outcome, phase and success. Do not search for a permutation that destroys
a favorable association. A random permutation can leave useful associations or
fixed points: report the realized disruption, all permutations and inadequate
exposure rather than claiming guaranteed erasure. The authored example above
does not establish exposure adequacy or an effect-size threshold.

Read, write, reset, transport, storage and intervention costs remain UNKNOWN
until the installed physical law defines them. Meter actual costs, including
content-dependent resets and external memory editing; common allowances and
attempted-operation counts cannot establish equal physical cost by themselves.
Use precommitted matched budgets, preserve heat/waste, and never refund or
replenish an arm after seeing its outcome. If the substrate cannot implement the
registered intervention without hidden support, do not execute this comparison.

Acceptance still concerns paired net useful action on unseen changes against
profitable fixed-reactive, memory-disabled and association-disrupted controls.
Matching an order-only control does not by itself reject experience-dependent
improvement. Outperforming a corrupted history does not by itself establish it:
the candidate must also beat fixed reaction and disabled memory under complete
costs, with adequate observed-memory exposure. Prediction, useful action,
within-life adaptation, selection and inheritance remain distinct endpoints.

## Executable reference-plan semantics (design only)

`experiments/adaptation_shuffle_plan.py` produces a bounded permutation **plan**,
not a controller, actor-input adapter or memory edit. The separate
`adaptation_shuffle_audit.py` interpreter checks plans without importing the
producer. The authored test source is the four explanatory records above;
there are no actors, new world outcomes, reserved challenges or learning results.

Evaluator records have exact fields `id`, `event_step`, `observed_step`, `cue`,
`action`, `outcome`. `observed_step=None` means unobserved. Only records actually
observed strictly before the cutoff are eligible; sort by observation time and
immutable identity, then retain the newest bounded window. Equal-cutoff
observations are excluded. Source chronology and identities stay unchanged.
Reject duplicate identities, nonchronological events, observations preceding
events, extra phase/teacher fields and boolean integer forgeries.

Freeze the seed independently **before viewing outcomes** in a future protocol.
The planner cannot prove that a human supplied it prospectively. A SHA256 counter
stream, domain `ora-adaptation-reference-plan-v1` followed by a zero byte, uses
eight-byte big-endian seed/counter values. The first eight digest bytes supply
unsigned draws. Reject draws at or above the largest multiple of the current
range at most 2**64, then use descending Fisher-Yates. Identity permutations and
fixed points remain included. Never search for a better disruption. Sixteen
fixed software-test seeds test determinism; they are not scientific samples.

For `order`, donor references move entire retained records. For `association`,
each slot keeps its own cue/action references and receives only the donor's
observed outcome reference. The interpreter reports whether the realized
cue/action/outcome multiset actually changed and how many fixed points remain.
Empty and singleton windows cannot establish disruption. Changing unobserved or
future payloads must not change eligible references or donor order. The full-world
digest changes if those payloads change: it is evaluator provenance, **not an
actor input**.

Plans contain evaluator identities, source digest and seed. A future physical
memory implementation must keep these outside the actor-facing interface and
expose only realizable retained sensory state. This helper does not implement
that boundary or authorize applying a plan. Planned reference read/write counts
are bookkeeping; they omit substrate-specific operations and are **not** physical
prices or proof of equal cost. Every plan and audit keeps
`physical_cost=UNKNOWN` and `design_only=True`; forged paid-cost or activation
claims are refused. Raw memory construction, state read/write/reset, intervention
cost, useful action and unseen-challenge performance remain unmeasured.

The reviewed helper source `e50341f89f4812230c54792fc189448ac7abcd72`
passed nine focused tests. All 32 authored plans (16 fixed software seeds, two
intervention kinds) passed separate interpretation and restored byte replay.
Whole-record order preserved associations in all 16 examples; outcome-only
permutation changed them in 13 and preserved them in 3. Preserve all outcomes;
this is an illustration of partial disruption, not a scientific effect estimate.
No worlds, actors, holdouts, memory edits, useful work or learning were measured.

Immutable local evidence: `D:/OraLab/runs/adaptation-reference-plan01-20261011`.
Seventeen raw seals, exact source, native process exits, tests, plans, interpreter,
archive and restored replay are preserved. Every child exited zero without
timeout or output truncation. Limits were 128 MiB allocation, 15 CPU/30 wall
seconds, four process slots, a 5 GiB disk floor, exclusive operator lock and
13 MiB combined prewrite evidence quota. Independent quota audit measured
945,428 logical bytes. Archive SHA256:
`32ceb6b4f7d1150f8eaf3a41145cbc91121f6e3b69285660588865f2efcaf6ee`.
Same-drive restore is not independent-host or physical-durability evidence.

## Counterfactual opportunity and selection boundary (design only)

October 11, 2026. This resolves a design ambiguity, not a new actor, policy,
experiment, challenge sample or demonstrated learning result.

Pair arms on the same **exogenous opportunities**, not forced identical realized
outcomes. A frozen environmental tape may declare finite resource arrivals,
hazard changes and challenge randomness. Each arm has its own equally endowed
world copy and material ledger. Its actions determine encounters, consumption
and delayed consequences under the same installed law. Different actions can
therefore produce different future sensory records and useful returns. Copying
the candidate's successful outcome stream into a control would supply feedback
that the control did not earn and invalidate the useful-action comparison.
Keep a mapping between corresponding exogenous resource identities for audit;
do not transfer consumed material, work or outcome knowledge between arms.

At a registered memory intervention, preserve that arm's already realized
world chronology and actual past outcomes. Apply only its own eligible observed
history to its retained state. Donor references must never cross actor/arm
boundaries. Provenance labels, hidden maps and future consequences stay evaluator
only. The earlier rule that memory editing does not change the real outcome
means an existing observation cannot be rewritten; it does not force all future
outcomes to match after changed actions. A common exogenous tape is not a teacher
or a prerecorded action-contingent success tape. Meter editing and all subsequent
actions separately, including arm-dependent costs and waste.

The primary independent unit is the prospectively paired, unscreened founder
and challenge allocation, not a time step, encounter or surviving actor.
Freeze the unseen challenge generator and reserve its independent random stream
before fitting/selecting any candidate or fixed-reactive design. Development
may use separate training opportunities only, with search/selection costs and
chosen designs declared before holdout access. The actor receives no phase
labels; held-out change definitions are evaluator-only. Do not select a reactive
baseline after seeing holdouts or give it fewer lawful resource opportunities.

Report unconditional paired net useful returns over every allocated unit,
including depleted, immobile and dead actors; do not discard their realized
costs or condition the primary result on survival. Post-depletion actions cannot
be imagined or refunded. Record survival and action/memory exposure separately.
Repeated encounters are nested observations, not additional independent founders.
Useful action means audited retained/exported work after its full bill, not an
evaluator reward. Any terminal salvage valuation must be defined by the same
law before sampling, not invented for successful survivors.

Within-life change requires traces from the same identified actor without
reproduction, replacement, researcher rescue or population selection. A paired
holdout advantage over all required controls is distinct from improved training
prediction, surviving an easier realized path or selecting a better initial
design. Adequacy, effect threshold and paired statistic remain to be frozen only
after a complete paid substrate exists. This clarification supplies none of its
missing physical memory/action prices and authorizes no helper execution.

Documentary audit: frozen 28efeda34500cb183514a189c455e834fe055edc;
`D:/OraLab/runs/adaptation-counterfactual01-20261011/independent-audit.json`.
Eight sealed records passed separate hash/archive restoration, design-scope,
null-work and plan consistency checks; all 851 shared tracked files unchanged.
The contemporaneous failed public optical-paper retrieval is preserved, not
treated as methods evidence. Accounted storage 773455 bytes under 8MiB, with
2MiB per phase and 5GiB free floor. Archive SHA256
bd99a274ac307a40f41d566a5ede806a6f208abb7f70867d3c123f91bde72ad4;
auditor SHA256 dbeab20c4fbb5b96ea096f8aa99db584e3c2def23f16a95e33db62c6d8d017e7.
This is documentary verification, not a controller or learning result.

## Freeze gate and stop decisions

Before executing this design, specify the exact physical law, resource stocks,
trace update/decay rule, neutral initial distribution, action space, experiences,
challenge generator, exposure adequacy criterion, seeds, duration, paired statistic,
effect-size threshold and falsifiers. Verify independent replay, memory/energy
accounting and causal controls on authored fixtures. Reserve unseen samples before
development; no tuning their challenges to the candidate's policy.

Reject useful experience-dependence if the candidate fails the registered unseen
action comparison, if fixed reaction/association-disrupted history explains the result, or if
the advantage depends on hidden subsidy or privileged phase information. Inadequate
action or memory exposure invalidates an informative capability claim; record it
before registering a genuinely different substrate. A positive result would be
bounded within-life adaptation under installed physics, not general intelligence,
consciousness, evolution or autonomous life.
