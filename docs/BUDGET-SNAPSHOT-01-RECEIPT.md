# BUDGET-SNAPSHOT-01 — self-accounting saved evidence ledger

This engineering repair changes no scientific laws, frozen experiment drivers,
historical receipts, observer UI or runtime activation policy.

## Defect and repair

Serializing `snapshot()` before its guarded write records the preceding
reservation. If JSON exceeds that reservation, the live writer correctly charges
growth before writing, but the saved ledger understates its own file. Seven
previous closure ledgers were preserved and separately reconciled without changing
their registered capacities. Those historical records are not rewritten here.

The additive `Budget.write_snapshot(phase, name)` creates an exclusive fresh path,
calculates JSON, precharges its extent, and recalculates until the complete ledger
fits its own reservation. Finite registered capacities bound growth. Quota refusal
happens before content writes; the empty file and any successful charges remain
available for failure investigation. Call it after all other evidence writes;
later writes require a new snapshot path. This is trusted single-writer accounting,
not an operating-system quota or a physical durability guarantee.

Frozen negative experiment drivers retain their exact serialization and hashes.
New laboratory writers should use this API rather than guessing metadata sizes.

## Verification and preserved failures

Pre-fix source `cebf5a4de` (resolve the full revision from the run contract) adds
regressions without the repair. A finite 400-file fixture reproduces a saved-ledger
audit failure while its live ledger passes. The first sandboxed run additionally
blocked the existing native hard-link test; the native rerun passes that check and
retains only the three expected missing-API errors, including two quota subcases.

Repair source `a11be82fe12d8ad1f842679962f1f4a6b162936b` passes 18 scoped runtime,
budget and launcher tests with one platform skip: 17 passes. The saved large ledger
round-trips through the separate filesystem auditor, refuses overwrite, and refuses
phase and combined quota excess before writing JSON.

A distinct child process importing only the separate auditor verifies 401 files,
69,791 logical bytes and a 69,391-byte self-accounting snapshot. Two deliberately
corrupted controls are rejected: a 65,536-byte self-reservation and an omitted raw
file. The first independent harness had an import-path error before creating its
fixture; audit-v2 fixes only the harness path and preserves the failed run.

All runs use pinned Git source archives, an exclusive operator lock, 5 GiB free-space
floor, 512 MiB process allocation limit, 90 CPU seconds, 16 process slots and
120 seconds wall time. Raw process exits, source, SHA-256 seals, archives and
restored copies remain under `D:/OraLab/runs/budget-snapshot01-*-20261010`.
The enclosing laboratory ledgers are independently checked from saved JSON.

No self-maintenance result is added. RECTIFY-01 remains rejected: zero qualifying
cases among 384; independent converters dominate post-damage usable work in all
381 cases funding every arm. AI-Research Pass 49 remains a separate interpretation
handoff, not a reproduced Ora capability. ADAPTATION-01 remains design-only.
