# LOST-WORK-01: acknowledged history versus recoverable history

Prospective bounded engineering test, October 10, 2026. Preserve the existing
world law and all scientific endpoints. This is an application-level recovery
measurement, not a power-loss test or persistent-pilot authorization.

The previous cold restore compared a tick7 backup against a tick32 reference.
That comparison alone cannot establish 25 lost acknowledged ticks: a reference
trajectory is not evidence that the original world actually reached tick32.

Use only the existing seed1/work96/max32 engineering fixture. Start one finite
world, pause at tick7 and preserve its complete backup. Resume the SAME world to
tick13. A trusted parent acknowledges tick13 only after successful child exit
and independent validation of the entire journal; preserve that observed prefix
as the acknowledgement evidence. Preserve a second backup at tick13. Continue
the original world to tick32 as the deterministic reference, without changing
the previously issued acknowledgement. No external outputs or actuation.

Restore each backup to a fresh D: directory under a new child process. Before
resume independently validate its complete prefix and identity. Compare against
the actually acknowledged prefix, not the later reference. Expect respectively
6 and 0 missing acknowledged transitions. Preserve the restored entry files;
resume to tick32 and require all33 complete states to equal the original run,
including RNG, noise cursor, ancestry, resources and world identity. Original
backup journal bytes must remain an exact prefix after resume.

Producer and separate read-only auditor calculate loss independently. Refuse
forged acknowledgement tick32 against the tick13 observed prefix, forged zero
loss for the stale backup, and a different-world backup. The auditor does not
import the loss calculator; both use the accepted independent world interpreter.
Run relevant recovery regressions. Freeze source before real execution. Apply
operator locking, 300-second/CPU, 512MiB allocation/four-process bounds, D: temp,
5GiB free-space floor and 128MiB finite evidence limit, checked between launches.
The disk check is a trusted-panel limit, not a hostile-writer OS quota. Bound
individual world journals by the existing 32-tick fixture and reader limits.

Report rollback transitions separately from deterministic recomputation. Exact
recomputation does not undo already observed external effects. Do not translate
ticks into seconds without measured cadence. Acknowledgement here means parent
validated application state, not independently proven physical durability.
This test defines no acceptable-loss policy: that policy, physical durability,
full-host restore, production isolation review and separate pilot approval remain.
