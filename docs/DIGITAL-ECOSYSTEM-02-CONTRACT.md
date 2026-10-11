# DIGITAL-ECOSYSTEM-02 v1: prospective paid triple-program world

Frozen before execution, October11,2026. One separate version of the primary digital ecosystem, implementing the dependency resolved by [paid binding01](DIGITAL-MEMORY-BINDING-01-RECEIPT.md). No extension or rescoring of closed ecosystem01, Task01 or binding01 laws/samples. Legacy AgentTest, observer and all reserved historical seeds remain separate. Reuse the reviewed deterministic accounting, executed-copy ancestry, round-robin scheduler and process/evidence limits; new state schema and interpreter are independently checked. The supplied VM is hardware/infrastructure, not an organism achievement.

## Candidate decision card and first gate

Question: can one fully paid, sandboxed computational substrate support ancestor and descendant reproduction alongside generic feedback, memory and interaction semantics? Necessary capability: entity-local inert triple programs can branch, compute, store feedback, self-write and causally copy their own paid words into new organisms. Smallest test: one disclosed reproductive ancestor in four seeds, each under faithful copying, installed mutation and disabled copying. Comparator: identical supplied ancestor with faithful copying; causal birth null: disabled copying with the same starting resources and base instruction charges. No installed learner, optimized strategy, target genome, hidden teacher, novelty reward or researcher rescue. Copy/mutation/birth primitives and favorable initial reactive food accessibility are authored assistance, not discovery.

Primary seeds24800..24803, unscreened; reserved24804..24807 remain unexecuted. Software fixture seed24790 is separate and not scientific replication. Horizon1536 global instruction quanta, extinction stop; tick64 checkpoint and exact resumed continuation. First infrastructure gate: generic independent interpreter accepts every full paid history and refuses impossible formation/parentage/balance/continuation fixtures; faithful arm births>=1 in every primary seed; disabled-copy births0 in every seed; mutation arm has at least one changed copied word pooled. No required advantage, novel behavior, descendant births, learning, repair or survival through change. Report them if observed without granting stage acceptance. If the supplied reproductive route is unavailable, stop and classify that dependency before broader panels; never tune these seeds or compensate resources. Claim-specific evolutionary or learning controls require a later frozen prospective test.

## Finite world and complete bill

Four ring positions,64 packets,16 at each position,20 energy each, cue=first8 hex digits of SHA256(`[seed,"food",packet_id]`) modulo2. Packet positions=ID//16. No replenishment, reward bonus or survival payment. Every ACT at a position with food consumes the lowest-ID local packet: successful port gains its20 up to body cap64, overflow to heat; failed port loses all20 to heat. This differs explicitly from closed ecosystem01's matching-food search. SENSE exposes that current packet's cue, not future packets, targets, genomes or researcher hints. Port target equals cue before global tick512, cue XOR1 at/after512. ACT's own success bit is the only feedback access. This predeclared change supplies a potential learning contingency; its occurrence/exposure alone is not unseen learning evidence.

One initial organism at position0 with energy12, six instruction triples below. Separate finite constructor stock128 pays one energy for each initialized program/state material cell. Code has18 cells and state16, so formation34, unused constructor94 inaccessible to organisms. Initial organism/environment energy1292 plus constructor128 = conserved1420. Food, overflow, computation and failed actions are explicitly ancestral heat; heat is unusable. Identity, parentage, energy registry, scheduler and environmental stock accounting are supplied infrastructure, not organism writable memory or unbilled learned state.

Material512, every body code word and state role has an assigned distinct raw unit. State16: memory8, registers2, PC1, cue1, feedback1, inbox1, position1, nursery cursor1. Code length1–32 triples; current ancestor and all descendants have six triples (no insertion/deletion). Memory/register values0–15, code words0–31; PC selects a triple; cue0/1/2 (2=empty); feedback0/1; one inbox empty or0–15. Nursery cursor is the count of paid writes, never arbitrary researcher adjustment. Program/state roles, including zeroes, need formation; no free daughter apparatus.

Every executed triple costs1 energy to heat, including unknown opcodes, failed/refused operations, branches, feedback access and memory operations. Instruction-internal PC/register/latch updates are explicit atomic semantics included in that base cost. COPY additionally pays1 per each of three code-word writes; SELFWRITE's one word is included in its base instruction. DIVIDE additionally dissipates16 for child state initialization plus2 release and transfers12 existing parent energy to child:30 parent energy after the base opcode. Transport, memory read/write, sensing and communication cost their base cycle; transfer moves existing energy only. These are authored digital constitutive costs, not physical prices/yields. No apparatus manufacturing or mechanical-profitability admission gate is imposed.

Population cap32. Every global quantum schedules smallest living ID greater than previous actor, wrapping; new monotonically assigned IDs join that same cycle. No fitness-dependent scheduler. Parent depletion to0 after an instruction releases all code/state/nursery units and records death. Failed formation leaves paid nursery intact until later successful division/death; birth promotes actual copied units, never clones host policy code. No maintenance subsidy, automatic organism repair, memory inheritance or researcher restart inside a run.

