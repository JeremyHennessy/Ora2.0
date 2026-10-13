# Renewable64: bounded ecology contract

Frozen prospectively October13UTC,2026. Version `DIGITAL-RENEWABLE-ECOLOGY-64-v1`.
This is a new environmental contract, not an amendment to Exposure23 or any
closed experiment. [Approved priorities](DIGITAL-DEVELOPMENT-PRIORITIES-20261013.md),
[original draft](DIGITAL-RENEWABLE-ECOLOGY-DRAFT.md),
[machine registration](DIGITAL-RENEWABLE-ECOLOGY-64-REGISTRATION.json),
[closed Firstborn63 result](DIGITAL-FIRSTBORN-63-PRIMARY-RECEIPT.md).
Status: DESIGN FROZEN; implementation/software/ordinary execution UNADMITTED.

## Question and supplied machinery

Can the existing disclosed NON-learning Mobile54 ancestor produce paid, viable
descendants that keep reproducing after founder expiration, under uniformly
renewed resources and finite individual execution budgets? This first admission
tests controlled lifecycle reachability. It does not test selection or learning.

Keep the existing digital instruction set, prices, body material, local memory,
movement, messaging, resource competition, COPY/DIV and ancestry. Reuse reviewed
code/contracts, not a wholesale VM replacement. Genomes remain sandboxed integer
data interpreted by the VM, without host Python, shell, network or filesystem
access. The ancestor is supplied exactly as nine triples:

`[[4,1,1],[6,0,0],[5,0,1],[6,0,0],[10,0,0],[12,0,0],[13,1,0],[13,1,0],[7,0,1]]`

Its fixed attempt-both-ports/COPY/DIV/movement cadence is authored machinery,
never discovered exploration or learned improvement. No selected historical
genome, successful updating policy, hidden teacher, repair, novelty bonus or
per-organism rescue. All new descendants arise from ordinary paid COPY/DIV.

Two demonstrated constraints justify the environmental additions. Exposure23 has
only1420 total energy with at least one unit irreversibly spent per instruction;
it cannot support indefinite activity. Fixed512 body words also bound concurrent
43-word bodies to11: without death/material release, at most ten additional
complete bodies can exist, regardless of fuel. Supplied uniform execution-budget
expiration makes turnover measurable without installing an organism death policy
or waiting for a mutation to create mortality. This constraint is not emergent
aging, repair or researcher-assisted survival. Both changes are declared before
any new outcome; the earlier draft lacked the execution limit and complete port
rule and remains preserved as a draft.

## State, material and VM instructions

All entities have a private code of3..96 words in triples, two four-bit registers,
eight four-bit RAM cells, PC, cue, feedback, inbox, position0..3, energy0..64 and
private unreadable nursery certificates. Birth inherits the copied program and
parent position only. Registers/RAM/PC/cue/feedback/inbox/nursery start zero/empty.
The16 paid state words encode the same fields as Exposure23. Parentage, generation,
identifiers, instruction counters and environment logs are external accounting
metadata, not free organism-readable memory or additional heritable channels.

512 reusable material unit identities belong exactly once to free storage,
living code/state or nurseries. Formation of the27-word founder plus16 state costs
43 constructor energy, leaves85 constructor/free469, and supplies12 founder
energy. Initial64 fuel tokens each contain20 energy and are separate exogenous
fuel, not body words. Initial total1420. Food locations are unchanged: IDs0..31
home0,32..47 site1,48..63 site2, no initial site3 stock. Home IDs16..31 are withheld
until64; the boundary costs16 constructor energy, leaving69. It is not a recharge.

Each executed instruction costs one energy before its action, adding one heat.
An ACT can rescue an entity whose just-debited energy is zero; death is checked
after the action. Code operands and all address/register reductions are unchanged:

