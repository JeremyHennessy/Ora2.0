# CADENCE-01 verified application-level recovery policy

Frozen source **cfd405bef30547e4306bdf1575b50959304d1638**;
[contract](CADENCE-01-CONTRACT.md), [decision](../data/cadence01/decision.json),
[complete archive audit](../data/cadence01/archive-audit.json).

Nine stopped-world backups (six four-transition batches, three eight-transition
batches) were written to physical disk C0 and read back on D1. Each successful
source-isolated independent replay preceded its actual acknowledgement. The
chosen proposed recovery budget is **zero lost acknowledged transitions**.
Backups name world/run identity, tick, exact source revision and archive checksum.

After acknowledgement24, the fixtures actually reached27 and31 without another
acknowledgement. Fresh-process restores from the C: tick24 archives lost zero
acknowledged transitions, discarding respectively three and seven unacknowledged
transitions. Original and restored worlds match all33 complete states through32,
including world identity, PRNG state/cursor, resources, history and ancestry.
Restored raw journal prefixes remain intact. Replay does not undo external effects.

Backup/compression/flush/fresh readback/replay timings were0.328–0.407 seconds
for four-transition batches and0.328–0.360 seconds for eight-transition batches.
Worker timings (including interpreter/launch) were0.546–0.687 and0.859–1.000
seconds respectively. This small engineering fixture supports proposing eight
transitions between acknowledged backups, at most seven unacknowledged transitions
between them. It establishes no wall-time loss bound, larger-world throughput,
live backup cadence or statistical timing guarantee. Every local simulation tick
already writes a checkpoint; backup cadence is a separate policy.

Independent full-state and rollback interpreters passed; a truncated archive was
refused, and a forged zero-unacknowledged-loss receipt was rejected. A separate
796-file complete C: archive readback rechecked all sealed hashes and reran both
world comparisons and the policy review from restored source. Archive SHA256:
`efdcceb8d66370ff5052c1ac64531f2b4a2913260a42bd838b45884f20ea75c3`.
Prewrite storage accounting:21,267,822 logical bytes /84,329,364 reserved bytes,
within228MiB; no claimed measured memory peak. Previous C: archives and shared
Ora files were checked unchanged. Every experiment child exited with its expected
status; rejected controls exited2 and1 respectively. No world remains active.

Read-only device inspection reports both drives healthy/online (C NVMe, D SATA,
GPT). The first sandboxed health query lacked CIM access; the approved read-only
retry succeeded. Device health, fsync and readback do **not** verify nonvolatile
controller-cache guarantees or abrupt power-loss durability. No power interruption,
full-host restore, new security identity, device-policy change or pilot activation.

## Remaining engineering acceptance

1. Establish physical durability with an approved controlled abrupt-power-loss
   test on disposable evidence, or independently verified storage/flush guarantees;
   retain pre-fault acknowledgements and prove recoverable identity/state afterwards.
2. Rehearse full-host restoration independently of the current OS/application
   installation, with pinned environment/source and complete world history.
3. Review production filesystem/network/import confinement and validate trusted
   launcher identity, advancing telemetry and expiry in the eventual configuration.
4. Bind the chosen zero-acknowledged-loss policy to a finite supervised pilot
   contract, including wall-time stopping/checkpoint rules. Activation needs its
   separate authorization. This receipt does not approve a pilot.

This is engineering progress only. Stage3 self-maintenance, organization-specific
useful-work advantage, functional inheritance and learning remain unproved.
