# LAUNCH-01 — actual confined launch, advance, expiry, stop and resume

Prospective finite engineering composition. Frozen scientific laws and histories
unchanged. Existing TELEMETRY-01 tests use an in-writer hook; this panel has a
separate observer/launcher and a real capability-confined child. No service, UI
publication, controller, persistent pilot or unattended world.

Two fixed trial blocks, each with a32-tick uninterrupted finite template-world
reference, a confined resource-interrupted world and its confined continuation.
Engineering seed1/work2 only. All world physics files unchanged. Each real launch
gets a fresh AppContainer SID, zero capabilities, new PID/native creation FILETIME,
suspended-token validation before execution and explicit bounded Job Object.
Each profile is deleted after its launch. The resource world resumes the same
identity/history rather than creating a replacement world under its second SID.

The parent creates the fixed world/run identity from the reviewed law/config,
obtains the native birth time from the suspended child's PID, validates the expected
capability SID and zero capabilities, writes its explicit launch binding before
resume, and later confirms the live PID has that birth time. Binding files are
operator-owned external evidence, not claimed authenticated against a hostile host.
Hardened launch storage is a separate parent-only folder outside the writable
workspace. Before simulation starts, every child attempts to overwrite its own
binding; this must produce native PermissionError/winerror5 and leave the parent
record byte-identical. No live consumer may promote a child-writable binding.

Scheduling-only child wrapper holds at committed ticks1,2,5 while the parent reads;
the continuation holds at ticks5,6,7 so its new launch must prove fresh advancement.
Hold/release records lie outside the authoritative world. Each hold is bounded;
it does not change the physical state, random draws or simulation law. At tick1,
the first sample must await advancement. At tick2, a fresh sample versus tick1
must be active and prefix-consistent; repeated same-tick sampling cannot be active.
While the child is alive at tick2, an actual wall-clock hold longer than5 seconds
must become stale/inactive. Release then allows tick5 to become active again.
Wrong birth FILETIME (PID reuse control), wrong world/run identity and forged
previous frame must refuse live status. Recorded observation never probes a PID.
Read-only samples must leave every authoritative byte unchanged during stable holds.

At tick5, the resource-interrupted child requests256MiB under128MiB aggregate
allowance; allocation must refuse/terminate, with process exit and actual cap
evidence preserved. A caught MemoryError is recorded and exits86; unexpected
allocation success fails the panel. No memory-peak bound is inferred. The stopped process must
report inactive despite the last running heartbeat. Resume in the SAME folder
under a different launch birth/SID must restore exact identity, ancestry, resources,
all33 simulation states/32 events, full PRNG/noise cursor and original raw prefix.
Final child termination must produce stopped/inactive observation. Reference child
instead reaches tick32 cleanly. Six native launches total; each launch/observation
and every failure retained. No retrying a failed outcome into success.

Full reviewed runtime/module origins and hashes recorded; grants affect only fresh
D: fixture folders. Keep approved observer and its owner's publication pause intact.
No loopback/public networking introduced. Child128MiB/5CPU seconds/one process/
30wall seconds; parent512MiB/90CPU seconds/four processes/300wall seconds;
panel deadline280 seconds,256MiB disk ceiling,5GB minimum free space and exclusive
operator lock. Source contract/implementation committed before native execution.
Independent replay/telemetry interpretation, full-byte no-mutation and semantic
forgery controls, archive restoration and independent C: readback required.

Success means all specified launch/advance/expiry/refusal/stop/resume cases pass,
with exact raw authoritative evidence. A query failure or changed world during
sampling must stay unknown/inactive. OS liveness alone is insufficient. No scientific
progress, power-loss durability or production isolation certification follows.

## Pilot gates that this test cannot close

Cold application restore from independent C: has passed; full-host recovery has
not. Establish a separate disposable-machine rehearsal before claiming it. Physical
power-loss/storage durability also remains untested; software faults are not a
replacement. An initial supervised-pilot contract must state an acceptable lost-work
budget and checkpoint cadence explicitly, then measure them under actual storage
faults. No zero-loss guarantee is claimed from flush or ordinary process exits.

Review production filesystem/network permissions, allowed runtime imports and
escape scope separately; disposable zero-capability probes are not a hostile-escape
proof. Operator-owned birth binding is trusted only within that launcher/host scope.
Any live viewer needs read-only consumption, expiry and local access review. Existing
recordings remain recorded. A finite supervised pilot still needs a separate contract
and explicit activation authorization after the outstanding gates are satisfied.
