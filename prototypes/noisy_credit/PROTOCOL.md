# Noisy delayed credit, frozen exploratory protocol v1

This is a NEW authored-controller assay, not a native Ora World, population,
evolution experiment or reproduction demonstration. The old binary controller
census, seed banks and native physics are not inputs. All rules below are frozen
before outcomes. A negative result is final for this attempt; no retuning.

Question: does integrating noisy, delayed personal experience repay its full
declared abstract execution and storage bill, against cheap alternatives?

Four equally sampled recurring cues, four actions, 384 trials per lifetime.
Each cue has a hidden preferred action. A fresh independently sampled mapping
replaces it periodically, including possible unchanged entries. Preferred action
succeeds with probability 0.8, each other action with probability 1/15. The same
pre-generated uniform variate is used for all policies on a trial. Thus rewards
are stochastic, not labels revealing the correct action. Feedback and food arrive
after 2 trials in development, 3 in validation. There is no feedback after the
384-trial horizon; unresolved attempts earn nothing. Cues are always observable
only by paying, target/noise/future are inaccessible to controllers.

Development: seeds 1000..1015, switch period alternating 64/96.
Validation: seeds 9000..9031, switch period alternating 80/128, independently
generated contexts, mappings and noise. No development outcome is a validation
input. Select ONCE by development mean final energy (dead actors score zero),
then name order on ties. Freeze selected candidate before validation evaluation.
Report all development candidates, all validation worlds and failed lifetimes.

Candidate family: optimistic per-cue four-action saturating counters, widths
1/2/3 bits and failure decrements 1/2. All counters begin at their common maximum
(no task knowledge); choose largest counter, lowest action on ties; success
increments attempted counter by one, failure decrements it. This learning rule,
optimistic initialization and representation are SUPPLIED. Parameters are
heritable in principle only; no mutations, selection populations or births run.

References: all four constant actions; all 256 cue-fixed maps (choose one on
development only); global cyclic win-stay/lose-shift; cue-specific cyclic
win-stay/lose-shift; cue-specific last successful action; cue-specific cumulative
success/failure estimator with optimistic unseen actions. Select strongest
reference by the same development criterion. Also report every reference on
validation, including retrospective strongest (not a deployable selection).
Fairness: an action-independent outcome does not supply a hidden target label.

Causal comparisons for the selected candidate: true personal feedback; feedback
clamped to failure while physical food unchanged; erase counters before each
decision; misattribute feedback to the next cue modulo four. All pay identical
operation/storage charges and physical success uses actual actions. These are
whole-life counterfactual comparisons, not authentic native checkpoints.

Resource rules: initial energy 128, cap 512, food 8 (unchanged from earlier
controller assay). Unit is 1/64 energy, exact integers. Action costs 1; cue
sensing 1 where used; feedback sensing 1 where used; a counter/WSLS update 1;
cumulative-estimator update 2 and decision arithmetic 2. Counter/WSLS lookup is
included in the action operation, not charged twice. Each allocated private bit
costs 1 energy at formation plus 1/64 per trial storage rent. Program formation
cost: constant 1, cue-fixed 4 + 8 table bits, WSLS 8, counters 12, estimator 16.
WSLS state is 2 bits globally or 8 contextual; counters are 16*width bits;
estimator has 16 successes and 16 trials as 9-bit counters (288 bits).
Delayed-learning metadata queue allocates (delay+1)*5 bits (cue2/action2/valid1).
All candidates pay for queue capacity even when empty. Estimator therefore may
fail formation; preserve that result. Fixed policies do not sense feedback or
allocate a learning queue, but food is still delayed externally.

Order: formation; each trial storage rent, delivery of due food (feedback
sensing BEFORE food for learning policies), paid update, optional erasure,
cue sensing, estimator arithmetic, paid action. Every payment must leave
strictly positive energy; otherwise death is immediate, no later food rescue.
Overflow is recorded as heat. Final energy = initial - all paid costs + actually
delivered food - overflow; dead remaining energy is recorded separately and
fitness proxy is zero. No copying, division or offspring continuation exists:
NO reproductive-fitness or all-native-cost claim is permitted.

Primary success: selected candidate beats the development-selected reference
on validation mean final energy AND has a positive paired difference in at
least 24/32 validation worlds; true feedback also beats each causal ablation
in mean energy. Report survival, delivered rewards, attempts, operation costs,
storage, formation and clipped heat. No significance or generality beyond this
finite distribution is implied. A strong-reference failure is not learning
success. Higher accuracy by itself is insufficient.

Execution: one trusted finite child using the existing Windows Job runner:
120 CPU seconds, 256 MiB Job, one active process, 300 s cooperative total wall,
32 MiB polled output budget. Do not import native VM, read archives, call models,
touch assistant state or retry a failed run. Unit fixtures are not assay runs.

Architectural implication is limited: a supplied compact learner's viability
does not establish that the native 27-word VM can discover or afford it. No
native price conversion, natural inheritance or cumulative intelligence claim.
