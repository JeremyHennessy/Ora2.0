# B-COMP-01: can inherited programs evolve useful delayed computation?

Prospective scientific design, v1, 2026-11-12. **NOT EXECUTABLE AUTHORITY.**
No seeds drawn, no population created, no candidate runtime installed. This selects one
next experiment, replacing neither old science nor its historical renewal proposal.
The exact future kernel, independent DATA verifier, inactive artifacts and byte-level
founder still require isolated engineering qualification before a scientific release.
Changes forced by implementation must be reviewed and frozen before outcomes, not tuned
after observing success. This is a local evolvability feasibility experiment, not an
open-endedness demonstration or a field-first discovery of digital memory.

## Hypothesis, nulls and independent unit

H: a small fixed host with generic programmable state admits ordinary inherited variants
that combine two separated inputs, preserve the useful function through reproduction,
and gain paid reproductive opportunity under an explicit information-dependent CPU grant.
The ancestor reproduces but has no input/output behavior. The solution sequence is NOT
seeded, transplanted, protected, or searched for in preparation.

Strong alternatives: cheap current-cue/constant/periodic behavior; accidental correlations
or input-history access; selection for copy speed unrelated to computation; random variant
sampling just as effective; transient non-inherited function; output spam; substrate too
fragile for useful variants to reproduce; a tiny finite-state policy explains everything.
The last alternative bounds a positive claim to evolved finite-state computation, not
learning. We deliberately do not ask organisms to learn the XOR rule during their lives.

Eight independently committed seed blocks. Three conditions per block (24 bounded jobs):

* **S — coupled selection:** ordinary mutable paid replication; task outputs can earn CPU.
* **N — no task payoff:** identical physics/IO/mutation, but task outputs earn no CPU.
  The unused global CPU remains available to basal scheduling; total executed budget equal.
* **R — parent-blind mutation search reference:** externally constructed candidates, not a
  naturally reproducing population. A 64-slot reservoir starts with the same ancestor;
  choose a reservoir parent uniformly, edit using the same mutation operator, pay the
  declared copy/evaluation costs, evaluate for a fixed 256 charged steps, and replace a
  uniformly drawn slot regardless of outputs, fertility or score. Partial last evaluation
  is retained as incomplete, not promoted. Evaluation is no-payoff and founder-only;
  paid children are diagnostic records only, removed as in the solo assays, never scheduled.
  A partial candidate never replaces a fully evaluated slot. This is mutation sampling with unbiased
  genealogical accumulation, not an assertion of equal mutation or reproductive opportunity.

S versus N is the primary intervention on useful-computation selection. R is a secondary
search-efficiency reference, **not** a randomized ecological equivalent. Fix total charged
training work, additionally report variants, mutation proposals, births and evaluations;
do not claim those different denominators were matched. R's catalog can contain functional
programs without paid ancestry. Its primary-style functional measurement therefore does
not require paid ancestry; inheritance and reproductive utility are separate outcomes.
Evolution includes random variation: this design tests contributions of selection and
inheritance, not whether evolution is categorically different from randomized search.

The independent analysis unit is the seed block, never a descendant, trial, condition or
deterministic re-evaluation. Eight is a bounded exploratory panel, not a power claim.

## Minimum proposed kernel, not a feature wishlist

Integer-data-only variable programs of 8..64 fixed-width instructions, three 8-bit
registers, four 8-bit RAM words, PC, copy head and lifetime counter. Operands are bounded;
relative branch targets wrap within the program. Instructions: NOP, IN, OUT, MOV, NAND,
LOAD, STORE, JZ, JMP, COPY, DIVIDE. No task-specific XOR, memory-rule instruction, historical
input buffer, arbitrary host operation, messaging, subroutine library or self-write.
IN writes current bit and phase to two designated registers; the third is unchanged.
It never returns the previous cue, correct answer, future RNG, population score or ID.
General conditional flow and RAM allow composition; larger RAM is not assumed helpful.
Proposed word encoding is `(op,a,b)`, op0..10 in the order listed above, a/b unsigned bytes.
Register and RAM operands reduce modulo3/modulo4; a branch uses signed8-bit b relative
to current PC, modulo tape length. Ignored operands remain legal neutral variation.

COPY copies the next instruction into a private nursery, spends one execution charge plus
one copy-write charge, allocates one unique free material word, advances the copy head,
and sets the third register to whether more parent instructions remain. It never clones
the entire tape for free. DIVIDE requires all copied words, funds initialization of ten
state words, transfers the nursery to a child, resets nursery/head, and otherwise refuses
after its base charge. Mutation applies to daughter instructions, never host semantics.
All science must log paid material ownership and every mutation; DIVIDE does not reread
or silently repair a damaged parent. Birth initializes RAM/registers to zero, not learned
parent state. PC/head/counter are also explicit bounded state, not free hidden memory.

