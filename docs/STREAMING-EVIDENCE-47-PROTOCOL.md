# Bounded streaming evidence audit repair

October12,2026. Engineering dependency of [History46](DIGITAL-HISTORY-46-RECEIPT.md).
The existing auditor calls path.read_bytes() for every evidence file, including
archives. A permitted multi-gigabyte archive cannot be audited under the proposed
384MiB parent cap with that whole-file allocation. This is an engineering defect,
not a VM/law mismatch or a scientific failure. No original rows will be queried.

Change only hashing to streamed1MiB reads. Keep SHA256 bytes, return schema,
capacity/denominator/link checks, reservation accounting and all frozen evidence
unchanged. Historical exported source remains preserved. Three new regressions:
multi-block3MiB-plus-tail hashing with whole-file reads forbidden and read sizes
checked; empty/partially reserved file accounting; changed bytes produce a changed
digest without changed capacity. Run the10 existing evidence-budget regressions.

Prospective five native calls: former implementation against the new bounded-read
regression (one EXPECTED native-one), corrected13 focused tests and a small
deterministic filesystem hash fixture, then restored13 tests/fixture. Require the
baseline's specific whole-file-read failure, not any arbitrary failure. Four
native-zero exits and source/restored identical fixture bytes. No repeated full
Windows suite. All native outputs/errors/caps/seals/failures preserved.

Each5CPU/at most10wall/128MiB/three processes/1MiB output; global90wall/25CPU
launch ceiling, finite120wall parent. Existing Python/exclusive lock/fresh D:/OraLab
root.64MiB prewrite raw24/archive8/restore24/failure8MiB; plus bounded8MiB
sequential ephemeral fixture temp allowance in a fresh D:/OraLab/temp directory,
never system temp. Require allocation plus5GiB free. Stream archives/restoration
and final storage interpretation too. Pin exact source/runner/config before run.

Zero World/closed-history query/new organism actions/resources/births/deaths/
ancestry/source sampling or policy installation. All prior scientific negatives,
World laws/prices/programs/controls/horizons/results/reserves remain unchanged;
no learning/evolution/repair/stage credit. Observer paused, private ancestry/UI
and separate research ownership intact, schedules unchanged. Same-host custody
does not establish off-host/full-host recovery or production confinement.

Next single dependency: bounded parent-memory/process and original-input-seal
preflight for the complete closed History46 census before its trace execution.
