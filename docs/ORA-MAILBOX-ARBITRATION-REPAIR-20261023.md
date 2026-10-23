# Mailbox arbitration candidate — October 23

Prospective software repair only; not deployed to the running v8 source. Failed pilots remain terminal, with no resend, rerun or rescoring. Historical file holder remains unknown.

The first attempted delete-sharing reader failed its held-reader replacement test on real Windows (WinError 5); its source and failed outcome are retained locally. The selected candidate instead takes the existing producer mailbox.lock while opening and reading at most 65,537 bytes. A busy consumer skips that poll and can still process already durable tasks. A producer encountering the reader lock receives Busy before its build callback or publication intent. No uncertain submission is retried. Reader exceptions release their lock; all non-lock errors still fail closed.

The publisher, task sequence/content identity, original 64 KiB limit and Store limits are unchanged. Eight new Windows fixtures cover mutual exclusion, real separate-process contention, generation identity, exception cleanup, ordinary reader denial, missing files, actual service ingestion and oversized refusal. Six Store, ten controller and eleven tail-budget regressions also pass locally (35 total). Existing frozen client collision recovery remains separately qualified; that client module is not part of this runtime checkout.

Windows CI must verify the exact candidate and 69 runtime byte hashes before any deployment review. No hot edit, automatic task switch or new operating lifetime is authorized by this document. The currently healthy runtime continues on d59f01e.
