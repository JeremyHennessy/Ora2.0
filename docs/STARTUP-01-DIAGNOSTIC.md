# STARTUP-01 — initial auditor failure preserved

Protocol b390d7f; first implementation7c4fa55. Existing Windows Python3.12.10
ran27 tests. The18 prior ENERGY-02/REACTIVATE-01/CONTACT-01 regressions passed;
new valid-state audit checks raised66 subtest/errors before any full panel ran.
The independent auditor used Counter(atoms_dictionary), which interprets the
dictionary's metadata values as counts instead of counting immutable atom keys.
This rejected valid genesis material ownership. The actual atom identities were
not duplicated or lost by this failure; it was a measurement implementation bug.

Correct only that count construction to Counter(atoms_dictionary.keys()). Add a
direct adversarial ledger test for valid genesis, duplicated ownership and hidden
heat. Preserve initial source, test log, process exit1 and sealed/restored evidence.
The frozen law, prices, finite stocks, schedule,3024-case panel,133920 events,
controls, success criteria and reserved samples remain unchanged. No full-panel
negative or positive science result came from this failed acceptance attempt.

The corrected-source631c71a attempt ran28 tests:27 passed and one adversarial
configuration test failed. Its fixture mutated the same configuration dictionary
used as the expected independent value, so both sides changed to False. Fix the
fixture to copy the forged record before mutation, preserving the expected budget0.
Canonical auditor comparisons already distinguish False from0. Preserve this
second source/log/exit1/archive too; no full panel ran and no physics changed.
