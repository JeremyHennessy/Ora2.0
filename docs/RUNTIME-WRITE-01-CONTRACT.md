# RUNTIME-WRITE-01 — authoritative short-write refusal

October10 engineering-only finite AL01-CAL fixture. No scientific law,
historical run, observer UI, controller or persistent operation changes.

Review finds checkpoint_pilot.atomic_json and record_step ignore the return
count from authoritative writes. Reproduce a backend that writes a prefix
without raising, then reports that short count. Atomic checkpoint replacement
must raise before promotion and preserve the previous checkpoint. Journal append
must raise before returning a new chain head, leave the last checkpoint intact,
and preserve the partial journal for manual review. Do not silently repair or
discard that failed tail. The newer heartbeat runner already checks exact writes;
keep its approved behavior unchanged.

First commit the contract and regression fixtures; run on that pinned pre-fix
source and retain the two expected failing assertions. Freeze a minimal repair
before repeating those fixtures. Successful checkpoint/append behavior, existing
abrupt-process recovery and deterministic reactor/PRNG replay must still pass.
Fault injection is engineering evidence, not an observed storage-device failure.
Source identity changes deliberately: old archived worlds must remain bound to
their historical runner revision, not be relabelled as the corrected runner.

Exclusive lab lock; D: temporary files and records;5GiB floor;512MiB allocation,
30CPU/30wall seconds,16 process slots per child. Each run raw16MiB,
archive16MiB,restore16MiB,failure1MiB,total49MiB. Precharge storage with the
reviewed Budget and independently audit the final self-accounting saved ledger.
Preserve process exits, source seals, injected failure evidence, archive and
restore checks. Publish reviewed diff only after exact-head CI and remote recheck.
Physical durability, full-host restore and production isolation remain open.
