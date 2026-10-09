# CARRIER-01 — finite material carriers, local construction and functional renewal

Prospective2026-10-09; preserve COUPLE,REDOX,RECYCLE,KINETIC,GRADIENT. None is
rerun or repriced. This installs a distinct substrate: individually identified,
finite **mass-bearing energy carriers** move between components and raw atoms.
Capture and manufacture are separate physical contacts. Catalysis changes an
activation chance, never stoichiometric yield or price. No free global fuel pool,
working founder, rewarded policy, template replication or controller in candidate.
Generic chemistry and the capacity to perform each reaction are programmed;
their realization and resource-exchange history are measured, not called life.

## Law, inventory and provenance

Eight cells in a periodic line. Twenty-four distinct atoms, six each of types0..3,
start raw at unscreened pseudorandom cells. Sixteen distinct carriers, four each
of lanes0..3, start empty at unscreened cells. Each cell has64 photons (512 total),
and the whole world128 finite thermal-motion units. No inflow. Heat is unavailable.
Two raw atoms at one cell and a charged carrier at that cell manufacture a new
component with a fresh object ID; neither atoms nor carrier IDs are copied.
Atom histories list every previous component. Ordered recipe u<=v has kind4*u+v;
capture lane is first SHA256 byte of ASCII `CARRIER-01|u|v` modulo4. No recipe,
topology, random seed or successful component is selected after results.

| Event | Inputs -> outputs |
| --- | --- |
| Charge | 4 local photons + empty carrier -> carrier potential3 + heat1 |
| Manufacture | 2 local raw atoms + charged carrier3 -> component potential1 + empty carrier + heat2 |
| Recycle | 2 local waste atoms + charged carrier3 -> same2 raw atoms + empty carrier + heat3 |
| Decay/damage | component potential1 -> its2 waste atoms + heat1 |
| Move | 1 thermal unit -> one-cell translation of an atom/component/carrier + heat1 |

Movement of a component moves both constituent atoms together. Waste/raw atoms
move singly. Recycling may recombine waste from different objects; there is no
handed pair, remembered partner search or successful construction selector.
Formation, release and component endowment are included in the3-unit price.
Every state: photons +3*charged carriers + active components + thermal +heat
+removed =640. All24 atom IDs and16 carrier IDs are conserved. A charged carrier
retains its charge-step, donor object ID, donor recipe, donor atom pair and whether
that donor was assisted. Basal charging has no donor. Consuming the carrier records
that provenance before clearing it. New objects retain atom and energy ancestry.

## Dynamics and fixed controls

Seeds73000..73031,2048 attempts each, six paired arms =192 unscreened worlds.
Xorshift32 unsigned generator, seed nonzero. Initialization consumes40 draws:
24 atom positions then16 carrier positions, each modulo8. Each attempt consumes
exactly8 further draws, including rejected/empty actions:
operation, carrier, atom1, atom2, component-anchor atom, direction, acceptance,
decay. Operation modulo6: move atom/component, move carrier, charge, manufacture,
recycle, decay. IDs sampled modulo24/16; no eligible-object search. Direction
low bit selects +1/-1. Charge requires an empty carrier and4 photons at its cell.
Basal accepts low acceptance byte<8. Local compatible component selected by
anchor accepts byte<64. **Only byte>=8 and<64 credits causal catalyst donation**;
basal successes never acquire a false donor. Decay accepts low decay byte<8.

At attempt512, before the sampled action, blindly damage every component in
cells0..3. No outcome-driven intervention. Record recipe types of currently
productive damaged unassisted objects only if no copy of that recipe survives.
At attempt1536, before action, remove all remaining photons to an explicitly
unavailable reservoir. Later manufacture/renewal uses retained charged carriers.
This removes natural energy, not researcher rescue; it cannot establish autonomous
activity after buffer depletion. Candidate has no researcher rescue at any step.

