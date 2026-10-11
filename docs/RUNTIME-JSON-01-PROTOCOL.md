# RUNTIME-JSON-01: authoritative JSON ambiguity

Engineering regression only. No scientific law, fixture trajectory, historical
record, observer interface or activation policy changes.

Before the fix, freeze a test-only revision and execute the two scoped tests in
a fresh D: evidence directory. Eight corruption cases insert a conflicting
earlier occurrence of an existing key; the last occurrence and checksums remain
unchanged. Manifest, checkpoint, receipt and journal, including nested payloads,
must all reject duplicated names before trusting a digest or replay result.
The valid four-step AL01 fixture must remain independently replayable and every
authoritative byte must remain unchanged during rejected verification.

After reproducing the failure, change only the checkpoint runtime's JSON
decoder, freeze a second exact revision and rerun these tests plus existing
checkpoint and short-write regression tests. A separate pair-list parser must
confirm each saved corrupted file really contains duplicate names even though
ordinary last-value parsing accepts its envelope checksum. Archive and restore
the source and evidence, then rerun the scoped suite from restored bytes.

Every invocation uses the existing operator lock, native 512 MiB/20 CPU-second/
30 wall-second/four-process limit, 5 GiB free-space floor, 1 MiB captured-output
cap and 25 MiB total evidence allocation. Preserve expected failing exits as
results, not runner errors. All source is reviewed and pinned before execution.
This validates application rejection only; it does not establish physical
power-loss durability, independent-host recovery or production confinement.
