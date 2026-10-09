# RESTORE-01 — prospective regression launcher clarification

2026-10-09, before any cold restoration panel executes. Preserve original contract
4d67e47a9f1cfab5242271ac8b690296eb236c75 and first attempt daea8a55225bff6897ae29f57ab19b9a106e5da6.

The first run reached 27 regression checks: three existing child-process tests
failed with exit 101 because the Windows virtual-environment redirector needed
another native process under the registered four-slot aggregate job. The cold
panel never ran; no restored child or AppContainer profile was created. Original
logs, exact source, exits and failed archive remain sealed on D: (326 restored files).

For the next attempt, invoke the SAME installed Python 3.12.10 core directly for
standard-library regression checks, using the existing environment's
sys._base_executable. This removes redirector overhead, without installing Python,
changing dependencies, raising the four-slot aggregate cap, changing test assertions
or altering application/world physics. The parent operator still runs from the
existing virtual environment. Panel/audit commands and restored independent-backup
child binding retain the registered source, four-slot parent job and unchanged
128 MiB / five CPU-second / ten wall-second / one-slot native child limits.

Freeze this execution clarification before rerunning. It changes only test
orchestration; preserve all failed evidence and report it alongside accepted results.
