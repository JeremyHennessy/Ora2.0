# STORAGE-02 — preserved baseline short-write failure

Protocol87737ab, reviewed diagnostic source d457ad2524ea2195fc5a69c84ec9fdb9774feacc.
Before repairs, two actual disposable worker processes were injected at the
advancing tick5 write. Both returned exit0 despite reporting only half the bytes
accepted by the targeted write. The journal case was rejected by the independent
HEARTBEAT-04 semantic inspector (exit2); its malformed tail was not repaired.
The pending case later overwrote its partial scratch file and had a valid final
journal (inspection exit0). Its initial write error was nevertheless unreported.
All21 archived files were restored exactly on the same laboratory drive. Evidence
archive SHA256:625bbc82bc9f85f0f2b4ef25b94e975ad8204d4f1b90f1aa64d457cd3c62c1db.

This is controlled user-space failure injection, not observed physical disk
failure. The narrow prospective repair checks every authoritative write count
before acknowledging that operation: lock initializer, JSON files and the three
existing heartbeat journals. It propagates OSError on partial/zero/malformed
write counts. It does not retry, truncate tails, change serialization/physics,
reclassify old evidence, alter restoration policy or start a replacement world.

Because source hashes bind runtime identity, old worlds retain their original
source archive for resumption; this is not permission to migrate old identities
to the repaired source. Complete old experiment datasets/protocols remain intact.
