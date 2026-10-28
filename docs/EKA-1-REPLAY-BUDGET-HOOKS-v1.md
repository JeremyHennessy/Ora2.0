# Mandatory replay reservation hooks: source only

Selection and derived reconstruction now require keyword-only `reservations`
and `genesis_index`. No default or fallback ledger is created. The future
exclusive owner must supply the canonical `Reservations` instance and allocate
distinct genesis indexes in each fixed dose slot. These calls do not issue
owner grants, assignment authority or native process permission.

Selection reserves one genesis and its entire assigned 4096-dispatch envelope
before `metadata_inputs()` can import replay dependencies. Derived
reconstruction first validates metadata, then reserves one genesis and its
entire prospective `stop_tick` envelope before `runtime_sources()`. The unchanged
Pressure71 `World.restore` creates one World and replays its original prefix
internally; charging only the visible suffix would miss that work. The full
envelope covers prefix, one paid READ and suffix. No credit returns after
extinction, bad input, failed comparison or later exception.

`Reservations.dispatches` writes a bounded block reservation, then synchronizes
it before returning. Mixed single/block calls share the same 4096 ceiling per
genesis. Whole-replay precharge avoids requiring a separate fsync for every
dispatch without raising the dispatch limit or dropping attempted credit.
Records describe reserved work, not proof that all those steps actually ran.
Actual event/closure/usage receipts remain independently necessary. Partial
write or synchronization failure still poisons the instance and retains bytes.

This is a source integration, not authenticated execution or native containment.
The constructor, original producer, other semantic fixtures and any references
must also be bound to the sole native owner and its shared budget. Process-birth
hooks, enclosing topology/deadline, physical file identity and original-owner
custody remain unqualified. Caller bypass/replaced ledgers and untrusted
interpreter/module state must be excluded by independently admitted executed-code
custody, not by a Python type check alone.

The biological law files and paid READ hook are unchanged. The selection and
reconstruction wrapper bytes changed, and the selection dependency hash was
updated. Old accepted source-gate/plan pins remain preserved historical data;
they no longer match these changed wrappers and cannot admit this head. Do not
run an old checker to relabel its old pass, silently refresh its pins or call
old CI a pass for the new head. Independent exact-source review, complete
prospective source/output/resource fit, safe whole-source CI and a separate
original-owner qualification registration must precede any replay. Population
and scientific admission remain separate and held.

Six new offline checks cover block bounds, single/block accumulation, burned
credit after later failure, failed-sync partial retention, mandatory wrapper
signature/order and the exact revised dependency hash. Replay modules were read
as AST only and never imported or called. Old test groups, World/VM/native
experiment roles and closed cohorts were not run. These checks cannot establish
semantic replay parity, native enforcement, full peak fit or useful learning.
