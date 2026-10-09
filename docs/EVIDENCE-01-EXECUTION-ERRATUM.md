# EVIDENCE-01 — prospective replay environment correction

The first copied-byte rehearsal560dd057 passed guarded writes, archive, restoration
and a filesystem audit before the historical replay. A final independent audit
then rejected it: the process-limit bootstrap regenerated Python bytecode inside
the restored historical source. These writes bypassed the guarded stream and
changed previously charged files. Preserve the first case and its earlier
provisional result; it did not pass the complete end-to-end gate. No original
TRACE-01 source or evidence was altered.

Added native hard-link check7b4a660 first failed link creation inside the tool
sandbox(Windows access-denied5), before testing the writer. Ordinary-host execution
passed all seven checks but again exposed the first case's bytecode discrepancy.
Both attempts and their actual exits remain preserved; neither is relabeled a
complete verified rehearsal.

Before a fresh copy-only rehearsal, set PYTHONDONTWRITEBYTECODE=1 for the entire
reviewed subprocess tree, including the process-limit bootstrap. Pin the exact
launcher environment and ensure it does not create other cache/temp artifacts
inside the managed case. Run the independent complete filesystem audit again
AFTER historical interpretation. Same writer/interpreter, prices, limits,
source/history and all original failed artifacts; no new science samples,
parameter tuning, refunded charges or favorable criterion changes.

This is a necessary wrapper correction, not OS enforcement. Arbitrary subprocess
writers still require a separately verified quota or guarded output integration.
