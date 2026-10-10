# Finite runtime acceptance boundary — October 10, 2026

This evidence review separates application recovery from remaining pilot gates.
No new runtime or physical fault test is claimed in this review.

| Gate | Verified evidence | Remaining requirement |
| --- | --- | --- |
| Lost work | CADENCE-01 independent archive audit restores 33 states each; 3 and 7 unacknowledged transitions lost, zero acknowledged loss | Proposed pilot policy: zero acknowledged loss, eight-step backup interval, at most seven unacknowledged transitions. Operator acceptance remains part of pilot approval; wall-time loss is not bounded by these results |
| Cold application restore | RESTORE-01 audit: eight launches, two exact cold restorations and six rejections; 33 states and 32 events each; dependencies restored from independent drive under new launch identity | Fresh OS/full-host recovery independent of the current trusted parent and OS |
| Physical durability | Off-drive flush/readback and complete archived-file checks establish readable copies | Abrupt power-loss/controller-cache durability evidence and a reviewed physical test procedure; no device policy or power interruption authorized here |
| Confinement | Bounded resource/storage/recovery and native launch cases; bootstrap now avoids cache writes | Validate the eventual production filesystem/network/import boundary under its exact launch profile |
| Observation | Verified fixture advances, expiry/stopped status and corrupt-cache rejection; read-only source/fixture integrity | Bind any future process to trusted launch identity and advancing actual-state evidence; recorded playback must remain labelled |

Actual audit files reviewed: `D:/OraLab/runs/restore01-cold-20261009-v5/audit.json`
and `D:/OraLab/runs/cadence01-archive-audit-20261010/raw/proof.json`.
The latter records 796 restored files and source
`cfd405bef30547e4306bdf1575b50959304d1638`; both explicitly mark full-host
and physical power-loss recovery false. Existing scientific and engineering
receipts remain authoritative for their narrower scopes.

The proposed loss budget is concrete; application readback does not approve it
for a persistent pilot. Gather full-host and physical durability evidence before
requesting separate supervised pilot activation. No unattended operation,
observer redesign or publication is introduced.
