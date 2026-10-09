# RESTORE-01 — next bounded setup attempt and relocatable audit evidence

2026-10-09, prospective before the next native panel. Second attempt at 73faa980
passed 25 Windows checks / two expected guards skipped, then failed the first
CreateAppContainerProfile call with HRESULT 80070057 before any world launch.
Its 454-file archive is retained. No successful new SID was returned. The exact
underlying Windows setup cause is not yet established; do not call this a world
continuity failure or claim that loosening security/resource limits solved it.

The selected name is within the documented 64-character pattern, and display /
description strings are within their limits; see [Microsoft's API contract](https://learn.microsoft.com/en-us/windows/win32/api/userenv/nf-userenv-createappcontainerprofile).
The capped parent used the virtual-environment redirector, consuming another
process slot. Next use the SAME installed core interpreter directly for all
standard-library orchestration commands, removing that overhead; retain four
aggregate slots and every native child cap. This is a discriminating setup attempt,
not an established diagnosis. If it still fails, preserve and investigate.

Record each attempted profile name and creation HRESULT before checking success.
Returned profile pointers and successful profiles still require exact cleanup.

Make independent acceptance relocatable: record the original new D: panel directory
for captured executable/module provenance, while reading restored runtime and world
bytes from the audit's current evidence folder. Never probe historical processes or
load an old laboratory installation during readback. All recorded module paths must
remain under that original new runtime; source/dependency hashes and exact replay
must validate the actual independent restored copy. This changes evidence plumbing,
not the frozen world source, state, physics, controls or success criteria.
