# INHERITANCE-03 operational recovery, before continuation

Initial pinned attempt e1152b2dc845a251738ee6cf5032bff4cdf2758a stopped
at primary seed24624. Fixtures and24 batches completed. Batch24 exited0,
without timeout/truncation, but active_before_close=1 violated the harness.
All original stdout, process records, failure and self-accounted quota remain
immutable in D:/OraLab/runs/digital-inheritance03-20261011. This is an incomplete
execution, not a scientific negative or a passed process cleanup check.

The launcher took that accounting field before closing its kill-on-close Job.
The harness had incorrectly used it as a post-closure gate. A focused launcher
change reads owned process identities before close and independently checks
signaled/absent OS processes afterward. A successful continuation must have the
new explicit post_close_processes_exited proof. Pre-close count remains recorded.
No caps, VM law, seeds, metrics, gate or reserve condition change.

Continuation uses a separate evidence root and exact reviewed source. Preserve
all initial outcomes; complete the SAME frozen primary panel, rather than choose
new samples. Reexecute all batches identically, comparing the completed initial
24 decoded raw batches byte for byte and the preserved batch24 stdout decoded
result byte for byte. No result-dependent replacement. Reserved panel still only
after the original scientific primary gate passes. Native failed attempt remains
failed. No historical result is amended.
