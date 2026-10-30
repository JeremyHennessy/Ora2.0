# Cumulative reservations: source only

The preparation plan at parent `48dee3ee6dc6b8ecb1c98bc690ebb806475a7321`
permits at most 14 logical roles, 56 process births, 32 geneses per dose
(dose 1 and dose 8), and 4096 dispatches per genesis. An active-process Job
limit cannot establish those cumulative totals.

`tools/eka1_cumulative_reservations.py` provides one fresh, non-resumable
reservation ledger for a future exclusive owner. Reserve each role, attempted
process birth, genesis and dispatch before the corresponding effect. A later
failure never refunds a reservation. Duplicate roles and genesis identifiers
are refused. Every record carries a sequence and previous-record SHA256;
each write is synchronized before its reservation returns. A short write,
synchronization failure or changed file extent/offset poisons the instance.
Partial bytes remain, and a new instance refuses the nonempty file. Closing
does not declare native termination, EOF, complete evidence or archive success.

These are reservations, not authenticated observations. The caller must own
the physical file and exclude competing writes, retain all failure artifacts,
and authenticate the real events independently. Hash chaining alone proves
neither durability against host loss nor original execution. The component
does not open a process, import a World, issue a grant or authorize replay.
It cannot prevent a caller from bypassing it or creating a different ledger.
The future native owner must enforce one manifest/ledger identity and debit
before every effect; that integration is absent and unqualified.

The additional ledger must be explicitly precharged *inside* existing output
allowances. Its internal 80 MiB refusal ceiling is not a new storage allowance.
At most 262278 permitted records, each at most 256 bytes, require at most
67143168 bytes before physical allocation/header costs. No actual allocation
or full-run measurement occurred. Per-dispatch synchronization may be too
expensive under the existing CPU/wall limits: performance, combined memory,
output, archive and exact restore fit remain unqualified. Do not increase caps
or silently replace complete records with a truncated accepted ledger.

Eight new synthetic checks cover fixed strata and ceilings, failed attempts,
duplicate identifiers, exact integer types, short writes, synchronization
failure, chain continuity and external extent change. They execute only this
stdlib component against temporary files, with no VM/native experiment or
old tests. The first attempt failed in test setup on sandbox temporary-folder
permissions; its definition and failure summary are retained outside the
source tree. Only the new group ran after using the authorized workspace for
temporary files. No independent review, exact-source CI or native
qualification is claimed.

Next: review and integrate this ledger with the existing sole native owner,
including enclosing deadline, real process-birth and genesis/dispatch hooks,
physical file custody and complete failure retention. Freeze the full
qualification manifest only after exact source/union/output costs fit.
Original-owner registration, safe exact-source CI and independent native and
scientific admission remain separate. All actual replay and population
execution remain held.