The proposed ancestor is the ordinary copy loop plus neutral padding, length16:
`COPY; JZ R2,+2; JMP -2; DIVIDE; JMP -4; NOP x11` (targets are relative to current PC).
All positions, including copying/branching/division, are mutable. Future byte encoding
must reproduce exactly this abstract program; no optimizer or solution insertion.
Neutral padding is supplied scaffolding and imposes copy cost, not discovered complexity.
An independent engineering trace must establish ancestor replication and ordinary
one-edit viability without evaluating mutant task performance. Failure means revise
design prospectively or stop, not protect the kernel or seed a successful genotype.

Per-instruction substitution .01 at COPY; choose uniformly from the other legal triples.
After a nursery completes, propose insertion .005 then deletion .005, at most one each,
uniform boundary/site and uniform legal inserted word. An out-of-range-length edit is
rejected without redraw; the otherwise copied daughter remains eligible and the rejected
proposal is logged. An accepted insertion allocates one distinct material word and pays
one write charge; deletion returns its word to free storage. No unaccounted byte appears.
Cache that nursery's indel proposal until birth or nursery loss: blocked DIVIDE must not
redraw a favorable edit. If extra material/state/CPU cannot be paid, no child is released.
Rates are design choices, not optimized from outcomes. The exact PRNG and event-level
atomicity must be frozen with the kernel before seeds.
No recombination, human winner selection, external archive reinsertion or rescue.

## Explicit computational ecology and costs

Start S/N with one supplied ancestor, otherwise empty capacity64. Fixed material pool
16,384 unique words covers live tapes, ten-word states, nurseries and free words. On death
all words return; no new material enters. At capacity a birth replaces a uniformly chosen
occupied slot, including possibly its parent, then transfers paid nursery/state. Replacement
is a supplied experimental dilution mechanism, not evolved mortality or ecological closure.
Every entity expires after4,096 basal opportunities if not replaced sooner. Bonus work is
charged but does not secretly alter its input clock or lifetime opportunity. No reseeding.

Basal scheduling gives each live entity one instruction opportunity per round in fixed
rotating order. A correct eligible output can request32 extra instruction credits, each
spent only when executed; cap each organism's queued bonus at64. Bonus service occurs
after that organism's basal service in a round, before moving to the next entity, up to
32 bonus instructions per round. CPU is withdrawn from the same finite job ledger, never
created: all base steps, bonus steps, copy writes and state initialization count. Unspent
credits at death/end are not executed work and cannot be inherited. N performs the same
output checks but queues zero bonus. This authored task-to-compute grant is **explicit
engineered selection**, not endogenous goal discovery or unbounded free energy.

An output earns at most one bonus per episode; all invalid/duplicate/early outputs cost
their normal instruction but earn nothing. No global memory access, use of journal or
evaluator state, variable instruction cost dependent on correctness, or host-clock input.
Birth/division-only programs remain strong competitors; the assay must not force the
desired behavior by killing nonresponders. Fixed expiry and finite total CPU are declared
constraints, not evidence of autonomous sustainability.

The 32-credit opportunity is a prospective cost budget, not a discovered biological law.
The four-NAND mathematical witness needs seven scalar operations plus delay; this does
NOT prove a full runtime policy's advantage. Before freezing release, an authored control
must independently pay all polling, input, memory, copying, division and delay costs and
show a possible net reproductive benefit versus the cheapest fixed/reactive references.
If it cannot, stop before science; do not inflate bonuses after observing populations.

## Information opportunity and shortcut defenses

Each organism's local basal-opportunity count defines64-turn episodes. At turns0..7 expose
cue x with phase1. Expose blank bit0/phase0 for g turns; then expose probe y/phase2 for
eight turns; remaining episode turns are blank. Only the first OUT during probe phase
is eligible; output low bit must equal x XOR y. Bonus instructions see the same current
input/phase until the next basal opportunity; they never advance the input clock. Omission
is incorrect. Input acquisition
is paid; no automatic history buffer or answer opcode. Cue/probe bits are independent
fair bits from separate exogenous domains; training gaps g are8,12,16 uniformly.
Episode number, seed, hidden bits, target, global time and RNG state are not readable.
Birth restarts local episode with a fresh independent stream, never a favorable first cue.

The current y and phase cannot predict missing independent x; conditional on any current
input, a history-independent strategy has expected accuracy exactly.5. Constant, current
cue, phase/age/periodic patterns and previous-output strategies are explicit references.
Finite training streaks can beat.5 by chance; no such streak is discovery evidence.
Registers, PC, heads, RAM, execution location and any accessible resource/scheduler state
must all be included in the information-channel audit. No claim that only STORE is memory.
Timing can store x if the program changes its state in response to x; that is legitimate
finite-state information use, not a shortcut. Timing that leaks x without program exposure
is a bug. Input streams are independent of the program's outputs/reproductive success.

