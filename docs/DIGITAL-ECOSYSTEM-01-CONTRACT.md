# DIGITAL-ECOSYSTEM-01 — prospective bounded world contract v1

October11,2026 human-approved strategic correction. The approved seven stage
names/subcategories remain; digital acceptance below is prospective. Preserve
all earlier physical protocols, receipts and negatives without rescoring them.
The VM/hardware is supplied infrastructure; organisms need not manufacture it.
Mechanical profitability is no longer a mandatory gate for digital evolution or
learning. This contract supplies possibilities, not discovered intelligence.

## Supplied versus emergent inventory

Supplied: integer VM, instruction meanings, organism boundary,6-cell program,
8-cell zeroed local memory, finite scheduler/food/material rules, copy errors,
birth/death mechanism, one deliberately reproductive ancestor, finite run limits,
measurement and checkpoint infrastructure. Ancestor code `[1,2,4,5,6,12]`
senses local food, tries to feed, writes its six program cells one at a time,
loops until a nursery is complete, divides, and loops again. This is an authored
reactive reproduction baseline; it is not discovered reproduction or learning.

Not supplied: a target descendant genome, success teacher, novelty reward,
optimized policy, learned memory contents, researcher rescue/repair, evolutionary
outcome, cooperation, parasitism or a strategy for an unseen challenge. Installed
mutation/copy/memory alone gives no credit for those achievements. All descendant
contents must come from executed parent writes; newborn memory starts zero.

AL01 accounting, AL02 executed-copy ancestry and AL03 ecology are reviewed design
precedents. Their frozen implementations are not changed or silently combined.
New files implement one separate computational substrate; legacy Ora/AgentTest
and observer remain separate. Existing native process limits/evidence budgets
are reused after exact-byte review. Old recovery profiles do not automatically
qualify this new state schema.

## World, resources and scheduler

Four positions on a ring share64 uniquely identified food packets,16 at each
position. Each has20 energy units and kind0/1 derived by the SHA256 address
`[seed,"food",packet_id]`, first8 hex digits modulo2. No replenishment. Initial
ancestor at position0 has12 energy, program material0..5 and memory material6..13.
Raw material14..511 is free. Total material512; total energy1292. Population<=32,
energy/entity<=64. Excess food energy becomes logged heat. Heat is unusable waste.
Food depletion and death count; there is no survival bonus.

One opcode executes per global step. Choose the smallest living ID greater than
the previous actor, wrapping to the smallest living ID. New IDs are monotonic
and enter that cycle; deaths release ownership. All actors use the same rule,
not fitness-weighted scheduling. Every opcode costs one energy to heat. Entity
local registers r0/r1 are integers; memory cells0..15; a single inbox holds a
0..15 message. Programs are only integers0..15, never host code. Their only
effects are the bounded VM operations below; no eval/import/shell/network/file
instruction exists. Local code is writable and mutations affect inert data.

## Complete instruction table

PC normally advances modulo6. The body/program length is fixed in v1; no
insertion/deletion or inferred open-endedness. The executed instruction is read
before any self-write. Empty/full/shortage operations do nothing beyond the
normal instruction cost, unless another result is specified.

| Integer | Exact effect |
|---|---|
|0|NOP.|
|1|SENSE: r0=kind of the lowest-ID local remaining food, or2 if none.|
|2|FEED: consume lowest-ID local food matching r0 modulo2; r1=success; gain20 up to64, overflow to heat.|
|3|MOVE: one ring position clockwise if r0 odd, counterclockwise otherwise.|
|4|COPY: if enabled, nursery incomplete, material and one extra energy available, read code[read], allocate lowest free material, pay extra1 heat, write nursery with source/destination/event ancestry, advance read.|
|5|BRANCH: PC=0 while read<6; otherwise normal advance.|
|6|DIVIDE: requires six executed writes,22 energy after base cost, eight free memory materials and population slot. Promote written nursery to child code, allocate eight zero memory cells, transfer12 energy to child, dissipate10 (memory8+division2); reset nursery/read. Otherwise refuse.|
|7|MEM_WRITE: mem[r0 modulo8]=r1 modulo16; base opcode pays write.|
|8|MEM_READ: r0=mem[r1 modulo8].|
|9|SELF_WRITE: if extra1 energy exists, pay it to heat and set code[r0 modulo6] to r1 modulo16; preserve its material ID and log old/new value.|
|10|SEND: to lowest-ID other actor at same position with empty inbox, deliver r1 modulo16; full inbox refuses, no hidden queue.|
|11|RECEIVE: if inbox filled, r0=message and clear inbox.|
|12|JUMP: PC=0.|
|13|INC: r0=(r0+1) modulo16.|
|14|TRANSFER: move one energy to lowest-ID other local actor if donor has it and recipient<64. Base instruction still costs1.|
|15|HALT: dissipate remaining energy; death.|

