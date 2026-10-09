# REDOX-01 — founder-free photochemical state cycling and damage reconstruction

Stage3 sprint,2026-10-09; prospective distinct candidate, not a retuning of
RECYCLE-01, KINETIC-01 or GRADIENT-01. Replace polymer ligation/cleavage and bond
transport with finite photochemical precursor/conformer cycling. Installed abstract
chemistry and contact kinetics, not validated molecular chemistry or discovered
life. No supplied successful network, selected seed, rewarded action or controller.

## Hypothesis and finite law

Generic local catalytic conformers may arise from raw precursor pairs and improve
capture-funded useful reconstruction after blind damage, beyond equally funded
spontaneous background chemistry. A naturally supplied photon/thermal environment
is a resource, not evidence of externally designed useful organization.

48 identified precursor objects, each owning two fixed atom IDs (96 total), all
unactivated and noncatalytic initially;64 cells of an8x8 periodic lattice, random
unscreened positions. Pair geometry and16 possible conformer states are supplied
chemistry, not working founders. Every cell starts with16 identified photons:
1024 energy units.256 identified thermal-work units fund motion;16 operator units
reserved in EVERY arm for supplied-control genesis only. Gross1296, no energy
inflow/refund or matter creation. All heat, exported energy and unused allowances
remain counted. No separately hidden formation/release/endowment cost.

Capture at a precursor's own cell requires two photons, storing potential2.
Already charged/active objects cannot charge again. Formation consumes that2:
one conformer potential plus one heat. Thermal decay or damage dissipates the
conformer's1 potential to heat and regenerates the SAME raw atom pair. Subsequent
capture must pay another two new photons. No fuel is reclaimed from heat. No
polymer release/transport/bond route exists in this new law.

Conformers catalyze generic precursor-to-conformer transitions without being
consumed; that rate possibility is installed, not learned. For catalyst state k
and proposed product state j, compatibility is SHA256(ASCII'REDOX-01|k|j')[0]mod4=0.
Do not inspect or choose a successful catalytic network. Formation accepts one
byte<4 without a compatible nearby active catalyst, <64 with one. Same formation
price in both cases. Thermal decay accepts a byte<16. Motion spends one thermal
unit to attempt one periodic nearest-cell hop; at zero thermal work it refuses.
No chemical potential funds motion and no unpriced global routing.

Every step draws in order: action randrange4 (capture/formation/motion/decay),
slot randrange48, contact-token getrandbits64, product randrange16, acceptance
randrange256, direction randrange4, destination randrange64, noise getrandbits64.
Formation contact is token modulo the number of OTHER objects at Manhattan
periodic distance<=1, sorted by fixed slot ID. Empty contact lists leave basal
formation available. This registered local-contact law selects no useful type;
modulo bias is explicit. All arms share the exact8-call stream and full RNG state.
Initialize48 position draws, then12 blind supplied-control type draws in every arm.
No future sample is inspected before exact implementation/interpreter freeze.

New functional/decayed objects receive fresh monotonically increasing IDs, exact
atom ownership, precursor/catalyst ancestry and photon IDs with capture times.
Assisted ancestry persists through both precursor cycling and catalyst influence.
Store every birth, full final state/RNG and raw noise/transition history; per-step
current-state hashes include the immutable birth-history chain head.

## Fresh panel and independent controls

Seeds63000..63031;4096 steps;192 worlds in six paired arms, eight fixed24-world
batches. No discarded/replacement sample, horizon or rate change after execution.

* Candidate: local basal4/catalyzed64 law.
* Catalysis inert: basal4 even with an otherwise compatible active partner; same prices.
* Background null: basal19, catalyzed64.19=4+(64-4)/4 is a nominal fully occupied
  mean under a quarter-compatible hash distribution, NOT an upper bound on the
  realized fixed table or organized states. It supplies no founder or free work;
  same gross stocks/costs. A simple fast background must remain a serious alternative.
* Well mixed: same reactions; a motion attempts the drawn arbitrary destination and
  costs TWO thermal units, both debited atomically. Routing assistance is not free.
