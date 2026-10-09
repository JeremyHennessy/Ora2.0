# STORAGE-02 — explicit write-error handling and bounded continuity

2026-10-09. Protocol87737abc2c6b67057d1a05ac981f0904014a259d;
diagnostic source d457ad2524ea2195fc5a69c84ec9fdb9774feacc;
accepted source7a137e146b5df1856775f59015aaea07b6d1331a, Windows Python3.12.10.
Exact reviewed LF source archive was executed under the existing operator lock,
5GB free-space floor, finite32-tick limits and300-second acceptance-command
timeouts; each panel's internal worker command has a30-second timeout.

## Problem and narrow repair

The preserved baseline acknowledged a half journal write with exit0; independent
semantic replay rejected the damaged journal with exit2. A half pending-file
write also went unreported, although later scratch writes overwrote it and the
final history was valid. See the [diagnostic](STORAGE-02-DIAGNOSTIC.md).
The shared writer now checks accepted byte counts for its initializer/JSON writes;
all three existing heartbeat journals use the same guard. Short/zero writes
propagate OSError. Physics, formats, finite bounds, recovery policy, old datasets,
source archives, reserved samples and approved observer are preserved.
Old source-bound worlds still require their original source archive; no migration
or historical regrading is implied.

## Completed acceptance

33 Windows tests passed in three serial bounded groups:2 new I/O tests,16 counter/
sequence-world regressions,15 template-world/snapshot regressions. Their elapsed
times were121.962s,113.152s and79.722s. These are separate command budgets, not a
claim that the whole milestone completed in300s. The earlier combined command
timed out after300s with28 completed tests and zero reported assertion failures;
that incomplete attempt is preserved, not counted as a passing suite.

Two fresh complete16-case panels exercised actual disposable file operations:
half/zero writes, write/flush/fsync errors, replacement failures and actual exits
81/82 during partial journal/pending writes. Both panels had83 recorded commands;
all matched their predeclared exits. Each independent audit verified:

| Outcome | Per panel | Both panels |
| --- | ---: | ---: |
| Direct complete-state continuations |13|26|
| Partial-journal rejections with unchanged inputs |3|6|
| Trusted tick3 snapshot continuations |16|32|
| Read-only recorded observer checks |16|32|

Every one of the29 continuing histories per panel matched all33 independently
replayed reference states, including identity, PRNG/noise cursor, atoms, object
ancestry, component/work provenance and the original journal prefix. Zero journal
writes leave tick4; other complete-journal failures leave tick5. Pending files
never supply authority. No partial tail is truncated or repaired in place.
The verifier imports no worker, injector or panel generator; it separately
reconstructs interrupted bytes and checks the exact ordered case/command ledger.
Normalized audits agree byte for byte. Timestamped journals from fresh invocations
are not claimed byte-identical. Canonical state-sequence SHA256:
96c3fd83045e28b7695d5146c7d49443bdbf7b23a6a53b2e03a3c4053f63ee4c.
A false successful-resume claim is independently rejected (exit2); tests also
reject missing cases, false source hashes and false observer claims.

118 historical/shared inputs remained unchanged.1,180 sealed evidence files
restored byte for byte on the laboratory drive. The earlier short-write baseline
and the incomplete300-second attempt have their own preserved source/log archives.
Exact source ZIP SHA256:
1142948b9088f484047a03f4806def4a5be9dd8549b516c727b746ffd35d0cdb.
Public repository changes contain the contract, code, tests and this receipt;
private evidence, integration and independent-drive readback records remain in
the laboratory. Existing BACKUP-01 separately established physical-drive backup.

## Limits and next priorities

This passes the registered user-space I/O fault/recovery gate. Successful readback
after an injected fsync error uses the same running OS/cache; it does not prove
that unsynchronized bytes survive power loss. Flush exceptions close the Python
file, which can flush buffered bytes. Device errors, kernel crash consistency,
directory synchronization, physical power-loss recovery, whole-host reconstruction
without the laboratory drive and hardened filesystem/network/process isolation
remain unverified. No hard memory-peak bound or unattended world is established.

Science remains STARTUP-01's conditional paid feasibility, with supplied encounter
order/channels/target length. Next precommit a separate unscreened finite substrate/
opportunity study that removes those assists; preserve all failures and nulls.
Do not install this assay's reactions into the world or reinterpret engine-installed
function as autonomous origin, inheritance, self-maintenance, adaptation or life.
Engineering next needs separately scoped isolation and physical durability gates
before a separately authorized persistent pilot. No observer publication, service,
unattended continuous simulation, API or infrastructure activation occurred.