| Opcode | Exact operation after base debit |
|---|---|
|0|SENSE stores position in cue and register a%2|
|1|READ feedback latch into register a%2|
|2|RAM[b%8] into register a%2|
|3|register b%2 into RAM[a%8]|
|4|CONST b%16 into register a%2|
|5|XOR register a%2 with register b%2|
|6|ACT using register a%2 modulo2; resets feedback0; attempt earliest accessible local token if any; success consumes it and supplies20 up to cap64, overflow becomes heat|
|7|JUMP to b modulo program triple count|
|8|IF register a%2 equals0, jump to b modulo triple count|
|9|SELFWRITE code value at b modulo code word count from register a%2; cannot change program length or material ownership|
|10|COPY the next three parent code words when copying enabled, nursery incomplete, free material at least3 and energy after base at least3; each word costs one additional energy/heat and gets a unique paid certificate; otherwise base-only refusal|
|11|If nursery length below code word count, jump to b modulo triple count; contents remain inaccessible|
|12|DIV only with complete nursery, at least30 energy after base,16 free state words and population below32; spends30:16 state +2 release heat +12 child startup; transfers nursery units to child, empties nursery, child position equals parent position|
|13|MOVE one site forward if register a%2 odd, backward if even, modulo4|
|14|SEND register a%2 to the lowest-ID same-site neighbour, only if that neighbour's inbox is empty|
|15|Receive/clear own inbox into register a%2 if nonempty|
|16|TRANSFER one energy to lowest-ID same-site neighbour if donor after-base has at least1 and recipient below64|
|17|HALT: all remaining actor energy becomes heat, then ordinary death|
|18..31|NOP after base debit|

On ordinary zero-energy/HALT death, all body/state/nursery units return to sorted
free storage. No automatic organism checkpoint rescue. COPY mutation remains the
existing deterministic per-word rule when mode is mutating: draw is first16 hex
digits of canonical SHA256 `[seed,"mutation",write_id]`; if draw%100<8, new value
is `(source+1+(draw//100)%31)%32`, else source. Faithful copying retains the source
but computes the same unused draw; copy_disabled refuses COPY. This is installed
variation, not organism-discovered mutation, and hash thresholds are not IID
Bernoulli evidence. First ordinary admission uses faithful mode only. No new
selector/rejection mechanism or researcher feedback on genomes. A later genome-level
mutation law requires its own prospective justification before any outcome.

## Resource renewal, sensory access and timing

Input modes are `renewed` and `no_inflow`. At each executed global tick divisible
by64, from64 through4096, renewed mode offers four20-energy tokens at EACH of four
sites. The outstanding stock cap is32 tokens per site, counting all remaining
initial tokens including the formerly withheld home stock. Process offers in
site0..3 order, each site's four offers in order. Every offer takes a new identity
from64 upward, including rejected offers, so identifiers do not depend on success.
Admit the offer only if current site stock below32; otherwise record an external
boundary rejection before entry. Rejected energy never joins internal totals.
There is no admitted outflow or heat removal. No_inflow mode records no offers.
No input follows extinction: global execution stops, with no host resurrection.

Initial token targets/kinds, the64 release and old remote phase flip are EXACTLY
the original Exposure23 formulas, pinned by source hash in registration. All newly
offered token kinds are `first8hex SHA256[seed,"renew-food",packet_id] %2`, observer
metadata only. New token targets at ACT time are:

`seed%2 XOR (first8hex SHA256[seed//2,"renew-port",site] %2) XOR int(tick>=2048)`.

This defines a shared hidden site mapping in each paired orientation, with a
declared global change at2048. No target depends on organism identity, genome,
ancestry, observed policy or researcher judgement. New home targets intentionally
use this explicit new-token rule; do not accidentally inherit an old packet-ID
conditional. Initial tokens retain their old target rule after2048.

The organism senses only position through SENSE and its own truthful ACT success
through feedback; it cannot read targets, packet kind/ID, stock, age, global tick,
inflow schedule or protocol metadata. Empty ACT feedback0 is not a truthful target
failure and must be labelled empty in evidence. Memory mechanisms are available
but this supplied ancestor uses no feedback-learning policy. The registered change
is an environmental challenge, not demonstrated adaptation or a held-out learning
claim. Paired arms share exogenous schedule and target law, never forced successes
or identical post-interaction stock outcomes.

