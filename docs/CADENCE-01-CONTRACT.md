# CADENCE-01: bounded backup acknowledgement and recovery policy

Registered October 10, 2026, before execution. Engineering fixture only;
not a natural-world experiment, physical durability test or pilot activation.

## Proposed supervised-pilot loss budget

Zero lost **acknowledged** simulation transitions. An acknowledgement may be
issued only after the stopped writer's complete journal, manifest, checkpoint
and history have been copied to the approved independent physical drive C:,
flushed, read back through a fresh process and independently replayed. A local
checkpoint or successful OS write is insufficient for this acknowledgement.
The acknowledgement names the exact archive SHA256, world/run identity, source
revision and tick. External actuation remains forbidden; recomputation cannot
undo external effects. This is a chosen proposed policy, not pilot approval.

Compare fixed backup batches of four and eight transitions. Use the existing
HEARTBEAT-03 engineering fixture, seed1, work96, horizon32, unchanged dynamics.
Stop/backup/readback/audit/ack at each batch boundary through tick24. Measure
worker time and backup-through-audit time separately using a monotonic clock.
No throughput target, automatic cadence tuning or realtime guarantee. Timing
includes cold interpreter/launch and independent replay overhead, and is not
an estimate of a future continuously running world's tick rate.

After acknowledgement24, execute one incomplete batch: to tick27 for cadence4
and tick31 for cadence8. Save these as observed, explicitly unacknowledged work.
Use only the acknowledged C: archive to restore into a fresh D: directory and
new child process. Expected acknowledged loss is zero; unacknowledged loss is
three and seven transitions. Continue both original and restored worlds to32;
all33 complete simulation states, RNG cursor/state, ancestry and identity must
agree. Preserve the restored raw journal prefix. New process is not a new
security identity, new OS, full-host recovery or physical power failure.

## Controls and falsifiers

Independent source-isolated full-state interpreter checks every backup before
acknowledgement, both terminal worlds and replay equivalence. Existing separate
LOST-WORK-01 calculator/auditor must agree on zero acknowledged loss. A truncated
backup copy must fail ZIP validation before use; a falsely claimed zero
unacknowledged loss must fail the independent cadence receipt review. Do not
modify a successful or failed run, change batch sizes after seeing timing, or
infer physical persistence from fsync/readback. Any error stops the panel and
retains the failure and source evidence. Old backup files must remain unchanged.

## Bounds and acceptance

One operator lock; sequential writers. Exact reviewed source committed and
archived before execution. Existing Python3.12; no fetched-code execution.
Each child has512MiB allocation cap,300CPU seconds, four processes, and the
remaining portion of a300-second total panel wall limit. These are enforced
limits, not measured memory peaks. Precharge persistent D: paths before writes:
raw128MiB/archive32MiB/restore64MiB/failure4MiB, total228MiB;5GiB free floor.
Only a new C:/ora/cadence01-20261010 directory, at most32MiB, on C0 distinct
from D1; no overwrites. Per-backup archives are flushed; original bytes and
checksums retained. All restores/temp/source/raw evidence remain on D:.

Accept the application-level procedure only if every actual acknowledgement
is backed by successful independent-drive readback/replay, both recovery losses
match registration, terminal full states agree, and all controls reject false
records. Report observed timing ranges without statistical/generalization claims.
The initially preferred proposed cadence is eight transitions, reducing backup
overhead while limiting unacknowledged work to seven between checkpoints; do
not adopt it if the panel fails. Wall-time loss remains unbounded by this test.

Physical durability, controller-cache behavior, abrupt power loss, full-host
restore, production filesystem/network isolation and trusted live telemetry
remain separate gates. No reboot, power interruption, device policy change,
unattended operation or pilot is authorized by this contract.