* `candidate`: the registered contacts and freely exchangeable carriers.
* `inert`: basal charging only; all other costs/inventory/contacts identical.
* `private`: catalytic carriers can pay only for recovery/reassembly of their
  donor's same atom pair. Basal carriers remain shared. This deliberately removes
  cross-component funding; cross-funding endpoints are structurally blocked and
  are diagnostic, NOT an independent positive statistical test.
* `shuffled`: at512 rotate every component's capture lane by1 modulo4, including
  subsequent components. Equal per-component specificity/stoichiometry; altered
  reaction relations, not a claim of equal realized encounter frequencies.
* `no-recycle`: waste recovery disabled. Recycling-dependent endpoints are blocked
  by definition; report other throughput, never use this as a significance claim.
* `supplied`: first four unscreened atom pairs0:1,2:3,4:5,6:7 are supplied
  components at each first atom's original cell. Pay shortest-ring transport of
  second atom and carrier0, one basal charge (4 photons), and manufacture (3
  carrier potential) per founder. No selected recipe or subsequent support.
  Founder atoms and energy-descended components stay conservatively assisted.
  Supplied organization is a controlled possibility, not autonomous origin.

## Endpoint, controls, statistics and stop

Before512, an unassisted active object is productive only if its causal charged
carrier funded manufacture of a *different recipe*. After blind damage, a lost
productive recipe Y qualifies only if a fresh unassisted Y is manufactured from
two atoms waste-recycled after512, using a carrier charged after512 by another
unassisted recipe X!=Y. The fresh Y must later causally charge a carrier that
funds manufacture of recipe X, completing the observed resource-exchange return
path by1535. Every price and provenance must be paid. This is functional recipe
replacement and a type-level exchange loop, not exact object continuity, copying,
reproduction or inherited organization. Other interactions are retained as data.

Pre-execution comparator clarification: inert also cannot produce a causally
catalyst-funded endpoint by definition. Treat inert/private/no-recycle as causal
path-removal diagnostics, not independent frequency evidence of emergence.
Primary pass: candidate>=8/32 endpoint worlds, adequate damage exposure>=16/32,
and one-sided exact paired McNemar P<=.05 versus shuffled (one registered test).
Record all ties/wins/losses, all
arm frequencies, exposure, capture/manufacture/recycling/transport/decay counts,
source assistance, energy remaining/depletion and post-photon-removal activity.
Inert/private/no-recycle/supplied are diagnostics, not extra hypotheses to shop among.

If exposure<16, classify underexposed and stop the tested law/horizon; do not
call zero renewal a decisive negative or change damage time/seeds/horizon toward
success. If adequate but gate fails, preserve and stop. If positive, independently
reproduce fresh prospectively registered samples before extending claims.

## Feasibility, execution and evidence gates

Freeze exact producer, independent interpreter and accounting fixtures before
execution. First authored fixtures must exhibit paid cross-funding, recycling,
new identity and post-damage useful replacement; refuse unpaid carrier, reused
identity and corrupted random draw. These fixtures are not panel founders.
Conditional on accounting tests, execute ALL registered seeds/arms without screening.
No new rates, stocks, recipes or stop gates after seeing results.

Existing global operator lock; per child512MiB allocation cap,300 CPU seconds,
4 processes,300 wall seconds; no memory-peak guarantee. Eight sequential batches
of4 seeds/24 worlds plus first-batch byte replay. Each fresh case raw32MiB,
archive16MiB,restore32MiB,failure2MiB,total82MiB; control metadata another82MiB.
Panel/control precharged reservation820MiB. Before any execution, also reserve a
final evidence package: raw128MiB,archive128MiB,restore256MiB,failure8MiB,total520MiB,
and final source-history/CI continuity raw16MiB,archive16MiB,restore16MiB,failure2MiB,
total50MiB. Complete laboratory reservation1390MiB, plus5GiB free-space floor.
The package retains all primary raw histories and failed processes, without
duplicating byte-identical already restored science files. Every transition,
draw, event, snapshot and ancestry preserved with exact source. Separate interpreter
must rederive every event/RNG/state, independent evidence-budget audit, forged-copy
refusal and complete byte restoration. No new runtime/observer/legacy code changes,
unattended world, public access or paid/model API.
