# FUEL-01 — chemical work coupling, prospective opportunity gate

Frozen before implementation or execution, 2026-10-09. Baseline Ora
1822c5012b7211c9af6ace8a3b151b12038011d0; AI-Research
09f4f33f5e7e76bd47d8d7278dd1ab6d38b96948, Pass39.

## Distinct hypothesis and scope

TRANSFER moved existing bond energy and merely displaced damage. LIGATE used
photons to activate chain precursors. Here a *mass-bearing chemical fuel* reacts
with reusable raw material: fuel consumption produces separately retained spent
fuel, heat and activated substrate. Dimers can catalyze that bimolecular reaction;
they neither supply its energy nor receive free charge. This changes resource
chemistry, not prices in a closed historical law. Test spontaneous functional
opportunities before a separate damage study. Installed chemistry is not life.

All primary controls can activate, construct, decay and reconstruct material.
No endpoint requires catalyst-labelled ancestry or a disabled reaction in a null.
No template copying, target structure, reward, controller or supplied founder.

## Fully specified law

Well-mixed ideal encounter vessel, no transport claim.24 distinct raw atoms,
types atom-ID modulo4 (six each),96 distinct fuel molecules with potential4.
Food and substrate are separate conserved mass inventories: total120 tokens.
All substrate initially free and uncharged. Startup energy384, no external
work, photons, regeneration, inflow, hidden activation or successful structure.
Spent fuel remains physically present and inert; it never becomes substrate.

Reaction A: one free uncharged atom + one unused fuel -> same atom activated2
+ spent fuel0 + heat2. Basal probability16/256. A separately encountered live
dimer whose sum-of-types modulo4 equals substrate type raises it to128/256.
No catalyst consumption, reward or energy creation. Shuffled arm adds1 modulo4
to the dimer signature. Inert arm uses basal rate only. Prices never change.
Reaction B: activated singleton2 + distinct uncharged singleton0 -> fresh
dimer with bond1 + heat1. Always occurs on the specified valid encounter.
Reaction C: encountered dimer bond1 -> two fresh uncharged singleton objects
+ heat1, if byte<8. This is dissipation and material recycling, not paid repair.
Free activation does not decay under this idealized law; identify buffer activity.

Object IDs append only. Every formation stores both parent IDs, constituent atom
IDs and charge's fuel ID; every cleavage stores parent and material histories.
Never relabel an old dimer as rebuilt. Material ownership, fuel ownership, heat,
activation and bonds checked after EVERY step: 4*unused fuel +2*active singles
+live dimer bonds +heat +4*inaccessible fuel =384.

## Frozen draws, samples and opportunity endpoint

32 unscreened seed blocks76000..76031, four arms in order candidate,inert,
shuffled,fuel-withdrawn (128 worlds),4096 steps each,524288 attempts. Use xorshift32
initialized to seed; six draws per step with shifts13,17,5 and unsigned32 masking.
Draw0 modulo3 selects reaction. Draw1/2/3 modulo ascending live-object count
select first, second, catalyst (uniform whole inventory, no successful search).
Draw4 modulo96 selects fuel; draw5 low byte supplies reaction chance. All six
requested draws advance even on failed encounters. Final cursor24576/world.
Fuel-withdrawn uses candidate law but at step2048 marks EVERY remaining unused
fuel inaccessible, retaining mass and energy. This is environmental starvation,
not withdrawal of researcher assistance: primary candidate receives none.

At final step4096, opportunity means >=3 live dimers, >=8 cumulative formations
and >=8 chemical activations. Count all formation routes without provenance
filtering. Report successful capture/formation/cleavage, causal extra activations
(chance>=16), reused atom formations, fuel depletion, remaining activation and
fuel, and whole mass/energy balances. Opportunity is NOT self-maintenance.

Gate: candidate >=16/32 opportunity worlds AND candidate exceeds BOTH inert and
shuffled in paired endpoint frequency. Exact one-sided binomial discordance test,
Holm family alpha.05 for these two comparisons (smallestP<=.025, other<=.05).
Starvation is diagnostic, not a required superiority comparator. Never infer an
advantage from catalyst-labelled counts unavailable to inert. No selected seeds,
cost/rate/resource/horizon tuning, extension or retry toward success.

## Subsequent decisive self-maintenance test (not authorized by gate failure)

Only after gate success independently reproduce on32 disjoint unscreened blocks
76100..76131 under the EXACT same law and opportunity endpoint. Register damage
implementation, random draw boundary and blind loss policy before that execution.
Then prospectively freeze a disjoint confirmation panel with two useful-loss
challenges, whole functional output restoration and reused atom provenance,
balanced nulls, resource-accounted perturbation and all-world intention-to-test.
No supplied successful structure and no selecting opportunity-positive worlds.
Acceptance requires useful activity rebuilt after both losses, not persistence,
single component repair, stored-energy spending or researcher-favorable founders.

## Execution and acceptance

Authored fixtures76999 check all three reactions, atom reuse and controls before
fresh samples. Freeze exact producer AND separate interpreter source before panel.
Independent interpreter must reconstruct draws, every object and ledger from raw
attempts; exact replay, forged energy/ancestry/draw rejection; preserve failures.
Operator lock, existing512MiB allocation/300s CPU/wall/4process limits per invocation,
finite prewrite disk budget and5GiB free floor. Preserve exact source, exits,
checksums, full raw evidence and independent off-drive restore/audit. No live
runtime, legacy edits, observer redesign or historical study modification.
Stop law if gate fails; absence of opportunity is not disproof of all chemistry.
