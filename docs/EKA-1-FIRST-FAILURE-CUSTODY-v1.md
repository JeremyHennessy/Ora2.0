# First failure and cleanup custody: source repair only

The accepted partial native candidate at `94e60da` remained unqualified for
actual launch. Static inspection found that `_fail` assigned `_failed` on every
call, so a later closed-owner refusal could replace the original cause. A
cleanup exception escaping `close()` could also replace the exception re-raised
by the caller. Nested cleanup could lose the first cleanup error when the second
operation failed too. These are source findings, not observed native failures.

The candidate now stores the first execution/refusal cause once. It attempts
ledger and owner-descriptor cleanup separately, records both cleanup causes in
order, and never retries either operation. A direct `close()` raises the first
cleanup exception after both attempts. `_fail()` retains that information and
returns so its caller can re-raise the original failure. When descriptor close
fails, the descriptor number remains available for custody; logical closed means
no further work, not proof of physical closure. No subsequent owner lifetime,
budget refund, ledger overwrite, archive closure or native success is inferred.

Five new offline state fixtures check primary-cause preservation, two simultaneous
cleanup errors, direct-close ordering, an fd cleanup attempt after ledger cleanup
fails, and a failed constructor before fd/ledger creation. They bypass construction
and mock close operations: no current-owner birth query, native process, World,
replay or old test group runs. They do not prove OS close behavior or containment.

Both replay wrappers bind the repaired candidate hash; selection also binds the
changed derived-wrapper hash. Biological law, paid READ source, counters, prices
and caps are unchanged. Old eleven-source manifests/reviews remain immutable and
do not admit these changed bytes. Complete new source closure, independent exact
repair review, safe exact-source CI and separate qualification registration remain
required. No scientific or native execution authority is added.

Next: independently review this narrow failure-custody repair, then continue
canonical-ledger/attempted-birth integration with the existing guardian only after
the enclosing topology, deadline, executed-code custody and complete resource/
output/archive/restore plan is reviewed under unchanged allowances.
