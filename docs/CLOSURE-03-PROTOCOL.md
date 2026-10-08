# CLOSURE-03 finite payload-restoration pilot v1

2026-10-08. Precommit before simulator implementation or sampled runs.
This narrows the design to paid causal payload restoration. It does not test
closed productive organization, functional equivalence, heredity or life.
The earlier measurement contract remains unchanged.

## Question and rival explanation

Do unscreened finite token populations restore a removed prerequisite and
target through a rebuilt prerequisite's productive participation? Does paid
suppression of one prerequisite-producing interaction reduce this endpoint
relative to a structurally matched sham? Ordinary finite-table redundancy is
the principal rival. Every splice interaction has an exactly equivalent fixed
table entry: no claim of irreducible computation or constructive superiority
is possible here. Stop expansion if the only evidence is this equivalence.

## Frozen law and generator

Use measurement contract `closure03-measurement-v1`: four integers 0..3 per
immutable payload, four material per token; ordered distinct live parents;
gate a[0]==b[3]; product (a[1],b[1],a[2],b[2]); one fuel per collision,
four precursor per successful birth, no parent consumption. Decay transfers
four material to waste. No rewards, mutation, migration, protected entity,
material recycling, fresh fuel, group copying or programmable host operation.

Each seed uses Python Random(seed), 32 genesis tokens (IDs g0..g31), four
successive randrange(4) draws per token. Duplicate payloads are allowed.
Never regenerate a failed population. Freeze observer signatures from genesis:
enumerate ordered pairs of distinct genesis token IDs with valid gates;
sort unique triples (product, actor genome, partner genome). Choose the
lexicographically first (P,T,a,b,c) for which a/b produces P, P/c produces T,
P and T are distinct and both occur in genesis. P/c requires two distinct
token IDs if its payloads coincide. This is an observer-selected structural
motif, not an organism or a random sample of all functions. All seeds remain
in denominators. If no motif exists, use P=(0,0,0,0), T=(1,1,1,1), no cut/sham,
and mark motif absent; never count it as eligible even if accidental restoration
occurs. No signature choice uses burn-in, outcomes or held-out results.

Choose cut=(a,b) from that first motif. Sham shares actor a, has a distinct
partner d from genesis with the same first and last coordinates as b (hence
the same potential incoming/outgoing gate degrees), and yields neither P nor
T; select the lexicographically first such pair present on distinct IDs.
If absent, mark unmatched, run both arms with their defined available
intervention (sham none), retain all outcomes, and exclude that seed only from
the predeclared matched contrast, reporting the unmatched count separately.
This matches potential gate degree, not realized trajectory productivity.

Two regimes per seed: precursor=128 or precursor=0 (sustained resource
absence control); fuel=160 in both. No resource is added later. Thirty-two
burn-in ticks then remove every live P/T copy, even when one is absent.
Follow for 128 ticks. A tick consumes three Random draws made after genesis:
u,v,w=random(),random(),random(). If at least two tokens live, sort IDs,
select actor floor(u*n), partner floor(v*(n-1)) from remaining IDs, and
attempt a collision. If fewer than two, no collision/fuel spend occurs.
If w<1/16 and any token remains after collision/control, remove the token
at floor((w*16)*n) in sorted live IDs. Damage is an event between ticks31/32.
No early stopping; empty worlds retain their remaining tick histories.
The finite 53-bit Random selection is the installed stochastic law, not an
ideal continuous distribution. Maximum births=32; live tokens<=64, material
total=256 or128, and each receipt<=1 MiB/4096 events.

## Six paired arms

All share genesis, frozen motif, initial budgets and draw stream.

1. `constructive`: splice rule.
2. `fixed_table`: immutable mapping of every valid ordered genome pair to its
   splice product. Only encountered entries are serialized, but auditor must
   verify that all valid encountered entries are included. Expect byte-identical
   event histories to constructive except law/table headers.
3. `cut`: splice births from cut pair after damage are immediately decayed,
   spending the same birth material and collision fuel.
4. `sham`: same immediate paid decay for the matched sham pair after damage.
5. `inert`: every birth is immediately decayed, including burn-in.
6. `external_rescue`: constructive law, but directly reintroduce P and T just
   after damage if both births can be afforded (8 precursor,2 fuel); ancestry
   remains external forever. If unaffordable, record no rescue, do not top up.

All suppression events are explicit birth followed immediately by decay;
there is no free repair or silent dropped material. Per intercepted birth
costs match. Diverging populations change collision opportunities and total
costs, so report actual material/fuel expenditure and do not claim trajectory
cost matching. Spatial locality, adaptation and evolution are not tested.

## Endpoints and analysis

Primary endpoint: eligible at damage AND motif present AND terminal live
internal post-damage P and T, with a rebuilt internal P directly participating
in birth of terminal T. Reuse measurement auditor without trusting generator
flags. Report all-seed and eligible-seed denominators, motif/match/eligibility
counts, extinction (zero terminal live tokens), terminal P/T counts, fuel used,
material transformed and rescue attempts. External descendants cannot pass.
Require exact constructive/fixed-table event equality per seed/regime; failure
is an implementation defect, not an interesting biological difference.

Predeclared scientific contrast: constructive minus cut and cut minus sham,
on motif-present, sham-matched, initially eligible paired seeds; retain full
all-seed arm outcomes alongside that conditional contrast. Report discordant
paired counts and two-sided exact sign-test p=sum binomial tails capped at1;
zero discordance p=1. No success threshold or tuning from development outcomes.
This small pilot can falsify claimed maintenance under this law; it cannot
establish an emergent closed organization even with a positive contrast.

## Panels, provenance and stop gate

Development seeds0..7 (96 seed/regime/arm receipts) only. Held-out seeds
8000..8063 (768 receipts), reserved now; do not execute them until complete
source and independent receipt validation are reviewed and merged. Initial
implementation must expose development-only execution; no auto study workflow.
Frozen horizons and signatures do not change after looking at either panel.
If no eligible matched worlds exist, report noninformative assay; do not add
seeded loops or select replacements. New laws require a new protocol/study.

Persist LF canonical JSONL raw receipts including full genesis, event ledgers,
tick draws/IDs, motif and interventions; study manifest pins protocol SHA256,
source revision, module SHA256, seeds, params and raw file SHA256. Independently
recompute generator, schedule, intervention selection and event ledgers. Any
corruption, missing/duplicate arm, law/schedule/ancestry/cost mismatch or fixed
equivalence failure rejects the archive; preserve invalid data. Output to a
new directory outside source. No overwriting prior evidence.

Finite CPU-only manual execution. Existing desktop lock,5GB floor,300-second
per-process timeout and pinned source snapshots apply. No continuous runtime,
network/model API or checkpoint claim. Off-drive backup, physical power-loss
and isolation remain open. Research intake: AI-Research
`a7574096e73123227338366a41d0bb013ced4d39`, reviewed new Pass11 handoff;
EERC remains a separate untested hypothesis, not an imported architecture.
