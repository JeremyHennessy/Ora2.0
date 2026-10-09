# KINETIC-01 — implemented draw and measurement clarification

Prospective clarification of KINETIC-01-PROTOCOL, before any43000..43031 map,
initialization or natural execution. No thresholds, costs, controls, samples,
duration or success criteria change. Candidate physics remains separate from Ora.

Python Random(seed),96 initial one-bit draws in atom-ID order, then eight16-bit
draws per step, including every invalid attempt. Identical initial bits/tape across
six arms. Preserve raw eight-draw requests, every outcome, full initial/final RNG
states/cursors, immutable object archive and final ownership ledger. Independent
interpreter regenerates the entire tape and every transition, not only totals.

Draw0 mod4 selects diffusion/association/cleavage/regeneration; draw1 mod16 site.
Draw2 selects first candidate from sorted IDs; draw3 selects second from the pool
excluding the first. Draw4 selects an eligible catalyst other than reactants;
choose uniformly from all length>=2 eligible chains, then test the fixed SHA map,
without screening/mapping-only candidate selection. Draw5 selects cut bond or
cardinal diffusion direction (left/right/up/down, periodic). Draw6 supplies the
reaction threshold modulo32/16/2; draw7 selects first paid fuel token, then draw3
selects a second from remaining charged tokens. No resampling invalid requests.

Diffusion pool at the site comprises molecules first (sorted molecule ID), then
fuel/waste tokens (sorted token ID). One selected carrier moves one lattice edge;
no work or atom change. Photons are local site stocks, not carriers. Association
and all carrier/catalyst/fuel pools are site-local except the well-mixed arm,
which uses all sites. Product keeps left reactant site. A regeneration selects
a spent token from that eligible pool using draw2 and consumes exactly two
photons at the token's actual site. Molecule maximum length six, eligible catalyst
length2..6. Mapping tests oriented words, seed and UTF8 SHA as original protocol.

Initial atom IDs0..95 at sites floor(ID/6); object IDs0..95 contain one atom.
Token IDs0..255 at floor(ID/16). Fresh sequential object IDs on every association
and both cleavage products; immutable creation step, parent IDs and atom strings.
Site is current location; historical archive retains creation location. Supplied
dimers pair IDs0/1..22/23 before step0, each at its common original site, with
the first two available local charged token IDs paid. Mark all descendant objects
of supplied dimers assisted forever. This provenance prevents supplied starting
organization from masquerading as independent reconstruction.

Withdrawal occurs immediately before the step4096 request: move all remaining
photons to exported energy, preserve gross accounting, never return it. Record
this deterministic event alongside the step request. Other arms export zero.

Primary endpoint is conservative: all lifecycle timestamps must occur in the
registered4096..8191 window. An unassisted type must be naturally formed, then a
specific copy catalyze a paid association, then the last active copy of that type
be removed by cleavage. Subsequent unassisted catalyst-assisted association must
reconstruct that type, and that reconstructed object itself must later catalyze
a paid association. Record formation/use/loss/reconstruction/use steps and IDs
and both causal catalysts. One endpoint per distinct word, not per molecule.
Loss through association does not substitute for registered cleavage. A retained
copy, initial supplied dimer, rate increase or mere formation is not an endpoint.

Report every seed/arm and exact one-sided paired sign test on candidate-minus-inert
endpoint counts (ties excluded, no selection). Candidate >=8/32 endpoint-positive
worlds AND sign-test P<=0.05 is the frozen positive gate. All costs, depletion
first-ticks, throughput, nulls and withdrawal outcomes remain secondary reports.
No reproduction, functional inheritance, ecological closure or intelligence claim.

Implementation development checks use only90000..90001 and authored reaction
fixtures, never future panel seeds/maps. Exact implementation must be committed
before the unscreened panel. Execute four predetermined seed batches of eight,
each48 worlds /393216 attempts, serialized under the laboratory lock,256MiB disk
ceiling per batch,512MiB memory/300CPU seconds/four processes/300wall seconds,
5GB floor. Separate bounded replay/audit per batch; preserve any failure before
correction. No retries changing law, horizon or future samples after outcomes.
