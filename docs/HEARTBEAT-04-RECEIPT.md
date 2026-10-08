# HEARTBEAT-04 — bounded template-world work provenance survives process exits

2026-10-08. [Contract](HEARTBEAT-04-CONTRACT.md) precommit
`9852081d0565506bec8ebc5e00cc229f92e2e63d`; implemented/executed
`3bc1ca652c2dd31ec46a13061604ff56d2ecc6fb`, existing Windows Python 3.12.10.
No contract/configuration/source changes after freezing. Existing development
seed 1 only: zero new independent scientific initializations. This adapts the
bounded recovery mechanism to the TEMPLATE-02 schema; it does not turn its
[negative science outcome](TEMPLATE-02-RECEIPT.md) into self-maintenance.

## Verified behavior

Complete serialized state includes 96 unique atom identities and external roots,
ready/nutrient/waste stocks and reclamation provenance, live objects, immutable
birth/parent/producer history, each current work token's identity/capture actor,
private/global ownership, heat/bonds, full Python PRNG state, noise cursor,
simulation tick and event chain. Status/resume frames consume no noise or work.
The original world identity and total horizon survive interruption; no replacement
world, extra tick or truncated history is created.

Manual acceptance reference: work 2 per initial monomer, total 32 ticks. Seven
actual subprocess exits: four single failures at tick 5/pre-commit **77**,
post-journal **78**, post-pending **79**, post-checkpoint **80**; a continuing
history interrupted at 5/77, 6/78 and 7/79. Every committed prefix was retained.
**Ten complete canonical state sequences** matched uninterrupted execution:
exact replay, four single faults, triple fault, pause/resume, missing checkpoint,
lagged checkpoint and post-lock recovery. Wall times/status-frame counts differ;
they are not part of the canonical simulated state.

Reference ended at tick/noise cursor 32 with all 96 atoms, 41 historic objects,
18 live objects, usable work 27 and heat 29. The 128-tick regression fixture
matched the original TEMPLATE-02 development stream's every event and terminal
world. Starved work 0/8 retained all eight neutral draws without creating work.
Pending snapshots were ignored; missing/lagged checkpoints rebuilt from the
independently audited committed prefix. Terminal resume was byte-idempotent.

The auditor imports no HEARTBEAT-04 worker and uses the separate neutral-law
interpreter to regenerate genesis, requests, costs, objects and work provenance.
Read-only observers verified history and reported checkpoint status/age; process
health remains unverified. Source/configuration mismatch, partial journal tail,
corrupt snapshot, coherently rehashed PRNG/work-actor forgery and real competing
resume exited **2** without modifying rejected evidence. Regression also rejects
rehashed noise cursor, draws, ancestry, token ownership and lifecycle changes.

## Verification, preservation and limits

**260 Windows tests passed**, exit 0, 228.245 seconds. Eight focused methods
passed in 57.329 seconds. No unexpected engineering development/acceptance
failures; all forced faults, rejections and negative cases are preserved. Manual
operator lock, 5GB free-space floor and 300-second subprocess timeout applied.
The separate diagnostic archive was deferred after its initial lock refusal;
the owning acceptance completed normally and no lock was removed/bypassed.

Run: `D:\OraLab\runs\heartbeat04-template-20261008T215848Z-3bc1ca65`.
Acceptance helper: `D:\OraLab\tools\verify_heartbeat_template.py`.
Source ZIP SHA256: `fb9169636332e6077407affc690856f1b144ce4e762d36d5ecab2d7f2dc3b634`.
Canonical terminal state SHA256:
`74b25e8e41d69ae4bf38cf0cb4fd4952fcd5910d5a7881127ccd836dcafc5485`.
Evidence archive SHA256:
`933498ac0aa53ebb06196826c1468208d7ff8c5199bd50503270175c766df81e`;
**197 files restored byte-for-byte on D:**. Source, exit codes, all journals,
interrupted prefixes, rejection inputs, read-only audits and complete canonical
state sequences are included. Evidence archives remain immutable; subsequent
GitHub integration receipts are saved separately.

This establishes bounded Windows process-exit continuity for the frozen schema.
It does not establish physical power-loss/storage-fault recovery, independent
off-drive backup, hardened runtime isolation, hostile-writer security or evolving
population continuity. The cooperative lock is not a security sandbox. Hosted
Linux CI is an additional regression gate, not Windows/power-loss validation.
No unattended/external service, self-hosted runner, automatic local update,
continuous operation, API or paid dependency was enabled. Original clones,
legacy code, old protocols/interfaces and frozen histories remain preserved.

Next engineering priority: supervised resource/isolation feasibility and the
independent backup/restore and storage-fault gates before any separately
authorized unattended operation. Keep actual population history and scientific
capabilities separate from reliable execution of this finite reference kernel.
