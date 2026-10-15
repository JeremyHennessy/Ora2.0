# Prospective per-batch size clarification, before execution

Review caught a counting ambiguity in frozen paid-reference v1: each individual
history has at most4input events, but the nine-history batch has at most36.
The per-history8192-byte input allowance therefore occurs NINE times. No World
or outcome has executed; no cap, role, horizon, programme, task or price changes.
Keep original v1 bytes and this clarification with both hashes in admission.

Correct conservative batch bound:
2304ordinary-events*3072 +9*8192input-addition +9*32768static +65536wrapper
=7,512,064 canonical bytes, strictly below unchanged8MiB=8,388,608. The ordinary
allowance excludes input rows (counted separately), includes fixed event/body/
code/state/hash/death fields. No COPY/DIV/sampler/new-entity/provenance growth.
Tests must retain all36input-event allowance and exact bound. Actual hard writer/
reader extent still stops overflow; this arithmetic is not a memory/CPU fit
guarantee or a physics/capability result. Source and all cases remain unscreened.
