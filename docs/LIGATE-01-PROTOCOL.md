# LIGATE-01 — activated feedstock and variable-length chain opportunity gate

Prospective, 2026-10-09. Distinct chemistry; CARRIER/AGGREGATE/RECYCLE remain
closed. This is an exploratory opportunity gate, not a confirmatory maintenance
panel. No protocol parameter is chosen from its reserved trajectories.

## Hypothesis and scope

Generic energy-driven activation and condensation can generate founder-free
chains which subsequently accelerate production of other chains. Variable-length
chain growth and cleavage replaces fixed two-atom manufacture/waste recovery.
The law is installed synthetic chemistry, not discovered molecular physics.
Well-mixed encounter sampling is an explicit idealization, not verified transport
or spatial self-organization. No catalyst, template, sequence or policy is supplied.

32 persistent binary atoms (16 of each type), initially individual monomers;
256 photon energy units, no inflow, no activated material or bound energy.
Every atom remains uniquely identified. Ordered chains contain 1–4 atoms.
Each covalent link stores one energy unit. A free monomer can store two units
of activation energy. Activation consumes three photons and dissipates one.
Ligation consumes the activation of an end monomer and joins it to another
chain: two activation units become one new bond plus one dissipated unit.
Cleavage dissipates exactly one bond unit; both fragments retain their other
bonds. There is no free regeneration or recycled-energy refund. Material is
reusable after cleavage; activation always costs fresh photons. All initial
endowment and removed energy enter the ledger. Initial total energy is 256.

## Generic law and comparators

2048 discrete attempts; each consumes exactly six xorshift32 draws, including
invalid contacts. Choose from current live objects in increasing identity order.
Draw0 modulo3 chooses activation, ligation or cleavage. Draw1 chooses first
object, draw2 second, draw3 catalyst, draw4 probability byte, draw5 orientation
or cleavage offset. No search for eligible partners. A catalyst is a separate
chain of length2–4. Its SHA256 ASCII `LIGATE-01|<binary sequence>` first byte
modulo2 defines which monomer type it activates. This changes rate, never cost.
Activation accepts probability byte<8 without a compatible catalyst, <64 with
one. Only bytes8–63 credit catalyst causation. Ligation accepts byte<128 when
exactly one selected reactant is an activated monomer, other unactivated and
combined length<=4; orient activated monomer left for even draw5, right otherwise.
Cleavage accepts byte<8 for an unactivated chain length>=2, cut at
1+draw5 modulo(length-1). Fragments are fresh objects with parent identity.

Four arms share each seed and initial resources: candidate as above; inert
never catalyzes; shuffled uses opposite target bit; constitutive accepts<64
without a catalyst and is a kinetic upper-bound diagnostic, not organization.
At step1536 discard remaining photons into an explicit removed-energy ledger.
This removes environmental fuel, not a researcher subsidy or external assistance.
No event selection, sequence sorting or favorable founder.

## Registered samples and decision

Discovery seeds75000–75031, all32×4 arms, unscreened. Author fixtures75999 only.
Any future maintenance confirmation must use disjoint seeds and a new frozen
protocol; these trajectories cannot become a tuned confirmation panel.
An object is productive only when its causally catalyzed activation funds a
ligation producing a DIFFERENT binary sequence. Trace atom activation donor,
formation and cleavage parents, alive status, energy and all attempts.
Opportunity per world: at step1024 at least two distinct LIVE productive
sequences AND at least four causally funded cross-sequence ligations before
1024. Gate requires>=16/32 candidate opportunity worlds and candidate advantage
over inert AND shuffled using one-sided exact paired McNemar tests with Holm
thresholds .025/.05. Report all counts and controls regardless of outcome.
Also report post-withdrawal ligations, energy depletion, length distribution,
cleavage reuse and ancestry. These are secondary, not maintenance acceptance.
No damage or repair endpoint in this gate. Failure closes this exact law/horizon;
do not tune costs, thresholds, seeds, inventory or horizons to pass.

## Execution and evidence gates

Freeze implementation and independent interpreter before any75000 trajectory.
Authored accounting/paid cross-production/cleavage checks must pass first.
Independent interpreter imports no producer code and reconstructs every draw,
event, state hash, final state and opportunity decision. Exact replay first seed
four arms; tampered noise, balanced unpaid energy and parent identity must reject.
Any failure is preserved; no silent panel rerun. 128 worlds/262144 transitions.
Operator lock, no competing writer, Python3.12 existing environment. Every child
512MiB allocation,300CPU/300wall seconds,4process bound; no memory-peak claim.
One fresh evidence root: raw128MiB, archive64MiB, restore128MiB, failure8MiB,
combined328MiB; 5GiB free floor plus entire reservation before execution.
Include frozen source ZIP, exact revision, all raw trajectories, process exits,
audit and replay proofs. Before publication independently restore the sealed
evidence to user-approved C:/ora and audit backed-up source/data. This is not
physical power-loss durability or full-host recovery. No persistent service,
legacy changes, observer redesign or publication activation.
