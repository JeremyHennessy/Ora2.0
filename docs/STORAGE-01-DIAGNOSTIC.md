# STORAGE-01 initial Windows capture failure

Frozen contract f26919e, first implementation a3481ec. All six initial focused
tests failed in snapshot creation with PermissionError while reading the lock
initializer through a second descriptor. The existing Windows byte-range lock
was held by this process on the original descriptor. No fault panel or science
execution began. The original source, test log, failure manifest and evidence
restoration are preserved privately; no prior evidence or old runtime changed.

Before corrected execution, check the bounded one-byte `L` initializer before
acquiring the existing lock; under the lock, capture only world data and include
that fixed validated initializer in the archive. The stable lock file is never
rewritten or unlinked. The old lock helper still checks its size and excludes
cooperative writers. Noncooperative edits/replacement remain an explicit open
isolation risk. Existing real competing-writer rejection remains mandatory.

This corrects a capture implementation error, not a physical-world hypothesis,
storage severity, fault outcome, accounting parameter or frozen law. The ten
frozen cases, source binding, independent replay, no-overwrite requirements and
all limits are unchanged. Preserve and report the failure alongside acceptance.
