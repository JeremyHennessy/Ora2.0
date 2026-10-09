# TRACE-01 — preserved disk-limit scope discrepancy

Post-execution packaging review,2026-10-09. Frozen contract844915e3 names a
16MiB evidence ceiling. Frozen implementationca6b24aa checks only the24 raw
component files; the private launcher did not enforce this limit over source,
replay and semantic-forgery evidence together. The contract did not explicitly
exclude those files. This is an operational scope discrepancy, not permission
to reinterpret the original ceiling after execution.

Raw panel including manifest:6,151,975 bytes. Total original run, excluding
its separate restored copy:21,727,475 bytes (includes43826-byte seal and186-byte
archive-proof file added during packaging). Preserved sealed payload before
these two files:21,683,463 bytes. Both exceed16MiB. The full preserved restored
copy is21,727,289 bytes. No data removed or compressed retrospectively to claim
the original limit passed. Fixed schedules, source identity, prices, outputs,
provenance, five checks, independent interpretation and byte replay remain valid;
the run did NOT demonstrate a16MiB bound over complete evidence.

The finite24-slot/3,904-request panel completed without a disk-full event, retained
its prechecked5GB free-space floor and process caps, and preserved333 shared and
232 prior backup files. This does not repair the missing aggregate quota check.
The component gate is accounting feasibility preparation with this operational
limitation, not a fully passed end-to-end laboratory storage-limit test.

Before any future behavioral or component execution, prospectively specify and
enforce separate finite ceilings for the complete raw/source/replay/failure ledger,
archives, and disposable restored copies, plus a combined laboratory staging cap.
Check writes before exceeding the relevant cap, including failure-preservation
allowances; reserve space rather than deleting failed evidence. No new fixture,
controller, physical-law tuning or behavioral sample is authorized by this erratum.