## Census, held-out assays, lineage and utility

Training stops at262,144 charged virtual steps, first extinction, STOP, or resource/integrity
failure. Save every endpoint occupied slot (up to64), with multiplicity, not a post-hoc
best organism. For R use its64 candidate slots; unevaluated/invalid slots remain visible.
No held-out score affects training, candidate retention, reproduction or seed selection.

All behavioral and solo reproductive assays are founder-only: each child is fully paid
and constructed, its immutable birth/genotype record retained, then its material is
returned through an explicitly labeled assay-removal event before the next instruction.
It is never scheduled or returned to evolution. This prevents a child-storage cap from
silently replacing the founder or censoring one assay at64 births. Removal is an assay
intervention, not an ordinary ecological death or evidence of viable grandchildren. They are
experimental evaluations, not unmanipulated ecological continuations.
For every unique endpoint genotype, a prospective isolated evaluation supplies64 episodes
(4 balanced x/y combinations × 4 unseen gaps10,14,20,24 × 4 repetitions), in a committed
unpredictable order. Each assay starts zero-state, mutation off, no offspring reinserted.
This is distributional transfer to sequences and timing, not a claim of a new task/domain.
All genotype types share the same test panel, which remains sealed until training ends.
Use full endpoint census weights; a genotype occurring40times contributes40/64, not one
arbitrarily chosen champion. Empty slots contribute zero for a valid extinct population.

Repeat a no-payoff behavioral assay after restoring ALL organism-visible cue-dependent
state at the cue→blank transition to its common pre-cue snapshot: PC/registers/RAM/heads,
nursery/copy-progress flags, bonus queue and every other identified accessible channel.
Fixed genotype and current/future input/episode accounting are held unchanged. Counterfactual
restoration is an explicit assay intervention, not an ordinary lawful World transition;
log removed/restored material, credits and state in a separate intervention account so
it cannot masquerade as conserved biological reproduction. Offspring stay unscheduled,
and no retained child record or host record can signal the erased cue back to the founder.
Report this as a broad intervention, not a memory-localization proof: resetting execution
can itself damage a program. Also replay paired opposite-cue snapshots followed by the
same probe, checking deterministic continuation and no hidden input leak. Correct balanced
history-conditioned outputs plus audited isolation, not erasure failure alone, establishes
history dependence. Conditional code location qualifies as memory just as RAM does.

Operational **functional qualifier** Q: at least58/64 intact correct responses, at most40/64
after complete-state erasure, and the independent replay/channel audit passes. Thresholds
are conservative design labels, not significance tests on64 independent organisms.
Record continuous accuracies and all response patterns too. The experiment cannot select
a different threshold because a near miss looks interesting.

Two further solo assays use the intact genotype with the same64 episodes, mutation off,
and task bonus enabled versus disabled. Both get exactly the same4,096 basal instruction
opportunities and input sequence. Bonus instructions are additional paid work, recorded
separately against the reserved assay ledger; only founder paid births count, with child
removal handled as specified above. Children are never fed into evolution. This identifies
within-genotype task-resource reproductive utility without attributing background effects
to a particular opcode. It measures solo paid-birth throughput, not competitive fitness
or population growth. A genotype qualifies as reproductively useful only if bonus-on
paid births exceed bonus-off, with complete cost closure. Raw accuracy without that
effect is reported as capability without demonstrated reproductive benefit.

For each endpoint-qualified Q genotype in S/N, trace its earliest recorded program origin
retrospectively from complete archives, without selecting founders for reruns. Report paid
parents/children/grandchildren, copy certificates, lost intermediates, same-program persistence
and contemporaneous rivals. Transient genotypes absent from the endpoint are not Q-assayed
under this budget; their functionality remains unknown. Do not impute it from ancestry.
Endpoint ascertainment can miss innovations that arose and were lost; this is an explicit
limit of the prevalence endpoint, not a whole-history discovery census.
Paid inherited function needs an original paid child and grandchild carrying the functional
program, not just a genotype in the endpoint catalog. Also report new syntactic variation
and useful function separately. R is not eligible for natural paid-inheritance claims.

## Registered outcomes and analysis

For each block/condition, F = number of endpoint slots carrying Q /64: qualifying occupancy
of the fixed capacity, not prevalence conditional on the number of living organisms. Also
report the actual living denominator and conditional prevalence where nonzero. The primary
exploratory estimand is mean of the eight paired `F_S - F_N`. Report all eight differences,
both census denominators, raw accuracy and descriptive SD/sqrt8 (undefined n<2). No
powered significance claim. Secondary: F_R and paired S−R with its non-equivalent-search
caveat; Q origins, inheritance, paid reproductive utility, first appearance, prevalence,
extinction, copy speed, program length, mutation opportunities and cost per useful origin.
Do not condition the primary analysis on Q appearing or populations surviving.

