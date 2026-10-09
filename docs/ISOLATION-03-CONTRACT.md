# ISOLATION-03 — confined resource termination and exact recovery

Prospective bounded engineering contract, 2026-10-09. Freeze before execution.
No fresh science, service, approved-world migration or changed simulation law.

## Question and fixed matrix

Does the existing native AppContainer/Job gate compose with recovery when actual
CPU, committed-memory and wall-time pressure occurs at a durable world boundary?
Use unchanged HEARTBEAT-04 seed 1, work 2, horizon 32, and two trial blocks.
Each block has an ordinary and confined reference, then six confined fixtures:
CPU pressure/control, memory pressure/control, wall pressure/control. Pressure is
authored instrumentation, not organism behavior. Each stopped pressure world is
copied before a fresh confined process resumes it without pressure. Controls run
to completion without a second launch. Expected total: 22 launches, 16 histories,
six resource stops and six exact resumes. No selected scientific samples.

All processes use the existing unchanged gate: 128 MiB job committed memory,
5 CPU seconds, 10 seconds wall, one process slot confined (two ordinary).
Pressure is injected after the original writer durably writes tick-5 pending
checkpoint, before replacement. CPU request is seven process CPU seconds versus
0.05 in control; wall sleep twelve seconds versus 0.05; memory one 256 MiB
bytearray versus 32 MiB. No child process or new limits are installed. Memory
denial records MemoryError then exits 42; CPU/time are actually job/supervisor
terminated, not a manufactured successful exit. CPU expected native job-time
exit 1816 or supervisor 124; wall supervisor 124. If the actual exit differs,
preserve failure and investigate before any corrected execution. Require CPU
elapsed <10 seconds, wall >=10 and <12, memory denial before completion. Controls
must finish requested pressure and world with exit zero under the same caps.

## Acceptance and falsifiers

Kernel token SID, zero capabilities and configured job caps must be read before
thread resume. Every process must independently be stopped after gate closure.
Resource marker must show reached tick 5 and exact fixture request. Stopped worlds
must independently replay to tick 5 with checkpoint at tick 4 and pending/journal
at tick 5. Six fresh-process resumes retain raw durable journal prefixes and match
all 33 states and 32 events of the ordinary reference, including immutable identity,
resources, component provenance, ancestry, RNG and noise cursor. Both references
and all controls must match. Independent audit imports no gate, worker or driver;
rehashed state forgery must reject. Recorded observations are read-only and not
claims of OS liveness. Wrong limits, missing markers, completed pressure worlds,
divergent states, prefix loss, unfinished processes or failed cleanup falsify pass.

## Preservation and scope

Exact clean source revision, LF Git archive, outer operator lock, 5 GB free floor,
256 MiB panel disk ceiling, 280-second panel and 300-second parent ceilings.
Existing parent resource limits apply. Retain all process exits, ACL/native evidence,
raw worlds, tests, independent audits, failures, checksums and D: archive restoration.
Use fresh D: folders, copied existing Python and a unique disposable AppContainer
profile. Change ACL/integrity labels only on these new folders. Preserve existing
installation, global firewall, observer, histories and legacy source. Reviewed
integration, exact-head CI and new independently read-back C:/ora backup precede
completed handoff. Physical memory peak, hardware power loss, hostile escape,
complete filesystem/network isolation and unattended operation remain unverified.
Software storage faults and new-profile/permission restoration remain separate
next engineering gates. No autonomous origin, self-maintenance or evolution claim.
