# Prospective metric canonical-key clarification - no primary retry

Read-only inspection of the two completed metric recordings confirmed a second
host custody mismatch before any new qualification: both contain eleven offspring
in at least one arm. The unchanged metric producer's post_expansion_served table
has integer child IDs. The canonical writer sorts integer keys numerically, but
the guarded receiver reads JSON string keys and sorts them lexically. Therefore
each old raw recording differs from canonical(parse(raw)); final guarded input
would correctly refuse it. No final role was attempted. Keep both originals,
their native/source/seal/hash provenance and the failed primary unchanged.

Normalize ONLY this small child-ID table to string keys in the host batch wrapper
before recording. Do not alter the qualified metric module, numeric values,
endpoints, World/source/prices/criteria or any old receipt. Add a scoped regression
with child IDs1,2,10,11 proving the old serialization mismatch and new guarded
canonical round-trip. The lifetime qualification's byte-equivalent comparison
is superseded ONLY for this disclosed serialization difference: require exact
parsed-value equality to both old successful metric recordings, publish both
raw and normalized hashes, and do not rewrite old bytes. No scientific rescoring.

Same two read-only qualification jobs/limits/input denominator; now run both new
regressions. Preserve all fifteen original histories/proofs and explicit old
source provenance. New third-prefix metrics remain a software derivation on
closed records, not a successful retry of the stopped primary role. No fresh
World, target/reserve, primary rerun or continuation is authorized by this note.
