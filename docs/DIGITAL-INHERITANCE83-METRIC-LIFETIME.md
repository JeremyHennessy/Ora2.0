# Host metric lifetime and canonical-key repairs - read-only qualification

The stopped primary exposed two evidence-handling defects. Its zip iterator cached
the previous full history/proof while loading the next recording, violating the
intended one-history-at-a-time bound. Every retained single-history audit had fit
the same512MiB limit. Separately, integer child-ID keys in post_expansion_served
sorted numerically on write but lexically after JSON parsing; the two completed
metric recordings were therefore noncanonical for the guarded final receiver.
Final acceptance had not been attempted.

Only the host batch wrapper changes: explicit iterator/unpack/release before the
next read, and string keys for that small reporting table before serialization.
No World transition, organism programme, VM price, learned state, metric arithmetic,
threshold, role roster, target or old receipt changes. Old sourcef6df6a7 and its
failure remain immutable. This does not complete or retry its failed metric role.

Two new regressions reproduce the retained zip-pattern lifetime fault with weak
references and the child-ID1/2/10/11 canonical mismatch. Both exact original and
restored source exports then consume all fifteen retained histories/proofs through
the fixed shared helper. Every metric validates; both old completed metric
recordings have exactly identical parsed values. Their original byte hashes and
the new canonical hashes are reported separately. No original bytes are rewritten.

Two bounded read-only native calls, zero new Worlds or target queries. CPU
16.21875/16.078125 seconds and peaks389259264/391045120bytes stay below the same
512MiB/60CPU/90wall limits. Full source, lossless cached inputs, native outputs and
archive restore are verified at
30405b16af44e11bd7e4b01e40420fd41bc5071f38577c656d486d0bab64bc90.
See [the qualification receipt](DIGITAL-INHERITANCE83-METRIC-LIFETIME-EVIDENCE.json),
[prospective qualification](DIGITAL-INHERITANCE83-METRIC-LIFETIME-CONTRACT.md) and
[canonical clarification](DIGITAL-INHERITANCE83-METRIC-CANONICAL-ADDENDUM.md).

The original primary stays closed incomplete. No fresh context, reserve, primary
retry or remaining-role continuation is admitted by these software checks. No
capability/stage/selection credit follows from the repair.
