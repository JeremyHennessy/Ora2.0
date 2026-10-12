# Streaming evidence audit repair receipt

October12,2026. [Prospective protocol](STREAMING-EVIDENCE-47-PROTOCOL.md),
[independent software result](../data/streaming-evidence47-results.json).
Source `54b1efd5f58be5fc49af145ec808d948dbc46ba0`. The evidence auditor previously allocated a whole file to
compute SHA256. That allocation was incompatible with a finite-memory audit of
permitted large archives. It now reads at most1MiB per hashing read; digest bytes,
ledger accounting, schema, hardlink/reparse guards and reservation checks remain
unchanged. This is an engineering integrity repair, not a World law change.

The old implementation fails the deliberately bounded-read regression with the
expected whole-file-read assertion. The corrected13 focused regressions pass
both from pinned source and its restored copy. Empty and partially used
reservations retain accounting; same-size changed bytes change the digest.
The small ordinary filesystem fixture has byte-identical original/restored
results. Five capped calls comprise one expected old-code failure and four
native-zero exits;64MiB prewrite evidence and8MiB sequential temporary fixture
caps were frozen. No large original history archive was queried to test this fix.

The first attempt is preserved as a failure: the three new tests passed but an
existing actual hardlink guard test received Windows access denied. A fresh
registered second root reran the same source, tests and limits with host file
permissions, without masking that test or changing acceptance criteria.

Zero World execution, closed-history query, organism actions/resources/births/
deaths, new ancestry, policy insertion, reserve opening or scientific stage
credit. History44 zero qualification and all closed laws/results remain intact.
Observer stays paused and private observer work remains protected. Native
isolation, off-host/full-host restore and production confinement remain unverified.
Next single dependency: Review and pin the finite whole6408 closed History44 trace diagnostic, including original raw seals and bounded parent/child memory, before querying those histories; keep all samples, references, controls, deaths, failures and ancestry.
