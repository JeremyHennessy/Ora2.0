# CONSTRUCTOR-01 component-history measurement v1

2026-10-08. Commit this contract before auditor/fixture implementation. The
paid law in `constructor01-law-v1.json` and its design contract remain frozen.
This gate validates authored receipts only, with zero new scientific seed
initializations. It is not the natural-opportunity study or a world runtime.

## Receipt schema and independent validation

A receipt has exactly schema `constructor01-events-v1`, case, mode, initial,
events and terminal. Mode is active/fixed/ghost/direct/external_source.
Initial/terminal state fields: integer nonnegative P,W,S (list of site nutrient
counts), waste,heat; objects mapping unique nonempty IDs to role A/C/I/D,
site,origin,producer_id,roots,functional. Site count1..8. Each site has at
most one object of each role. Genesis objects have origin `genesis`, no
producer and root list equal to their own ID. All initial object mass and
S potential count as supplied laboratory resources. Genesis heat/waste may
be zero or positive but cannot appear or disappear later.

Events contain exactly seq, request, result, opportunities, before_sha256,
after, previous_sha256, sha256. Requests: action,site,role,new_id. Allowed
actions build/external_build/direct_build/contact/decay/impair. Birth actions
require role and a new ID; decay/impair require role and null new_id; contact
requires null role/new_id. The chain begins at SHA256 of canonical initial
state. Hash canonical JSON with sorted keys, compact separators and UTF-8;
an event hash excludes its sha256 field. Hashes detect inconsistent bytes,
**not authenticity**: independent semantic replay must also reject a coherently
rehashed forged history. Do not accept a claimed summary as an authoritative
endpoint. The auditor imports neither the fixture writer nor any simulator.

Reconstruct every live slot, birth, retirement, cost, result and state from
initial state and requests; compare claimed producer/root tags and complete
poststates exactly. Never reused successful-birth IDs, even after retirement.
Builds record their actual live same-site catalyst ID, not a merely existing
genome/role or retired parent. Initial state does not contain invented births.
An attempted failed birth creates no object or ancestry.

## Operations and availability denominators

Internal build: occupied slot, missing catalyst, P<4, W<2 are unavailable in
that precedence. Otherwise pay4P/2W, heat+2 and create object from live
same-site catalyst (A->C; C->A/I/D), origin internal, inherited root list.
External build bypasses the catalyst but pays the same4P/2W, origin external,
new root=self. Direct build is legal only in direct mode and uses the same
price, origin engine_direct, root=self. These two are explicit laboratory
shortcuts and can never be reported as internal production.

I is functional except in ghost/external_source modes; A/C are functional,
D is inert. Fixed mode uses the same law and is a valid installed-physics
counterpart. All mode/functional flags must agree. Contact at W0 is
unaffordable; at W1 pays read1W into heat then fails processing; W>=2 pays
both1W charges even if nutrient or function is absent. With S>0 and live
functional I, consume oneS, waste+1, W+3, heat+5 and log source local and
actual I ID. External_source contact instead logs source external and null
interface ID, with exactly the same S/work/heat debits and no assumed
independent forecasting/controller. If S0, return unavailable empty after
paying; otherwise missing function is unavailable no_function.

Decay of a present role retires its ID to4waste, charge0. Paid impairment of
a present role requires1W, adds1heat and retires4mass to waste; absent role
or W0 is unavailable (absent before work), with no charge and no future
replacement of the target. The auditor must distinguish attempts from
successful removals and preserve unequal subsequent trajectories.

Before **every** request report eight booleans: vacant requested product,
catalyst present, funded internal build, funded bypass build, interface
present, nutrient present, funded local contact and funded external contact.
These derive from prestate; irrelevant build flags are false outside birth
requests. Availability does not imply a sampled encounter, event or useful
maintained network. Exact mass/P/work/heat invariants and integer/nonnegative
constraints apply to every event, including failed attempts and read-only
exhaustion. Shared banks and zero passive upkeep remain installed assumptions.

## Endpoints reconstructed from history, never user-supplied

Report internal C births, external/direct births, all local/external
conversions, conversions using supplied I, and conversions using newly
internally assembled I. Report distinct I IDs separately from conversion
counts; events/fixtures are not independent populations.

A **renewed production-chain use** requires a paid local conversion by I4
with these exact causal relationships (labels denote distinct IDs, not
literal names):

1. I4 internally born from live C3; C3 internally born from live A2.
2. A2 internally born from live C1; C1 internally born from live A0.
3. A0 was retired **before** A2 birth; C1 retired **before** C3 birth.
4. Every parent was local/live at its corresponding birth; all four new
   objects have distinct, paid birth events. Source is local, not external.
5. Reconstruct inherited external roots and report them explicitly. A0 may
   be a genesis/external precursor; its descendants remain externally rooted.

Missing ancestors, retained old objects, externally rescued C3, installed I,
retrospective source, one C birth, or passive persistence do not satisfy this
chain. A validated chain is a narrowly authored causal history **not** natural
formation, sustained closure, autonomous maintenance, repair, reproduction,
evolution or life. Fixed-law chains are accepted, not falsely called evidence
against or for emergence. Unique I IDs and converted units remain descriptive.

## Authored validation cases and failure tests

Valid fixtures: passive retention, supplied I, one internal C then I,
renewed A/C chain, supplied C shortcut, externally rescued C, direct-bank
shortcut, ghost renewed chain, fixed counterpart, external-source effect,
P0, work4 trap, work1 partial contact, matched C/D impairments and a
cross-site absent producer. These are16 authored receipts, not simulations of
random populations. Only active renewed and fixed renewed fixtures satisfy
the renewed-chain-use endpoint. Every fixture's unavailable controls count.

Adversarial tests coherently rehash after changing costs, material/heat,
functional flags, producer/roots, ID reuse, retirement order, cross-site
producer, mode and opportunity flags. Also test malformed schema/integers,
missing events, partial-payment invention and corrupt/truncated chains.
Reject violations rather than returning a successful classification. Valid
external shortcuts must stay valid but fail the internal renewal endpoint.

Manual Windows acceptance uses existing Python, operator lock,5GB floor,
300-second per-process limit, clean pinned source ZIP, exact fixture/report
replay and preserved same-D archive. Original runtime receipt remains reported
AL01 evidence; no new restart, power-loss, off-drive backup or isolation claim.

## Admission and next step

If measurement/adversarial checks pass, freeze a separate full finite
unscreened stochastic protocol (fresh seeds96 onward, no8000..8063), before
simulator implementation. Define neutral proposals, geometry/genesis law,
budgets, natural availability denominators, first-natural-new-C impairment
ordering and fixed/ghost/direct/external controls. Do not use authored schedules
or shorten the ancestry criterion after seeing data. Zero matched triggers
means no causal test. Stop rather than retune old worlds or activate a worker.

Repository intake at this gate: Ora main d001203616c13fbb6fa312dc1101ee09c1def26d
(verified PR21) and AI-Research main f2839a5c3ca8871d97a18f00073e00590966e122
(final Pass16) unchanged. No new research reproduction or architecture import.
Track B heartbeat/persistence/observer remains separate and inactive; off-D
backup, physical power loss and hardened isolation remain unresolved.