* Photon withdrawal: export all remaining photons at2048 before that step's action;
  retain/export/heat accounting and all paid buffers. This is resource withdrawal,
  not withdrawal of all apparatus or proof of living without energy.
* Supplied random conformers: before step0, try12 blind random types in slots0..11;
  each must pay2 local photons plus1 operator unit, yielding1 conformer/2 heat.
  Preserve failed genesis, every assisted ancestor and the same gross allowance.
  Supplied functionality is never autonomous origin.

At2048 before the first post-damage action, in every arm, deactivate ALL active
objects in the predefined left half(x<4). Same current object atoms retained,
potential to heat, fresh precursor IDs and assistance provenance. The fixed region
is not selected by observed function or abundance. Damage-inactive worlds remain.

## Primary gate, opportunity, falsifiers and stop

An endpoint requires a naturally generated, unassisted conformer that performed
paid catalysis before damage; its specific atom pair is deactivated by the blind
damage; it is rebuilt into an unassisted conformer with BOTH photons captured
after damage and a natural catalyst; its replacement subsequently catalyzes another
fully paid formation. The replacement may have a different state: report this as
functional replacement, not exact sequence inheritance. Separately report exact
state restoration and retained-copy/environmental reacquisition alternatives.

All32 candidate worlds are the frequency denominator. Require>=8 endpoint worlds
AND one-sided paired sign-test P<=0.05 versus the background null's endpoint
worlds. Report every control, wins/losses/ties, all inactive/damaged worlds,
pre-damage-functional and damaged-functional exposure, post-damage throughput,
capture costs, waste/heat, chemical-buffer ranges, and all resource zero times.
At least16 candidate worlds must have a pre-damage-functional atom pair actually
damaged; otherwise the reconstruction capability comparison is exposure-inadequate,
not a positive or universal impossibility result. No selective eligibility rescue.

If gate fails, close this law/horizon; preserve positive reactions, negative worlds
and exposure failures. No arbitrary favorable parameter/founder/sample adjustments.
A passing gate demonstrates bounded spontaneous functional replacement under
installed chemistry; independent reproduction and causal damage/structure tests
must precede self-maintaining-organization or inheritance claims. No reproduction,
evolution, intelligence or Stage3 completion inferred.

## Feasibility and verification before science

Prospective draw/endpoint clarification: only acceptance bytes in [basal,64)
establish causal catalytic influence; a transition accepted below basal is
spontaneous even with a compatible contact. Inert never has causal catalysis.
Damage exposure refers to the current conformer ID having actually catalyzed,
not an old conformer of the same atom pair. At2048 apply source withdrawal,
then blind damage, then the action; captures during that action count as after
damage. The draw cursor counts API calls, not internal variable MT word usage.
The primary endpoint concerns replacement of fixed feedstock pairs, not component
manufacture, reproduction or a demonstrated continuing organizational lineage.

Authored fixtures must prove full two-photon capture/one-potential formation,
paid decay/recycling/reconstruction, local shortage without global borrowing,
atomic thermal/operator payment, assistance persistence, post-damage-buffer
exclusion, all-arm exact draws and complete energy/material/object history.
These are supplied possibility fixtures, not natural outcomes. Freeze exact law,
draw layout, endpoint and separate interpreter before the unscreened panel.
Independent replay of the first24 worlds, all192 transition replays and rehashed
payment/noise/provenance forgeries required. Interpret all controls before next law.

Use reviewed existing Python, exclusive operator lock, no overlapping writers,
PYTHONDONTWRITEBYTECODE=1 and5GB floor PLUS reserved staging. Each primary/replay
batch uses guarded raw64MiB/archive16MiB/restore64MiB/failure1MiB phases, combined
128MiB. Eight primary batches plus one24-world replay reserve1152MiB, with64MiB
supervisor and16MiB verification: total1232MiB. Reserve failures, full source,
RNG/history, ZIP growth and restores before writes. Separate final publication/
backup staging needs its own finite manifest reservation. Per subprocess512MiB,
300CPU-second/four-process/300wall limits. This does not grant OS quotas or hostile
writer/physical durability guarantees. Keep all lab/temp/archive files on D:.