## Inert instruction semantics

Decode opcode,a,b from current triple before any self-write. Default PC advances modulo number of triples. Register selectors modulo2; memory addresses modulo8; branch destinations modulo number of triples; constants modulo16. Full/refused/empty operations still pay base1. No host-language evaluation/import/shell/file/network instructions exist.

| Opcode | Exact operation |
|---|---|
|0|SENSE current lowest-ID local packet cue (or2) into register a and cue latch.|
|1|Own latest ACT feedback into register a.|
|2|READ memory b into register a.|
|3|WRITE register b into memory a.|
|4|CONST b modulo16 into register a.|
|5|XOR register a with register b.|
|6|ACT using register a modulo2, attempting lowest local packet; update feedback0/1, record packet/cue/target/port/waste. Empty food returns feedback0.|
|7|Jump to b.|
|8|Jump to b if register a equals0.|
|9|SELFWRITE flattened code word b modulo code size to register a; preserve unit, record old/value.|
|10|COPY next three own code words into lowest three free units if copy enabled, nursery incomplete, extra energy3 and three materials available. Each word records actual source unit/value, index, destination, global writeID, tick and mutation. No half instruction copying.|
|11|Jump to b while nursery has fewer words than own code.|
|12|DIVIDE if paid nursery complete, extra energy30,16 free materials and population slot. Child at parent's position, code promoted from nursery, all16 state cells zero/empty, PC0, energy12. Record parent, generation, writeIDs, every child state initialization, release/energy transfer. Reset parent nursery.|
|13|MOVE one ring step clockwise if register a odd, otherwise counterclockwise.|
|14|SEND register a to lowest-ID other co-located actor only if that actor's inbox empty; no queue.|
|15|RECEIVE into register a if inbox present, then clear.|
|16|TRANSFER one parent energy to lowest-ID other co-located actor if extra energy>=1 and recipient<64.|
|17|HALT dissipates all remaining energy, dies.|
|18–31|Charged NOP.|

Installed mutation uses SHA256(`[seed,"mutation",global_write_index]`), first16 hex digits integer d: mutating mode d%100<8 changes copied word to `(old+1+(d//100)%31)%32`; faithful mode no change; disabled copying writes no nursery. This affects inert operands/opcodes, never host code, and is not strategy discovery. Inputs/stocks are matched exogenous opportunities; endogenous schedules/outcomes are not copied between arms.

Supplied ancestor: `[[0,0,0],[6,0,0],[10,0,0],[11,0,0],[12,0,0],[7,0,0]]`. SENSE,ACT,COPY,branch until nursery complete,DIVIDE,JUMP. No installed memory or feedback-learning routine, no supplied mobile successor. Descendants arise only from paid parent writes. Register/memory/code/PC/cue/feedback/inbox/position/cursor are durable channels; future experience nulls must cover every channel while matching resource costs. Survival/reproduction/genome diversity alone are not learning, useful inheritance, sustained evolution or open-endedness.

## Logs, replay and failure boundaries

Every step records identity, decoded triple, before body hash, actual sense/attempt/feedback, paid writes/self-writes/messages/transfers, birth/death certificates, full surviving actor state and full world hash. Snapshot contains all program/state/material, energy/food/heat, ancestry, counters, last actor, nextID and events; SHA256 over canonical sorted JSON. The independent interpreter derives each transition from the law and compares all state/checkpoint fields, not only totals. Restore reconstructs the executed prefix from genesis and refuses any mismatch in the complete checkpoint, including metadata. Exact tick64 continuation is software recovery only; no physical/full-host crash restoration is demonstrated.

Existing exclusive operator lock; check owner before stale action. Native cap128MiB/5CPU seconds/10wall seconds/3processes/output1MiB per bounded call. Disk floor5GiB plus evidence total64MiB; phases raw/archive/restore/failure16MiB each. Pin and export exact committed source/config before execution; source zip, SHA readback and separate restored-byte replay of every primary seed. Preserve native exits/failures and all twelve histories, including extinction. Independent audit after producer/interpreter checks metrics, source/receipt seals, process cleanup and all reserves untouched. No overlapping laboratory writer, persistent world/controller/observer/service/API activation. Off-host/full-host durability and production confinement remain explicit future persistent-pilot gates.

Next single decision: if basic paid population gate passes, prospectively choose a claim-specific comparison in this one substrate; require useful descendant behavior versus supplied/fixed/no-variation baselines for evolution or resource-matched memory/own-history disruption with reserved unseen challenge for learning. Damage/repair is not tested here; engine restart never receives organism repair credit. All Stage3/5/6/7 acceptance remains unchanged unless a corresponding independent comparison actually meets its own prospective gate.
