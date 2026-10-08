# HEARTBEAT-03 — finite sequence-world continuity

2026-10-08. Freeze before implementation. Extend the verified HEARTBEAT-02 commit
rule and stable cooperative OS lock in a separate heartbeat03-v1 schema.
Old counters, laws, data and interfaces remain unchanged. TURNOVER-01 supplies
an engineering reference world, not a newly accepted science candidate.

## Authoritative state

Configuration: existing development seed 1, initial work 0..1000, original
total horizon 1..128. Acceptance uses work 96/horizon 32 and work 0/horizon 8;
no fresh scientific sample. Serialize the complete active sequence-world state:
unique atoms, external origins, recovery markers, live objects and consumed
parent IDs, nutrient stocks, waste provenance, usable work, heat and bonds.
Also serialize full Python Random.getstate (including Gaussian cache), noise
cursor, simulation tick, event hash chain and immutable history of every born
object. Object IDs may never be reused. Resume restores the saved generator
state, not a seed-only replacement, and consumes exactly one quintuple per tick.

Independent replay regenerates genesis and every on-demand noise request,
compares full generator/state/history after every transition and conserves all
atom bits and energy. It imports the independent material auditor, not a worker.
The uninterrupted reference must also match TURNOVER's existing development
stream and law. Identity binds world/configuration/source files/Python/revision.

## Recovery and observer

Complete append/LF/flush/fsync frames remain the commit boundary. Snapshots must
equal a fully audited journal prefix. Missing/lagging checkpoints can be rebuilt;
partial/corrupt journal or corrupt/ahead/non-prefix snapshot fail without changes.
Pending files are never authoritative. Stable OS lock and finite 32-resume cap
retain HEARTBEAT-02 semantics; no PID lock deletion or silent history truncation.
Resume preserves original identity and total horizon. Pauses/status frames do
not advance noise, objects or energy. Terminal resume is byte-idempotent.

Read-only observer reports committed tick, noise cursor, object/atom counts,
energy and checkpoint lag, heartbeat age and unverified process health. It must
not modify state or turn recent metadata into a liveness claim.

## Bounded acceptance

Reference 32 ticks and zero-work 8 ticks (neutral motion/damage still progress).
Actual subprocess exit at tick 5: pre-commit 77, post-journal 78, post-pending 79,
post-checkpoint 80. One continuing identity suffers sequential 5/pre-commit,
6/post-journal and 7/post-pending faults. All seven exits, four single histories,
one triple history and pause/resume at 5 must match uninterrupted complete
canonical state sequences, including generator/history, byte-for-byte. Journal
prefix bytes remain intact; epochs/wall times/status frames are excluded from
equivalence. Prove terminal idempotence and missing/lagged snapshot restoration.

Reject coherently rehashed changes to random state/cursor, draws, world state,
ancestry/object history, energy and tick; source/config/world/Python mismatches,
partial tail and invalid checkpoint. Real competing resume must exit 2 without
changing unlocked bytes. Preserve failures, source, logs and independent audits,
replay and same-D archive restoration. Manual lab lock, 5GB floor and external
300-second subprocess timeout remain required.

This is bounded process-exit recovery of a stochastic finite reference world,
not power-loss/storage-failure recovery, off-drive backup, security isolation,
evolving-population continuity, self-maintenance or continuous runtime. No
unattended/external service, automatic resume or fresh scientific panel.