## Scheduler, execution budget and expiration

Keep the deterministic lowest living ID greater than last actor, or wrap to
lowest living ID. One instruction per global tick; newborns participate in this
existing scheduler. Log IDs, last actor and actual opportunities; do not assume
every organism receives the full global horizon or promote late-born survivors.

Each entity has a256-INSTRUCTION lifetime budget, counted only when it actually
executes. The environmental turns map starts founder0 and each paid newborn0.
After each VM instruction, increment its actor's count, including the terminal
instruction. If VM death already occurred, retain that death reason. Otherwise,
on count256, expire the actor: remaining energy becomes heat; body/state/nursery
material returns to sorted free storage; death counter increases. No genotype,
generation, performance or researcher exception. Other organisms' budgets are
unaffected. This environmental counter is inaccessible/nonheritable and never
part of the16 organism state words; it grants no organism storage or energy.

Raw tick frames distinguish pre-instruction input, the unchanged VM action and
post-instruction expiration. Preserve the actual live VM after-body before an
expiration, the released unit/energy certificate and final dead/absent state.
Do not present that pre-expiration body as available after death. The full final
state hash includes lifetime counters, inflow counters/next token ID and scheduler
metadata. Expiration is supplied mortality, not self-HALT or repair.

## Accounting and complete lifecycle admission

At every subtransition, sum(live actor energy +constructor +20 per admitted
remaining token +heat) equals1420 +20*admitted_new_tokens. Offered equals admitted
plus rejected token counts. At4096 there are at most64 epochs/1024 offers/20480
offered energy; internal energy at most21900. Outstanding fuel at most128 tokens,
fixed body material512. Every birth consumes27 uniquely certified code units,
16 state units,2 release heat and12 startup. Every expiration/HALT converts
remaining energy to heat and releases actual owned units; no energy disappears.
Track unit reuse after death independently of merely continued host execution.

Minimum founder formation43 plus reproductive heat55 gives98 before acquisition,
movement, branches, failures, refusal and cap loss. The minimal COPY/DIV energy
debit is67 (ten base +27 copied words +30 DIV), of which12 transfers to child.
The ordinary9-cycle program takes70 founder instructions to its first division
under the old demonstrated route, not ten; renewal at64 can alter its actual
resource/cap timing, so Firstborn63's first-birth70 gate is NOT imposed here.
Subsequent loops have eight instructions and nine paid COPYs per full nursery;
actual DIV refusals, parent retention, transient energy and material availability
determine viability. No average-balance admission. Extra installed sampler work
is not a general minimum biological/digital reproduction price.

Freeze ordinary seeds65000..65003, two paired exogenous contexts/both orientations;
all use the exact supplied ancestor and faithful copying. Run ALL four renewed
and ALL four no_inflow histories, at original and restored canonical source, with
full4096-or-extinction endpoint and the SAME independent new-law evaluator. This
is eight original history roles/eight engineering replays, not16 independent
samples. Seeds65100..65103 are reserved UNOPENED; no fresh unseen or variation
panel is admitted by this protocol. No source-program bank or winner insertion.

Software reachability/refusal cases, exact canonical code/controller pins and
finite native/storage registration precede any ordinary World. Preserve all
ordinary outcomes, not only the first failure. Admission passes only if EVERY
renewed history has: valid accounting/replay/source/paid parentage; founder
expiration by its256th actual instruction; at least128 further global instructions
with only descendants; at least12 total paid births (exceeding the no-death ten-body
limit); maximum generation at least3; a paid descendant birth after founder death
whose parent acquired food personally before its birth event; an observed paid
generation1→2→3 chain with each reproducing descendant's prior personal food;
actual food acquisition from new tokens after founder death; and at least one
living descendant at the finite endpoint. All no_inflow controls must also pass
integrity, ancestry and endpoint checks; their viability failures are retained,
not grounds to stop/repair the renewed ordinary denominator.