Functional discovery, inherited retention and reproductive utility are separate gates for
the architectural interpretation. Continue only with repeat evidence (at least two
independent S blocks containing paid inherited useful Q) and positive primary mean; report
R even when it matches or beats S. These are engineering/scientific decision thresholds,
not a p-value or broad evolutionary law. If R matches S, the claim that selection improved
discovery is unsupported even if representability is established. If Q arises but does not
pay reproductive costs or persist, the central hypothesis is not supported at this budget.

Valid extinction/no Q/sterile lineages are scientific zeros. Interrupted, missing, corrupt,
invalid or over-limit jobs are NOT zeros and never replaced or retried. With missing required
outcomes, full eight-block contrast is unidentified; provide available paired outcomes with
their exact denominator and missingness limits, plus F-based worst-case bounds where useful.
No dropping difficult seeds or pooling with AL02/AL03. All three conditions per block are
preassigned. Block0..7 arm orders are SNR, NRS, RSN, SRN, NSR, RNS, SNR, NRS;
this counterbalances time position as closely as eight blocks permit. One active job at a time.

## Proposed finite envelope and pre-release conditions

24 jobs, eight blocks×three conditions, no retries/replacements. Proposed per-job envelope:
262,144 charged training steps; at most64 unique endpoint genotypes; at most four4096-base-
turn assays per genotype plus enabled bonuses. Copy writes and ten-word birth-state
initialization are additional charges, not free instructions. Set a hard maximum of
4,194,304 charged steps/job; truncation is explicit incomplete evidence, never covertly
relax the cap. The reproductive bonus assay can exceed4096 executed instructions but
not its4096 basal opportunities; bound extra instructions by32 per eligible episode and
include them in the overall cap. Maximum campaign virtual work100,663,296 charged steps.

Propose retaining5s child-Job CPU,10s wall,128MiB,3active processes and2process births per
job (aggregate120CPU/240wall seconds). These are **proposed ceilings, not measured capacity
or an inherited grant**. Full traces of many more virtual steps need a separately approved
new evidence envelope: proposed32MiB raw+32MiB journal,96MiB archive/job, plus128MiB research
overhead =2,432MiB campaign storage. Historical AL03's1MiB evidence ceiling is NOT silently
increased or reused. Inert worst-case trace/replay measurements must establish that full
records and assays fit CPU/evidence caps; otherwise revise the prospective budget or stop
before authorizing science. No extrapolation from AL03's tiny workload proves feasibility.

Approximate implementation: one bounded integer transition kernel, one small task adapter,
one independent DATA replay/analysis module, and source/condition admission using existing
Job, journal and custody mechanisms. Expect hundreds, not a new general framework of
thousands, of scientific transition/verifier lines; this is a planning estimate, not a
delivery guarantee. Exact source reuse/rights and cost measurements remain engineering
questions. Do not port all Avida, Mobile54 or a mutable interpreter merely for this assay.

Before science: freeze exact word encoding, legal mutation alphabet/PRNG, founder bytes,
paid transition ledger, verifier, assay accounting, source pins and inactive artifacts;
qualify IO isolation, one-output grants, state reset, conservation, reproduction, corruption
rejection and no-World admission with authored fixtures. Verify no unintended innate task
skill. No task-performance mutant search or prospective population calibration is permitted
under this research instruction. Reuse existing process/custody/review without changing
scheduler, director, accounts or OS privileges.

After source/protocol qualification, create a seed-free protocol commitment, then derive
8 block seeds with domain-separated SHA256(`B-COMP-01|protocol_digest|block|draw`), rejecting
previously consumed seed/context identities by a declared registry. Derive separate PRNG
domains for mutation, dilution, inputs, arm and held-out panels. Commit all actual seeds,
orders, holdout hashes and fresh attempt paths before running any condition. No such seed
list or release authority was created here. A final independently recorded GO must bind
the exact package and the owner must separately authorize these24 jobs and assays with
the final evidence budget. Preserve existing STOP until that release, and preserve every
consumed claim/failed record. STOP on integrity failure; never use a new run to repair data.

## Limits and next decision

A positive result would demonstrate naturally varied inherited programs discovering and
retaining a new useful finite-state computation under disclosed artificial task selection.
It would not demonstrate spontaneous reproduction, endogenous goals, sustained ecology,
learning an unknown rule, evolving interpreters, intelligence or open-ended innovation.
If a one-bit FSM explains it, say so. If task rewards alone explain success, say so.
Only after this gate should a separate protocol ask whether experience can alter an
inherited policy advantageously under hidden rule changes versus inexpensive fixed and
reactive strategies. No further study is automatically authorized.
