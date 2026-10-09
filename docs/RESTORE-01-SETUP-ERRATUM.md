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

### Prospective identifier correction after the controlled diagnostic

Two independent disposable calls for each prefix crossed four/eight aggregate
process slots. The established `OraLab.Integrated.` prefix plus a fresh UUID
(50 characters) created successfully under both budgets. `OraLab.ColdRestore.`
plus a fresh UUID (51 characters) returned E_INVALIDARG under both budgets.
Every diagnostic profile deletion returned zero; no world ran. This isolates a
label-dependent refusal in those calls, not a general documented 50-character
Windows limit or proof of its underlying cause. The earlier prose character
counts were off by one; measured lengths are authoritative.

Use the established accepted prefix with new unscreened UUIDs. Every new SID must
still differ from every original archived SID. No budget, capability, world law,
endpoint or control changes. Preserve all prior failures. Two private diagnostic
packaging failures (missing helper import; duplicate reporting keyword) are also
retained separately and do not constitute world execution.
### Host launcher diagnosis supersedes the identifier correction

The tool sandbox parent was itself AppContainer (two capabilities); the ordinary
host parent was not (zero capabilities). The same prospective 2x2 diagnostic
under the ordinary host created all four labels successfully, including both
51-character labels, under unchanged four/eight process caps. All were deleted.
Thus the sandbox label comparison does not justify changing the host identifier.
Restore the original prefix; record and require the ordinary-host token before
creating profiles. No elevation of child privilege or relaxation of confinement.

The v4 sandbox panel produced eight refused launch attempts (WinError87), zero
world execution, two cleaned nested profiles, and an independent audit rejection.
Earlier profile refusals and the private packaging failures remain preserved.
Run subsequent native acceptance from the existing ordinary host launcher, as the
previous verified native laboratory panels did. This is an orchestration context
correction; no scientific law, world state, resources or child caps change.