At energy0 after the operation, actor dies and returns all program/memory/nursery
material to the pool. No engine clone populates daughter code. Every birth lists
six parent write events and daughter material IDs; child experiences are not
inherited automatically. Communication and transfer compete for shared positions;
their enabling laws do not prove emergent ecological coordination.

Each COPY uses the SHA256 address `[seed,"mutation",global_write_index]`, first16
hex digits as integer d. In mutating mode, d modulo100<8 changes the opcode to
(old+1+(d//100) modulo15) modulo16. Faithful mode never changes it. Copy-disabled
mode writes no nursery material. This deterministic address scheme preserves
replay without sharing endogenous outcomes across arms. It is not an optimizer.

## First bounded population protocol and stop gates

Freeze source before execution. Seeds24000..24003, all three modes mutating,
faithful,copy_disabled,256 steps or extinction,12 complete unscreened worlds.
Environment food addresses match across arms; each arm earns its own resources,
births and outcomes. Report every death/extinction, unsuccessful copy/division,
birth, changed byte and descendant birth, not only a survivor. These are
descriptive four-seed measurements, not a statistically powered evolution assay.
Seeds24004..24011 are reserved and MUST NOT execute in this study.

StageA fixtures: positive supplied ancestor produces a certified birth; the SAME
birth interpreter refuses forged engine births/missing write ancestry. Disabled
copy and resource denial must not create births. Exercise all VM instructions
with software fixtures; fixtures confer no organism-behavior credit.
StageB population: first run the twelve frozen bounded histories. Required
infrastructure gates: every step conserves resources/ownership, birth certificates
match executed writes, no disabled-copy births, no faithful copy mutations,
independent instruction/event interpretation, deterministic source replay and
checkpoint64 continuation to the identical final history. Any mismatch stops
claims; preserve failures before repair. No favorable outcomes are promised.

Log program/memory hashes, IDs,parentage,generation,copy errors, resource use,
senses/actions,communication/transfers,self-writes,deaths,failed operations and
developer assistance. Snapshot includes all live code/register/memory/nursery,
food/material owners,clock,last actor,next ID,mutation write index and full event
history. Checkpoint restore is host engineering recovery, never organism repair.

No damage or unseen challenge is executed in StageB. Before those tests, freeze
meaningful internal digital damage that demonstrably destroys qualified function,
organism-caused restoration endpoint and untouched-resource controls. Before
learning claims, freeze resource-matched fixed-reactive,supplied-ancestor,
memory-disabled and own-history-disrupted controls with reserved unseen changes.
Before functional evolution claims, freeze no-variation/inheritance-disabled
comparisons, descendants' independent functional assays and founder denominators.
Genome diversity, survival, reproduction and duration alone are insufficient.

## Prospective seven-stage acceptance

Stage3: paid digital functioning, organism-caused repair/reconfiguration;
founder-free formation remains a separate3.5 claim, not prerequisite to every
other stage. Stage4: bounded ecological state/competition before a separately
authorized supervised persistent pilot. Stage5: executed descendant reproduction,
useful inheritance,variation,differential success,then sustained functional
evolution. Stage6: experience causally improves useful actions on unseen changes
within the SAME lifetime, separately from selection/reconstruction. Stage7:
flexible transfer/coordination and open-ended discovery only on new evidence;
intelligence and consciousness remain separate. No status advances by redirection.

No unattended world/service, OpenAI API/LLM, paid external tool, observer activation
or legacy change. All runs use operator locks, native time/memory/process caps,
finite disk evidence quota and5GiB free floor. Physical durability/off-host/full-
host recovery and production confinement gaps remain explicit; they are not all
mandatory gates for this safely bounded data-only experiment. Persistent pilot
activation still requires separate authorization.
