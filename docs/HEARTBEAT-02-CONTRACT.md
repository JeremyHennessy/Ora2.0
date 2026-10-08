# HEARTBEAT-02 — finite counter checkpoint continuity

2026-10-08. Freeze before implementation; extends engineering evidence only.
Preserve HEARTBEAT-01 schema, files and receipts unchanged. No new scientific
worlds, population persistence, service, automatic restart or unattended run.

## Identity and commit rule

Use a separate heartbeat02-v1 schema, explicitly launched on a new directory.
Immutable identity binds world ID, exact source revision, configuration,
worker/auditor file SHA256 and Python version. Counter configuration remains
work0..1000 and max_ticks1..1000. One tick consumes1work and produces1heat.
Journal genesis and every committed state retain identity and simulation tick.
UTC heartbeat and invocation epoch are metadata, never simulation advances.

Complete append/LF/flush/fsync journal records are the commit boundary. After
each record, flush/fsync a pending checkpoint and replace checkpoint.json.
Checkpoint must equal a fully audited journal prefix; a lagging or missing
checkpoint can be rebuilt from the complete journal. A corrupt/ahead/non-prefix
checkpoint, malformed manifest, changed source/configuration, broken/partial
journal, invalid identity or nonconserving history is rejected before mutation.
An abandoned pending file is ignored, never authoritative. No tail truncation,
silent corruption repair or lost-history replacement. Missing genesis requires
manual investigation, rather than creating a new world during resume.

Acquire a nonblocking OS file lock on a stable one-byte writer.lock. Never
unlink this file or decide lock ownership from a PID or timestamp. Initial
directory creation admits one founder; resumes require an existing lock file.
Kernel lock release after process exit allows explicit manual resume; an active
holder rejects all competing resumes. Windows uses msvcrt.LK_NBLCK, Unix uses
fcntl.LOCK_EX|LOCK_NB. These are cooperative local filesystem controls, not
host isolation or adversarial filesystem security. See [Python locking API](https://docs.python.org/3/library/msvcrt.html).

## Lifecycle and audit

Genesis epoch0 running/ready at tick0. Advance records increase tick exactly1
within the original total horizon. A per-invocation optional pause_after records
paused/operator_pause at that tick without state change. Explicit resume from
running/paused appends running/resumed with unchanged state and epoch+1;
maximum32 resumes. No transition after exhausted/tick_limit terminal; repeated
resume of complete output is an idempotent verification, not a new history.
Resume options must repeat original world/revision/work/max_ticks; any mismatch
is rejected. Fault injection and pause are invocation controls, not new laws.

Independent read-only auditor imports no worker; verifies manifest, hash chain,
sequence, complete state transitions, energy, epoch/lifecycle and checkpoint
prefix. Reports verified journal tick separately from checkpoint lag, status,
heartbeat age and unverified process health. Does not promote a lagging snapshot
to current or write repairs. Recent running metadata alone never proves liveness.
Actual wall-clock reversal is rejected. Hashes establish integrity, not authorship.

## Predeclared acceptance

Reference work12/max_ticks32, and work20/max_ticks7 quota. Force actual subprocess
exit at four tick boundaries: pre_commit77 (computed next state not journaled),
post_journal78, post_pending79 and post_checkpoint80. Test tick5 for all four,
and repeated faults at ticks5/6/7 on one continuing identity. Explicit resumes
must reproduce the uninterrupted canonical tick0..endpoint state sequence
byte-for-byte, with no missing/double work, no replacement identity and all
original committed journal bytes retained as a prefix. Wall times, epochs,
status-only frames and journal hashes legitimately differ and are not claimed
byte-identical. Include pause/resume and quota/empty-work idempotent completion.

Reject coherently rehashed skipped/doubled/fabricated timer, energy, epoch,
terminal and identity histories; corrupted/missing genesis, partial tail,
checkpoint ahead/wrong/corrupt, configuration/source/Python mismatch; prove
rejected resumes leave all bytes unchanged. Real competing resume process while
another holds the lock must exit2 without mutation. Observer must be read-only.
Missing/lagging checkpoint recovery is allowed only after full prefix audit.
Preserve source ZIP, fault exits, pre-resume snapshots, logs, authoritative states,
audits, test results and failures; exact replay plus same-D archive restoration.
Use existing manual lab lock,5GB floor and external300-second process timeout.

This establishes bounded process-exit recovery of an authored counter only.
It does not establish physical power-loss, drive-failure/off-D restoration,
population/PRNG continuity, OS isolation, self-maintenance, evolution or learning.
Those gates remain open, with separate authorization before unattended activation.
