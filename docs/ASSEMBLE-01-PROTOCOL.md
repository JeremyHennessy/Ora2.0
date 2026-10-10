# ASSEMBLE-01 — finite fuel-driven assembly and useful renewal

Prospective registration, 2026-10-10. No historical law or sample changes.
This is a new dimensionless toy law, not an empirical molecular model.

## Question and novelty

Does a chemically paid assembly/disassembly route, competing with fuel waste,
increase finite-time profitable restoration of a resource converter? LOCAL
only paid activation from a work store and used symmetric catalytic barriers.
Here fuel directly changes assembly state, while a distinct passive release
route closes a fuel-consuming assembly cycle. Unlike the supplied RATCHET
motor, every world begins with two raw atoms, zero work and no working object.
The installed three-conformation load coupling is deliberately conventional;
its existence, chemistry and small geometry are not discoveries or life.
Direct fuel coupling alone was already tested; the new question is competing
fuel-driven assembly turnover combined with raw-start useful work and repair.

## Complete law

Two labelled reusable atoms occupy two degenerate sites. Ten labelled tokens
are fuel F (potential 6) or waste P (0). Raw atoms have potential 0; a colocated
dimer's conformations A/B/C have potentials 1/4/3. Initial heat 8, work 0,
all ten tokens F: conserved energy 68, twelve material identities.

Every reaction has its exact reverse. Fuel assembly: raw pair + F -> A + P,
heat +5. Passive assembly: raw pair -> A, heat -1. Chemical drive:
A + F -> B + P, heat +3. Relaxation B -> C, heat +1. Load C -> A,
work +2, heat unchanged. Waste route F -> P, heat +6 in every conformation.
Reverse routes pay the stated heat/work and regenerate fuel when applicable.
All stores must remain nonnegative. No replenishment or implicit chemical
potential, one-way drive, resource grant, founder, steering or rescue.
Symmetric free-atom/dimer diffusion has zero cost in this explicitly ideal,
degenerate two-site model; it is not directed transport or an empirical price.

Each direction's acceptance is prefactor / 64 times
2^min(0, delta_heat). Candidate assembly/waste prefactors 32/2;
independent 17/17; shuffled 2/32. Drive, passive assembly, relaxation, load,
diffusion all 16. Both directions share each barrier. The shuffle swaps
allocation between productive and dissipative fuel routes, not component
labels. Same labelled proposal alphabet and sum of barrier allocations 34;
actual occupancy-weighted flux is NOT asserted matched. All arms retain every
reaction, load and physically attainable endpoint. This is a kinetic route
test, not a topology or universal superiority claim. Any positive result
requires a further throughput-matched control and reserved-sample reproduction.

## Accounting admission before samples

Exhaustively enumerate the complete reachable physical graph; independently
verify reverse actions, energy, material, heat degeneracy and labelled-token
multiplicity. Check a paid raw-start certificate in EACH primary arm. The
certificate consumes two assembly tokens and eight drive tokens: 16 useful
work, two full formation bills of 6 and destruction bill 1, surplus 3. Final
store 15; post-damage work change 9, fresh-output-minus-post-bills 3. This
authored possibility is not a sampled result. Overall fresh load output <=20;
this is a fresh-provenance bound, NOT a bound on thermal/recycled gross output.
Do not simulate if the independent gate rejects accounting or attainability.

## Frozen sampling, damage and endpoint

32 fresh unscreened seeds 85000..85031, each in three arms, 4096 attempts;
reserved seeds 85100..85131 untouched. Two initial random site bits. Each
attempt selects uniformly among 68 slots: for each of ten tokens assembly,
drive and waste each in directions -1,+1 (60); passive assembly, relaxation,
load each -1,+1 (6); two hop slots (2). Draw one u32 acceptance and one recorded
unused noise u32, including every rejection. No seed retries or screening.

At attempt 2048, blind atom-0 destruction if bound and work >=1: break dimer,
return both atoms raw, work -1, heat +(old body potential +1). No damage otherwise.
The old dimer ceases to exist; fresh objects preserve both atom identities and
ancestry. Paid formation creates a new dimer. A first rebuilt dimer must remain
current at the end and produce fresh useful work. Every accepted action, object,
token provenance, state and final RNG/draw hash is retained and independently
interpreted. Waste-to-fuel regeneration is paid and never restores virgin status.
Fresh work means the conformation was charged by a token's FIRST forward drive;
load reversal, thermal regeneration and fuel assembly receive no fresh credit.
All reverse load transfers debit the conservative linked-output ledger.

Require documented fresh load output before loss, actual loss, new first
reconstruction, fresh output through that reconstruction and four strict
positives: whole store change, post-damage store change, whole and post fresh
output minus ALL net formation bills and destruction. Fuel assembly costs 6,
passive assembly costs 1 (heat); exact reverse refunds same; destruction 1.
Formation fuel is a maintenance input distinct from the environmental fuel
used for conversion. Do not double-debit formation from work: it is not paid
there. Protect initial heat (end >=8) AND post-interval heat (end >=pre-damage).
Report chemical depletion/regeneration, gross thermal work, complete bills,
reconstruction and exposure separately. No external assistance exists, so this
is not a withdrawal experiment; post-depletion activity is diagnostic only.

Candidate needs >=24/32 functioning losses, >=8/32 successes and one-sided
paired exact McNemar versus BOTH primary controls with Holm familywise .05.
Otherwise FAIL or UNDEREXPOSED; close this exact law/resources/horizon. No cost
decreases, extra fuel, longer horizons, new favourable seeds or tuned barriers.
Independent interpreter must reproduce EVERY state, rejection cursor, ledger
and ancestry; exact replays seeds 85000/85015/85031 all arms; refuse altered
payment, ancestry and draw hash. Finite operator lock, 300-second process caps,
512 MiB allocation bound (not measured peak), 200 MiB evidence reservation,
5 GiB disk floor, source pin, off-drive readback and preserved negative baselines.
No continuous operation, observer publication or legacy changes.
