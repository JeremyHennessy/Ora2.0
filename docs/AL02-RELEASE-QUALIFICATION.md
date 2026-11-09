# AL02 V2 release qualification

Run from the clean isolated Windows qualification checkout:

```powershell
python -I -B -S tools/qualify_al02_release.py
```

A nonzero exit or a missing PASS receipt blocks an engineering-readiness claim.
The command prints an evidence directory containing the machine-readable verdict,
raw journal and output, custody receipts, race and interruption results, and logs.
Keep the evidence and obtain an independent rerun at the same stable revision.
Any changed source or artifact invalidates the affected evidence.

## Trust and dependency order

Reviewed runtime bytes except consent feed the source inventory, then the binding,
then the inactive package. Consent embeds the artifact digests. The external
installation record pins the resulting consent bytes downstream. Independently
verify that record and the pinned bytes. The trusted parent and clean checkout
are prerequisites. In-process code modification is outside this trust boundary.

Release identity is distinct from human authorization, an atomic attempt claim,
and accepted scientific evidence. A directory claim blocks reuse even if empty
after a crash. An intent receipt alone does not prove dispatch.

The repository rehearsal calls the real consent gate on the frozen V2 bytes
inside the real custody admission callback. Its test-only wrapper separately
verifies a disposable command and scope. The real Job receives only the pinned
inert fixture worker. Fixture context, authorization, paths and command are
recorded separately. No production option enables this wrapper. The scientific
worker entry and live scientific workload are outside this qualification.

## Approval and recovery

PASS supports review of the inert engineering contract. Before any installation,
obtain separate approval, verify byte-exact backups of production consent and
custody, and compare all proposed bytes with the external installation record.
Install the pair recoverably while PARKED and verify readback and refusal without
authority. Restore both backups on failure and preserve any attempt directory.
Activation and any scientific release require their own explicit approval.
