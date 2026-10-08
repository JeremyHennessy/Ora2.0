# Local runtime — bounded operation only

**2026-10-08: Windows RUNTIME-01 acceptance reported complete.** The user supplied a local Codex receipt for commit `205e0030de07986ef4244f38f01890bdf62d5a10`, Python 3.12.10, and 126 passing tests (suite exit 0). GitHub main was independently inspected and matched that revision. The local computer, evidence files and archive were not independently accessed from this chat.

## Reported verification

- Process interruptions at steps 37 / 43 / 50 exited 77 / 78 / 79.
- Resumes and verification exited 0. All four authoritative reference files matched byte for byte.
- Corruption, source/configuration mismatch and competing-writer attempts exited 2.
- Same-drive archive restoration, operator lock, minimum-space rejection and actual 300-second timeout passed.
- No Windows-specific runtime failures were reported.

This establishes reported bounded Windows **process-exit** recovery for the RUNTIME-01 reactor fixture. It does not establish recovery for every spatial or heredity experiment. Historical setup and earlier calibration notes retain their original dates and scope.

## Outstanding gates

1. **Independent off-drive backup:** same-drive restoration is useful but cannot protect against that drive failing. An independent backup destination and verified restoration remain outstanding.
2. **Physical power-loss recovery:** process exits and Linux CI do not test power interruption, storage caches or filesystem durability. No power-loss reliability is established.
3. **Hardened isolation:** basic lock, free-space and timeout controls do not demonstrate least privilege or enforced filesystem/network isolation.

Continuous simulation, unattended scheduling, an organism state service and automatic deployment remain unimplemented/unverified. Do not enable them by implication.

## Operating contract

Keep local laboratory files on the existing D: laboratory drive. Use existing installations. An operator manually reviews the exact source revision and change list before applying updates; fetching code is not permission to execute it. Preserve source snapshots, histories, failed runs, checksums and restoration receipts in separate run directories.

No self-hosted GitHub Actions runner, paid hosting, subscription, metered API, OpenAI API key or LLM is required or authorized for these experiments. No automatic execution of incoming commits.

GitHub stores reviewable source and protocols; local Codex performs operator-reviewed bounded acceptance on the workstation. Observer output is read-only and cannot repair or replace authoritative state. New checkpoint integrations require separate schemas and acceptance tests.

## Next science gate

[CLOSURE-02 precommitted protocol](CLOSURE-02-PROTOCOL.md) tests cost-controlled shell function. Its implementation and held-out execution are separate future gates. Passing runtime acceptance does not establish biological function, individuality or digital life.
