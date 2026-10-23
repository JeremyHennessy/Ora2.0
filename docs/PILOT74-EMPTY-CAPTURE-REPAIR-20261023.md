# Empty capture transport repair

V2 completed 16 original/restored roles, then failed at the first planned crash/partial case. Its native receipt records expected exit 78, zero captured bytes, EOF, no capture errors and closed child ownership. The guardian adapter sent that empty capture to the proof-document reader, which correctly refuses zero-length proof documents. This is a transport defect, not a full recovery qualification pass.

The isolated change authenticates empty output through the existing available-evidence scanner, including plain-file, link-count, descriptor/path/ancestor identity, actual zero extent and exact hash checks. Nonempty captures keep the existing exact reader. Empty proof documents remain refused. Exit codes, role checks, process caps, deadline, workload and production admission are unchanged.

Eight new data/transport regressions cover empty and nonempty captures, rejected empty proofs, wrong digest, false zero extent, missing file, hard links, and a synthetic client exchange retaining exit78/empty output. They do not launch a guardian, replay a qualification role or construct a World.

Failed v1 and v2 are sealed and must never resume or retry. A separate attempt requires fresh authorization, exact-source CI and independent registration/preflight. The live Ora source is unchanged. General CI test-harness failures on the preceding source remain separate debt; no broad CI pass is claimed.