These are prospective finite controlled turnover criteria. Endpoint survival is
censored, not indefinite life. Installed expiration helps create vacancies, not
successful organism behaviour. More fuel can remove selective pressure; cap
losses, untouched stocks, ACT opportunity success/failure/empty, competition,
allocation refusals, actor turns, generation/death reasons and full resource bills
must be reported. An ordinary failure closes mutation/selection admission and
preserves the failed configuration; no posthoc rate/age/horizon/threshold changes.

## Finite execution and replay

World horizon4096 global instructions or extinction, population cap32/actual
27-word lineage body bound11, genome length fixed, no host children spawned by
organisms. At most409 births by nine-COPY-plus-DIV work; at most12288 paid word
writes; at most1088 offered/initial packet IDs. These are conservative analytical
bounds, not performed work or guarantees of viable generations.

Prepared fixtures use explicit non-scientific seeds/stub states with World
trapped wherever possible; no65000/65100 context or mutation queries in design.
Before ordinary execution pin exact new producer, independent referee, source
manifest/contract/configuration, worker/controller and evidence harness. Reuse the
existing exclusive PID-owned operator lock/prewrite quotas/native caps/archives.
Check lock owner before stale action. No competing writers. Exact execution
supplement will specify row transport and meaningful output bounds before runs;
these conservative ceilings alone do not admit a runner:

- Child256MiB/30CPU/60wall/three slots/native output1MiB, decoded history64MiB;
  outer512MiB/1200CPU/2400wall/four slots. Maximum34 children: two prepared plus
  sixteen generators and sixteen full referees at original/restored sources.
- Main8192MiB(raw/archive/restore2560 each,failure512), controller8MiB,24GiB free.
  Sixteen rows ×64MiB plus34 native outputs ×(1MiB+16KiB) +64MiB metadata/source
  and32MiB ZIP overhead remains below2560MiB per phase.
- Same-host source/evidence seals, streamed archive/full byte restoration, raw
  native exits/timeouts/truncation/cap readbacks/process closure and independent
  storage audit. Native/identity/accounting/replay/transport failure is integrity
  failure, not an organism result. Preserve partial outputs without blind retry.

Checkpoint at executed tick64 or earlier extinction. Restore by deterministic
genesis replay under the NEW law, checking complete state, scheduler last/next ID,
write IDs, lifetime counters, token IDs/counters, source/config and all events;
then resume original/restored Worlds to4096/extinction with exact equality.
This means32 generator World trajectories/constructors for16 generated histories,
not32 independent scientific samples. Efficient direct-state continuation is a
later engineering deliverable, not a claimed achievement of this contract.

## Acceptance boundaries and next dependency

Design earns no stage credit. Ordinary pass supports controlled paid descendant
turnover in this bounded authored environment only. Variation, useful inheritance,
differential reproductive success and selection need a separately registered
unscreened population and causal controls after viable ordinary admission. Choose
later generations/opportunities prospectively from actual ordinary exposure and
cost evidence; no universal Firstborn63 gate. Resource persistence, diverse genomes
and births alone do not establish sustained evolution, open-endedness or learning.

Single next ecology dependency: implement this exact environment and independent
VM/resource/lifetime referee, reuse the existing finite harness, and demonstrate
software reachability/refusal before a pinned ordinary execution registration.
The [older-history learning table](DIGITAL-OLDER-HISTORY-ADMISSION-DRAFT.md) proceeds
independently, with no reproduction prerequisite. No primary learner is supplied.

Keep all historical laws/prices/results/samples/reserves, approved observer UI,
paused observer, private integrated ancestry, separately owned AI-Research and
15-minute development/three-hour audit cadence. No persistent/unattended world,
public runtime, service, self-hosted runner, OpenAI API/LLM/paid service or legacy
AgentTest change. Off-host/full-host durability, confinement/process identity,
retention and separately authorized supervised pilot remain future gates.
